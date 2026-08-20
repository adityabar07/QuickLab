import urllib.request
import json
import sys

# Ensure clean UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/execute"
SESSION_ID = "v1_user_session_test"

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
            elif kind == 'html':
                print(f"[{kind.upper()}] HTML Table received (length: {len(o.get('data'))} chars)", flush=True)
        if res.get('variables'):
            print(f"Active Session Variables: {[v['name'] for v in res['variables']]}", flush=True)
        return res

# 1. NumPy
run_code("""import numpy as np
numbers = np.array([10, 20, 30, 40, 50])
print("Numbers:", numbers)
print("Mean:", np.mean(numbers))
print("Maximum:", np.max(numbers))
print("Minimum:", np.min(numbers))
""", "1. NumPy Example")

# 2. Pandas
run_code("""import pandas as pd
data = {
    "Name": ["Aditya", "Rahul", "Amit", "Priya"],
    "Marks": [85, 92, 78, 95]
}
df = pd.DataFrame(data)
print(df)
print("Average:", df["Marks"].mean())
""", "2. Pandas Example")

# 3. Matplotlib Sine Wave
run_code("""import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("Sine Wave")
plt.xlabel("X")
plt.ylabel("sin(X)")
plt.grid(True)
plt.show()
""", "3. Matplotlib Sine Wave")

# 4. Seaborn 20x20 Heatmap
run_code("""import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

np.random.seed(42)
data = np.random.rand(20, 20)

plt.figure(figsize=(10, 8))
sns.heatmap(
    data,
    annot=False,
    cmap="viridis"
)
plt.title("20 × 20 Heatmap")
plt.show()
""", "4. Seaborn Heatmap")

# 5. SciPy
run_code("""from scipy import optimize

def equation(x):
    return x**2 - 4

result = optimize.root(equation, 1)
print("Solution:", result.x)
""", "5. SciPy Root Finding")

# 6. SymPy
run_code("""import sympy as sp

x = sp.symbols("x")
equation = x**2 - 5*x + 6
solutions = sp.solve(equation, x)

print("Equation:", equation)
print("Solutions:", solutions)
print("Factorized:", sp.factor(equation))
""", "6. SymPy Solve & Factorize")

# 7. Scikit-learn
run_code("""from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

iris = load_iris()
X = iris.data
y = iris.target

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
accuracy = accuracy_score(
    y_test,
    predictions
)
print("Model accuracy:", accuracy)
""", "7. Scikit-learn Model Training")

# 8. Combined Data Science Example
run_code("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

np.random.seed(42)
data = pd.DataFrame({
    "Math": np.random.randint(40, 100, 100),
    "Science": np.random.randint(40, 100, 100),
    "Computer": np.random.randint(40, 100, 100)
})

print(data.head())
print("\\nStatistics:")
print(data.describe())

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=data,
    x="Math",
    y="Computer"
)
plt.title("Math vs Computer Marks")
plt.show()
""", "8. Combined Data Science Pipeline")

# 9. Multiple Code Cells / Session Persistence
run_code("""import numpy as np
x = np.array([10, 20, 30, 40, 50])
""", "9. Session Persistence — Cell 1")

run_code("""print(x.mean())""", "9. Session Persistence — Cell 2")

run_code("""y = x * 2
print(y)
""", "9. Session Persistence — Cell 3")

# 10. DataFrame Cell Output (Last Expression)
run_code("""import pandas as pd
df = pd.DataFrame({
    "Student": ["A", "B", "C"],
    "Score": [90, 85, 95]
})
df
""", "10. DataFrame HTML Table Output")

# 11. Error Handling (Syntax error)
run_code("""print(hello""", "11. Error Handling (Syntax Error)")

print("\n" + "="*60, flush=True)
print("ALL 11 V1 TEST SUITES EXECUTED VIA QUICKLAB API!", flush=True)
print("="*60, flush=True)
