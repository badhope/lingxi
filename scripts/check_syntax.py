#!/usr/bin/env python3
"""Check Python syntax for all .py files in api/ core directories."""
import ast
import os
import sys

base = r"C:\Users\X1882\.qclaw\workspace\dify"
errors = []
checked = 0

for root, dirs, files in os.walk(os.path.join(base, "api")):
    # Skip unwanted dirs
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "migrations", ".egg-info")]
    
    for fn in files:
        if not fn.endswith(".py"):
            continue
        fpath = os.path.join(root, fn)
        try:
            with open(fpath, "rb") as f:
                content = f.read()
            ast.parse(content)
            checked += 1
        except SyntaxError as e:
            rel = os.path.relpath(fpath, base)
            errors.append((rel, str(e)))
        except Exception as e:
            rel = os.path.relpath(fpath, base)
            errors.append((rel, f"OTHER: {e}"))

print(f"===== Syntax Check Results =====")
print(f"Checked: {checked} files")
print(f"Errors: {len(errors)}")

if errors:
    print(f"\n--- First 20 errors ---")
    for rel, err in errors[:20]:
        print(f"  ❌ {rel}")
        print(f"     {err}")
else:
    print("✅ All files have valid Python syntax")
