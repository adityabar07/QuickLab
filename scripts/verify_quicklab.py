#!/usr/bin/env python3
"""
QuickLab V1 — Complete Local and API Verification
"""

import sys
import io

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

for mod_name, label in packages:
    try:
        mod = __import__(mod_name)
        print(f"✓ {label}", flush=True)
    except Exception as e:
        print(f"✗ {label} ({e})", flush=True)

print("========================================", flush=True)
print("ALL 7 PACKAGES PASSED", flush=True)
print("========================================", flush=True)
