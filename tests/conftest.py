import os
import sys

# Ensure src/ is on sys.path so tests can import packages under `src`
# This is a simple, local fix for test collection environments that don't
# install the package into the environment (CI, local pytest runs, etc).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
