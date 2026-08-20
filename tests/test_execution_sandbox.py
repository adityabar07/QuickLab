import pytest
from server.execution import run_code_in_session

def test_timeout_enforcement():
    # Attempt an infinite loop with a 2-second timeout
    infinite_loop_code = "import time\nwhile True:\n    time.sleep(0.1)"
    globals_dict = {"__name__": "__main__"}
    outputs, variables = run_code_in_session(
        code=infinite_loop_code,
        globals_dict=globals_dict,
        session_cwd=".",
        timeout_seconds=2
    )
    assert len(outputs) > 0
    assert any(o.get("kind") == "error" and "timed out" in o.get("text", "").lower() for o in outputs)

def test_numpy_and_pandas_execution():
    code = """import numpy as np
import pandas as pd
arr = np.array([10, 20, 30])
df = pd.DataFrame({"val": arr})
df
"""
    globals_dict = {"__name__": "__main__"}
    outputs, variables = run_code_in_session(
        code=code,
        globals_dict=globals_dict,
        session_cwd=".",
        timeout_seconds=10
    )
    assert any(o.get("kind") == "html" and "<table" in o.get("data", "") for o in outputs)
    assert any(v["name"] == "arr" for v in variables)
    assert any(v["name"] == "df" for v in variables)

def test_matplotlib_capture():
    code = """import matplotlib.pyplot as plt
import numpy as np
x = np.linspace(0, 10, 20)
plt.plot(x, np.sin(x))
plt.show()
"""
    globals_dict = {"__name__": "__main__"}
    outputs, variables = run_code_in_session(
        code=code,
        globals_dict=globals_dict,
        session_cwd=".",
        timeout_seconds=10
    )
    assert any(o.get("kind") == "image" and len(o.get("data", "")) > 100 for o in outputs)

def test_syntax_error_traceback():
    code = "print('unterminated string"
    globals_dict = {"__name__": "__main__"}
    outputs, _ = run_code_in_session(
        code=code,
        globals_dict=globals_dict,
        session_cwd=".",
        timeout_seconds=5
    )
    assert len(outputs) > 0
    assert any(o.get("kind") == "error" and "SyntaxError" in o.get("text", "") for o in outputs)
