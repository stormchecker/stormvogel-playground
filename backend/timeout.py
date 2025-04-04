import subprocess
import sys

try:
    result = subprocess.run(
        ["python3", "/script.py"], timeout=30, text=True
    )        
except subprocess.TimeoutExpired:
    print("Timeout10sec!", file=sys.stderr)
