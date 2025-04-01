import subprocess
import sys

try:
    result = subprocess.run(
        ["python3", "/script.py"], timeout=10, text=True
    )        
except subprocess.TimeoutExpired:
    print("Timeout10sec!", file=sys.stderr)
