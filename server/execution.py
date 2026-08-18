"""
QuickLab — Python Code Execution Engine
Provides safe, isolated session execution with rich representation capturing
(Matplotlib, Plotly, Pandas DataFrames, Images, SymPy, Streams, and Shell commands).
"""

import sys
import io
import os
import ast
import base64
import traceback
import subprocess
import threading
from typing import Dict, Any, List, Tuple, Optional

# Pre-set headless Matplotlib backend
os.environ["MPLBACKEND"] = "Agg"
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


class OutputCapture:
    def __init__(self):
        self.outputs: List[Dict[str, Any]] = []

    def add_stream(self, text: str, name: str = "stdout"):
        if text:
            self.outputs.append({"kind": "stream", "name": name, "text": text})

    def add_error(self, text: str):
        if text:
            self.outputs.append({"kind": "error", "text": text})

    def add_result(self, text: str):
        if text is not None:
            self.outputs.append({"kind": "result", "text": str(text)})

    def add_html(self, html_content: str):
        if html_content:
            self.outputs.append({"kind": "html", "data": html_content})

    def add_plotly(self, json_or_html: str):
        if json_or_html:
            self.outputs.append({"kind": "plotly", "data": json_or_html})

    def add_image(self, b64_png: str):
        if b64_png:
            self.outputs.append({"kind": "image", "data": b64_png})


def capture_matplotlib_figures() -> List[str]:
    """Captures all open Matplotlib figures as base64 PNG strings and closes them."""
    imgs = []
    if plt is None:
        return imgs
    try:
        fignums = plt.get_fignums()
        for num in fignums:
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode("utf-8")
            imgs.append(b64)
        plt.close("all")
    except Exception as e:
        pass
    return imgs


def format_value_representation(val: Any, out_cap: OutputCapture):
    """Inspects an expression value and adds the richest appropriate output representation."""
    if val is None:
        return

    modname = getattr(type(val), "__module__", "")
    clsname = getattr(type(val), "__name__", "")
    full_type = f"{modname}.{clsname}"

    # 1. Pandas DataFrame / Series
    if "pandas" in modname and ("DataFrame" in clsname or "Series" in clsname):
        try:
            html = val.to_html(max_rows=100)
            out_cap.add_html(html)
            return
        except Exception:
            pass

    # 2. Polars DataFrame / Series
    if "polars" in modname and ("DataFrame" in clsname or "Series" in clsname):
        try:
            html = val._repr_html_() if hasattr(val, "_repr_html_") else str(val)
            if "<table" in html:
                out_cap.add_html(html)
                return
        except Exception:
            pass

    # 3. Plotly Figure
    if "plotly" in modname and ("Figure" in clsname):
        try:
            import plotly.io as pio
            # Export as responsive interactive HTML div
            html_div = pio.to_html(val, full_html=False, include_plotlyjs=False)
            out_cap.add_plotly(html_div)
            return
        except Exception:
            pass

    # 4. PIL Image
    if "PIL" in modname or hasattr(val, "save") and hasattr(val, "format"):
        try:
            buf = io.BytesIO()
            val.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            out_cap.add_image(b64)
            return
        except Exception:
            pass

    # 5. NumPy Array that represents an Image (3D uint8 or float)
    if "numpy" in modname and clsname == "ndarray":
        if val.ndim == 3 and val.shape[2] in (3, 4) and val.dtype.kind in ('u', 'i', 'f'):
            try:
                from PIL import Image
                import numpy as np
                norm_arr = val
                if val.dtype.kind == 'f':
                    norm_arr = (np.clip(val, 0, 1) * 255).astype(np.uint8)
                else:
                    norm_arr = np.clip(val, 0, 255).astype(np.uint8)
                img = Image.fromarray(norm_arr)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                out_cap.add_image(b64)
                return
            except Exception:
                pass

    # 6. HTML repr objects
    if hasattr(val, "_repr_html_") and callable(getattr(val, "_repr_html_")):
        try:
            html = val._repr_html_()
            if html:
                out_cap.add_html(html)
                return
        except Exception:
            pass

    # 7. SymPy Objects
    if "sympy" in modname:
        try:
            import sympy
            out_cap.add_result(sympy.pretty(val, use_unicode=True))
            return
        except Exception:
            pass

    # Default: Standard Python repr
    try:
        r = repr(val)
        out_cap.add_result(r)
    except Exception:
        out_cap.add_result("<unrepresentable object>")


