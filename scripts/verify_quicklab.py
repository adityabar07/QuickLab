import sys

packages = [
    ('numpy', 'NumPy'),
    ('pandas', 'Pandas'),
    ('seaborn', 'Seaborn'),
    ('plotly', 'Plotly'),
    ('torch', 'PyTorch'),
    ('torchvision', 'Torchvision'),
    ('torchaudio', 'Torchaudio'),
    ('cv2', 'OpenCV'),
    ('pgmpy', 'pgmpy'),
    ('networkx', 'NetworkX'),
    ('statsmodels', 'Statsmodels'),
    ('scipy', 'SciPy'),
    ('sympy', 'SymPy'),
    ('sklearn', 'Scikit-learn'),
    ('PIL', 'Pillow'),
    ('nltk', 'NLTK'),
    ('spacy', 'spaCy'),
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('openpyxl', 'OpenPyXL'),
    ('xlsxwriter', 'XlsxWriter'),
]

print("="*60, flush=True)
print("QUICKLAB EXECUTION ENGINE VERIFICATION", flush=True)
print(f"Python Version: {sys.version.split()[0]}", flush=True)
print("="*60, flush=True)

for mod_name, label in packages:
    try:
        mod = __import__(mod_name)
        ver = getattr(mod, '__version__', 'available')
        print(f"  [OK] {label:20s}: {ver}", flush=True)
    except Exception as e:
        print(f"  [FAIL] {label:20s}: ERROR ({e})", flush=True)

print("\n" + "="*60, flush=True)
print("RUNNING FUNCTIONAL USER TEST CASES", flush=True)
print("="*60, flush=True)

# TEST 1: Seaborn Heatmap
try:
    import numpy as np
    import seaborn as sns
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    np.random.seed(42)
    data = np.random.rand(20, 20)
    plt.figure(figsize=(10, 8))
    sns.heatmap(data, annot=False, cmap="viridis")
    plt.title("QuickLab Heatmap")
    plt.savefig('heatmap_test.png')
    plt.close()
    print("  [OK] Heatmap Test              : SUCCESS (heatmap_test.png created)", flush=True)
except Exception as e:
    print(f"  [FAIL] Heatmap Test            : ERROR ({e})", flush=True)

# TEST 2: Plotly Scatter
try:
    import numpy as np
    import plotly.graph_objects as go
    x = np.linspace(0, 10, 100)
    fig = go.Figure(data=go.Scatter(x=x, y=np.sin(x), mode="lines"))
    html = fig.to_html(include_plotlyjs=False)
    print(f"  [OK] Plotly Test               : SUCCESS (Interactive HTML rendered, {len(html)} bytes)", flush=True)
except Exception as e:
    print(f"  [FAIL] Plotly Test             : ERROR ({e})", flush=True)

# TEST 3: PyTorch Matrix Multiplication
try:
    import torch
    x = torch.randn(1000, 1000)
    y = x @ x.T
    print(f"  [OK] PyTorch Test              : SUCCESS (shape = {y.shape})", flush=True)
except Exception as e:
    print(f"  [FAIL] PyTorch Test            : ERROR ({e})", flush=True)

# TEST 4: OpenCV Circle Drawing
try:
    import cv2
    import numpy as np
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.circle(img, (250, 250), 100, (0, 255, 0), -1)
    print(f"  [OK] OpenCV Test               : SUCCESS (shape = {img.shape})", flush=True)
except Exception as e:
    print(f"  [FAIL] OpenCV Test             : ERROR ({e})", flush=True)

# TEST 5: pgmpy Bayesian Network
try:
    from pgmpy.models import BayesianNetwork
    from pgmpy.factors.discrete import TabularCPD
    model = BayesianNetwork([('A', 'B')])
    cpd_a = TabularCPD('A', 2, [[0.6], [0.4]])
    cpd_b = TabularCPD('B', 2, [[0.9, 0.2], [0.1, 0.8]], evidence=['A'], evidence_card=[2])
    model.add_cpds(cpd_a, cpd_b)
    valid = model.check_model()
    print(f"  [OK] pgmpy Test                : SUCCESS (check_model = {valid})", flush=True)
except Exception as e:
    print(f"  [FAIL] pgmpy Test              : ERROR ({e})", flush=True)

# TEST 6: NetworkX Shortest Path
try:
    import networkx as nx
    G = nx.Graph()
    G.add_edge("A", "B", weight=4)
    G.add_edge("B", "C", weight=2)
    G.add_edge("A", "C", weight=7)
    path = nx.shortest_path(G, "A", "C", weight="weight")
    print(f"  [OK] NetworkX Test             : SUCCESS (shortest_path = {path})", flush=True)
except Exception as e:
    print(f"  [FAIL] NetworkX Test           : ERROR ({e})", flush=True)

# TEST 7: Statsmodels OLS
try:
    import statsmodels.api as sm
    import numpy as np
    X = np.linspace(0, 10, 50)
    X = sm.add_constant(X)
    y = 2.5 * X[:, 1] + 1.2 + np.random.normal(size=50)
    model = sm.OLS(y, X).fit()
    print(f"  [OK] Statsmodels Test          : SUCCESS (R-squared = {model.rsquared:.4f})", flush=True)
except Exception as e:
    print(f"  [FAIL] Statsmodels Test        : ERROR ({e})", flush=True)

print("="*60, flush=True)
