"""
QuickLab — Python Code Execution Engine
Provides safe session execution with timeout enforcement, resource limits,
traceback sanitization (no internal path disclosure), and rich output capturing.
"""

import sys
import io
import os
import ast
import base64
import traceback
import subprocess
import threading
import concurrent.futures
from typing import Dict, Any, List, Tuple, Optional, Callable

from server.config import settings
from server.security import sanitize_traceback, validate_code_input

# Pre-set headless Matplotlib backend
os.environ["MPLBACKEND"] = "Agg"
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


class OutputCapture:
    def __init__(self, max_bytes: int = 5 * 1024 * 1024, stream_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.outputs: List[Dict[str, Any]] = []
        self.max_bytes = max_bytes
        self.current_bytes = 0
        self.stream_callback = stream_callback

    def _append(self, item: Dict[str, Any]):
        approx_size = len(str(item.get("data") or item.get("text") or ""))
        if self.current_bytes + approx_size > self.max_bytes:
            if not any(o.get("text") == "\n[Output truncated: Exceeded maximum buffer limit]\n" for o in self.outputs):
                truncated_msg = {"kind": "stream", "name": "stderr", "text": "\n[Output truncated: Exceeded maximum buffer limit]\n"}
                self.outputs.append(truncated_msg)
                if self.stream_callback:
                    self.stream_callback(truncated_msg)
            return
        self.current_bytes += approx_size
        self.outputs.append(item)
        if self.stream_callback:
            try:
                self.stream_callback(item)
            except Exception:
                pass

    def add_stream(self, text: str, name: str = "stdout"):
        if text:
            self._append({"kind": "stream", "name": name, "text": text})

    def add_error(self, text: str):
        if text:
            # Sanitize tracebacks to prevent information disclosure
            clean_text = sanitize_traceback(text)
            if clean_text:
                self._append({"kind": "error", "text": clean_text})

    def add_result(self, text: str):
        if text is not None:
            self._append({"kind": "result", "text": str(text)})

    def add_html(self, html_content: str):
        if html_content:
            self._append({"kind": "html", "data": html_content})

    def add_image(self, b64_png: str):
        if b64_png:
            self._append({"kind": "image", "data": b64_png})


def capture_matplotlib_figures() -> List[str]:
    """Captures all open Matplotlib/Seaborn figures as base64 PNG strings and closes them."""
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
    except Exception:
        pass
    return imgs


def format_value_representation(val: Any, out_cap: OutputCapture):
    """Inspects an expression value and adds the richest appropriate output representation."""
    if val is None:
        return

    modname = getattr(type(val), "__module__", "")
    clsname = getattr(type(val), "__name__", "")

    # 1. Pandas DataFrame / Series -> Render HTML Table
    if "pandas" in modname and ("DataFrame" in clsname or "Series" in clsname):
        try:
            html = val.to_html(max_rows=100)
            out_cap.add_html(html)
            return
        except Exception:
            pass

    # 2. HTML repr objects
    if hasattr(val, "_repr_html_") and callable(getattr(val, "_repr_html_")):
        try:
            html = val._repr_html_()
            if html:
                out_cap.add_html(html)
                return
        except Exception:
            pass

    # 3. SymPy Objects -> Pretty format
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
    """Executes a shell command inside the temporary sandbox."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 30 seconds.", 1
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

            val_repr = str(val)
            if len(val_repr) > 80:
                val_repr = val_repr[:77] + "..."

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


def _execute_code_core(
    py_code: str,
    globals_dict: Dict[str, Any],
    session_cwd: str,
    out_cap: OutputCapture
):
    """Inner core runner executed with output capturing."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    sys.stdout = captured_stdout
    sys.stderr = captured_stderr

    original_cwd = os.getcwd()
    try:
        os.chdir(session_cwd)
    except Exception:
        pass

    try:
        tree = ast.parse(py_code, filename="<quicklab-cell>", mode="exec")
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

    except Exception:
        tb_lines = traceback.format_exception(*sys.exc_info())
        err_msg = "".join(tb_lines)
        out_cap.add_error(err_msg)

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        try:
            os.chdir(original_cwd)
        except Exception:
            pass

    stdout_val = captured_stdout.getvalue()
    if stdout_val:
        out_cap.add_stream(stdout_val, "stdout")

    stderr_val = captured_stderr.getvalue()
    if stderr_val:
        filtered_err = "\n".join([
            l for l in stderr_val.split("\n")
            if "FigureCanvasAgg is non-interactive" not in l
        ]).strip()
        if filtered_err:
            out_cap.add_error(filtered_err)

    # Capture any newly generated Matplotlib / Seaborn figures
    mpl_imgs = capture_matplotlib_figures()
    for img_b64 in mpl_imgs:
        out_cap.add_image(img_b64)


def run_code_in_session(
    code: str,
    globals_dict: Dict[str, Any],
    session_cwd: str,
    timeout_seconds: Optional[int] = None,
    stream_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Executes Python source code string inside the session's isolated namespace.
    Enforces strict execution timeout and limits output buffer sizes.
    """
    timeout = timeout_seconds or settings.EXECUTION_TIMEOUT_SECONDS
    valid_code = validate_code_input(code)
    out_cap = OutputCapture(max_bytes=settings.MAX_OUTPUT_BYTES, stream_callback=stream_callback)

    # Handle shell magic lines (e.g. !pip install ...)
    lines = valid_code.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("!"):
            cmd = stripped[1:]
            out_cap.add_stream(f"$ {cmd}\n", "stdout")
            out_s, err_s, _ = execute_shell_magic(cmd, session_cwd)
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

    # Execute with timeout watchdog without hanging on thread pool join
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        _execute_code_core,
        py_code=py_code,
        globals_dict=globals_dict,
        session_cwd=session_cwd,
        out_cap=out_cap
    )

    try:
        future.result(timeout=timeout)
        executor.shutdown(wait=True)
    except concurrent.futures.TimeoutError:
        out_cap.add_error(f"Execution timed out after {timeout} seconds. The kernel has interrupted the execution.")
        executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:
        out_cap.add_error(f"Execution engine failure: {str(e)}")
        executor.shutdown(wait=False)

    var_list = inspect_variables(globals_dict)
    return out_cap.outputs, var_list
