#!/usr/bin/env python3
"""
QuickLab V1 — Official Package Verification Suite
Tests the 7 standard QuickLab libraries:
1. NumPy
2. Pandas
3. Matplotlib
4. Seaborn
5. SciPy
6. SymPy
7. Scikit-learn
"""

import sys
import io

# Ensure UTF-8 output encoding
sys.stdout.reconfigure(encoding='utf-8')

packages = [
    ("numpy", "NumPy"),
    ("pandas", "Pandas"),
    ("matplotlib", "Matplotlib"),
    ("seaborn", "Seaborn"),
    ("scipy", "SciPy"),
    ("sympy", "SymPy"),
    ("sklearn", "Scikit-learn")
]

print("========================================", flush=True)
print("QUICKLAB ENVIRONMENT CHECK", flush=True)
print("========================================", flush=True)
print(f"Python: {sys.version.split()[0]}\n", flush=True)

all_passed = True
for mod_name, label in packages:
    try:
        mod = __import__(mod_name)
        ver = getattr(mod, "__version__", "installed")
        print(f"✓ {label}", flush=True)
    except Exception as e:
        print(f"✗ {label} (Error: {e})", flush=True)
        all_passed = False

print("========================================", flush=True)
if all_passed:
    print("ALL 7 PACKAGES PASSED", flush=True)
else:
    print("SOME PACKAGES FAILED", flush=True)
print("========================================\n", flush=True)

# Functional Tests for the 7 Libraries
print("--- RUNNING FUNCTIONAL UNIT TESTS ---", flush=True)

# 1. NumPy
try:
    import numpy as np
    numbers = np.array([10, 20, 30, 40, 50])
    assert np.mean(numbers) == 30.0
    assert np.max(numbers) == 50
    assert np.min(numbers) == 10
    print("  [OK] NumPy Functional Test             : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] NumPy Functional Test           : FAILED ({e})", flush=True)
    all_passed = False

# 2. Pandas
try:
    import pandas as pd
    data = {"Name": ["Aditya", "Rahul", "Amit", "Priya"], "Marks": [85, 92, 78, 95]}
    df = pd.DataFrame(data)
    assert df["Marks"].mean() == 87.5
    assert "<table" in df.to_html()
    print("  [OK] Pandas Functional Test            : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] Pandas Functional Test          : FAILED ({e})", flush=True)
    all_passed = False

# 3. Matplotlib
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y)
    ax.set_title("Sine Wave")
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    assert len(buf.getvalue()) > 100
    print("  [OK] Matplotlib Sine Wave Test         : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] Matplotlib Sine Wave Test       : FAILED ({e})", flush=True)
    all_passed = False

# 4. Seaborn Heatmap
try:
    import seaborn as sns
    np.random.seed(42)
    heatmap_data = np.random.rand(20, 20)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=False, cmap="viridis", ax=ax)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    assert len(buf.getvalue()) > 100
    print("  [OK] Seaborn 20x20 Heatmap Test        : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] Seaborn 20x20 Heatmap Test      : FAILED ({e})", flush=True)
    all_passed = False

# 5. SciPy
try:
    from scipy import optimize
    def equation(x):
        return x**2 - 4
    result = optimize.root(equation, 1)
    assert abs(result.x[0] - 2.0) < 1e-4
    print("  [OK] SciPy Root Finding Test           : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] SciPy Root Finding Test         : FAILED ({e})", flush=True)
    all_passed = False

# 6. SymPy
try:
    import sympy as sp
    x = sp.symbols("x")
    eq = x**2 - 5*x + 6
    sols = sp.solve(eq, x)
    sol_ints = [int(s) for s in sols]
    assert 2 in sol_ints and 3 in sol_ints
    assert "(x - 2)*(x - 3)" in str(sp.factor(eq)) or "(x - 3)*(x - 2)" in str(sp.factor(eq))
    print("  [OK] SymPy Solve & Factorize Test      : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] SymPy Solve & Factorize Test    : FAILED ({e})", flush=True)
    all_passed = False

# 7. Scikit-learn
try:
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    assert acc >= 0.85
    print("  [OK] Scikit-learn RandomForest Test    : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] Scikit-learn RandomForest Test  : FAILED ({e})", flush=True)
    all_passed = False

# 8. Combined Data Science Test
try:
    np.random.seed(42)
    comb_data = pd.DataFrame({
        "Math": np.random.randint(40, 100, 100),
        "Science": np.random.randint(40, 100, 100),
        "Computer": np.random.randint(40, 100, 100)
    })
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=comb_data, x="Math", y="Computer", ax=ax)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    assert len(buf.getvalue()) > 100
    print("  [OK] Combined Data Science Pipeline    : PASSED", flush=True)
except Exception as e:
    print(f"  [FAIL] Combined Data Science Pipeline  : FAILED ({e})", flush=True)
    all_passed = False

print("========================================", flush=True)
if all_passed:
    print("ALL FUNCTIONAL TESTS PASSED!", flush=True)
    sys.exit(0)
else:
    print("SOME FUNCTIONAL TESTS FAILED!", flush=True)
    sys.exit(1)
