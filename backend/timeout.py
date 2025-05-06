import subprocess
import sys

try:
    result = subprocess.run(
        ["python3", "/script.py"], timeout=30, text=True
    )
    sys.exit(result.returncode)  # Propagate the exit code of the executed script
except subprocess.TimeoutExpired:
    print("Timeout10sec!", file=sys.stderr)
    sys.exit(1)  # Return a non-zero exit code for timeout
