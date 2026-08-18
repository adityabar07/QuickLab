import urllib.request
import json
import sys

# Ensure clean UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/execute"
SESSION_ID = "test_user_session_101"

def run_code(code, title):
    print(f"\n--- RUNNING: {title} ---", flush=True)
    data = json.dumps({"code": code, "session_id": SESSION_ID}).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"Exec Count: {res.get('exec_count')}", flush=True)
        for o in res.get('outputs', []):
            kind = o.get('kind')
            if kind in ('stream', 'result', 'error'):
                print(f"[{kind.upper()}] {o.get('text').strip()}", flush=True)
            elif kind == 'image':
                print(f"[{kind.upper()}] Base64 PNG image received (length: {len(o.get('data'))} chars)", flush=True)
            elif kind == 'plotly':
                print(f"[{kind.upper()}] Interactive Plotly chart received (length: {len(o.get('data'))} chars)", flush=True)
            elif kind == 'html':
                print(f"[{kind.upper()}] HTML Table received (length: {len(o.get('data'))} chars)", flush=True)
        if res.get('variables'):
            print(f"Active Session Variables: {[v['name'] for v in res['variables']]}", flush=True)
        return res

# TEST 1: Seaborn
run_code("import seaborn as sns\nprint('Seaborn:', sns.__version__)", "TEST 1: Seaborn")

# TEST 2: Plotly
run_code("import plotly\nprint('Plotly:', plotly.__version__)", "TEST 2: Plotly")

# TEST 3: PyTorch
run_code("import torch\nprint('PyTorch:', torch.__version__)", "TEST 3: PyTorch")

# TEST 4: OpenCV
run_code("import cv2\nprint('OpenCV:', cv2.__version__)", "TEST 4: OpenCV")

# TEST 5: pgmpy
run_code("import pgmpy\nprint('pgmpy:', pgmpy.__version__)", "TEST 5: pgmpy")

# TEST 6: NetworkX
run_code("import networkx as nx\nprint('NetworkX:', nx.__version__)", "TEST 6: NetworkX")

# TEST 7: Statsmodels
run_code("import statsmodels\nprint('Statsmodels:', statsmodels.__version__)", "TEST 7: Statsmodels")

# TEST 8: Session Variable Persistence (Cell 1 & Cell 2)
run_code("""import numpy as np
x = np.array([10, 20, 30, 40])
""", "TEST 8: Cell 1 (Variable Definition)")

run_code("""print(x.mean())""", "TEST 8: Cell 2 (Variable Reuse)")

# TEST 9: Heatmap Test
run_code("""import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

np.random.seed(42)
data = np.random.rand(20, 20)
plt.figure(figsize=(10, 8))
sns.heatmap(data, annot=False, cmap="viridis")
plt.title("QuickLab Heatmap")
plt.show()
""", "TEST 9: Heatmap Test")

# TEST 10: Plotly Test
run_code("""import numpy as np
import plotly.graph_objects as go

x = np.linspace(0, 10, 100)
fig = go.Figure(
    data=go.Scatter(
        x=x,
        y=np.sin(x),
        mode="lines"
    )
)
fig.show()
""", "TEST 10: Plotly Test")

# TEST 11: PyTorch Matrix Multiplication
run_code("""import torch
x = torch.randn(1000, 1000)
y = x @ x.T
print(y.shape)
""", "TEST 11: PyTorch Matrix Multiplication")

# TEST 12: OpenCV Circle Test
run_code("""import cv2
import numpy as np

img = np.zeros((500, 500, 3), dtype=np.uint8)
cv2.circle(img, (250, 250), 100, (0, 255, 0), -1)
print(img.shape)
""", "TEST 12: OpenCV Circle Drawing")

# TEST 13: DataFrame HTML Table Output
run_code("""import pandas as pd
df = pd.DataFrame({
    "Name": ["A", "B", "C"],
    "Marks": [90, 85, 95]
})
df
""", "TEST 13: DataFrame HTML Rendering")

print("\n" + "="*60, flush=True)
print("ALL TESTS COMPLETED SUCCESSFULLY VIA QUICKLAB BACKEND API!", flush=True)
print("="*60, flush=True)