def execute_shell_magic(command: str, cwd: str) -> Tuple[str, str, int]:
    """Executes a shell command (e.g. !pip install or !ls) inside the temporary sandbox."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 60 seconds.", 1
    except Exception as e:
        return "", f"Shell command execution error: {str(e)}", 1


def inspect_variables(namespace: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Inspects user-defined session variables (excluding internal and imported modules)."""
    vars_list = []
    ignored_keys = {
        "__name__", "__doc__", "__package__", "__loader__", "__spec__",
        "__builtins__", "_", "_quicklab_globals", "_quicklab_out", "In", "Out"
    }

    for key, val in list(namespace.items()):
        if key.startswith("_") or key in ignored_keys:
            continue
        try:
            type_name = type(val).__name__
            mod = getattr(type(val), "__module__", "")
            if mod and mod != "builtins":
                type_name = f"{mod.split('.')[0]}.{type_name}"

            # Summary representation
            val_repr = str(val)
            if len(val_repr) > 80:
                val_repr = val_repr[:77] + "..."

            # Array / DF shape if applicable
            shape_info = ""
            if hasattr(val, "shape"):
                shape_info = str(val.shape)
            elif hasattr(val, "__len__") and not isinstance(val, (str, bytes)):
                shape_info = f"len={len(val)}"

            vars_list.append({
                "name": key,
                "type": type_name,
                "shape": shape_info,
                "preview": val_repr
            })
        except Exception:
            pass

    return vars_list[:100]


def run_code_in_session(
    code: str,
    globals_dict: Dict[str, Any],
    session_cwd: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Executes Python source code string inside the session's isolated namespace.
    Captures stdout/stderr, last-expression result, Matplotlib figures, and Plotly charts.
    """
    out_cap = OutputCapture()

    # Handle shell magic lines (e.g. !pip install ...)
    lines = code.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("!"):
            cmd = stripped[1:]
            out_cap.add_stream(f"$ {cmd}\n", "stdout")
            out_s, err_s, ret = execute_shell_magic(cmd, session_cwd)
            if out_s:
                out_cap.add_stream(out_s, "stdout")
            if err_s:
                out_cap.add_error(err_s)
        else:
            clean_lines.append(line)

    py_code = "\n".join(clean_lines).strip()
    if not py_code:
        var_list = inspect_variables(globals_dict)
        return out_cap.outputs, var_list

    # Redirect standard streams
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    sys.stdout = captured_stdout
    sys.stderr = captured_stderr

    # Change working directory to session sandbox
    original_cwd = os.getcwd()
    try:
        os.chdir(session_cwd)
    except Exception:
        pass

    try:
        tree = ast.parse(py_code, mode="exec")
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expr = tree.body.pop()
            if tree.body:
                exec_code = compile(tree, filename="<quicklab-cell>", mode="exec")
                exec(exec_code, globals_dict)
            eval_code = compile(ast.Expression(last_expr.value), filename="<quicklab-cell>", mode="eval")
            eval_result = eval(eval_code, globals_dict)
            if eval_result is not None:
                globals_dict["_"] = eval_result
                format_value_representation(eval_result, out_cap)
        else:
            exec_code = compile(tree, filename="<quicklab-cell>", mode="exec")
            exec(exec_code, globals_dict)

    except Exception as exc:
        # Format traceback cleanly
        tb_lines = traceback.format_exception(*sys.exc_info())
        # Filter internal frames
        filtered = [l for l in tb_lines if "server/execution.py" not in l]
        err_msg = "".join(filtered).strip()
        out_cap.add_error(err_msg)

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        try:
            os.chdir(original_cwd)
        except Exception:
            pass

    # Append captured stdout and stderr
    stdout_content = captured_stdout.getvalue()
    if stdout_content:
        out_cap.add_stream(stdout_content, "stdout")

    stderr_content = captured_stderr.getvalue()
    if stderr_content:
        out_cap.add_error(stderr_content)

    # Capture any newly generated Matplotlib / Seaborn figures
    mpl_imgs = capture_matplotlib_figures()
    for img_b64 in mpl_imgs:
        out_cap.add_image(img_b64)

    # Inspect current variables
    var_list = inspect_variables(globals_dict)

    return out_cap.outputs, var_list
