import pytest
import os
import time
import docker
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sandbox import (
    start_sandbox,
    stop_sandbox,
    lint_code,
    execute_code,
)

client = docker.from_env()
USER_ID = "test-real-user"

def wait_for_container_ready(container, timeout=5):
    for _ in range(timeout):
        if container.status != "running":
            container.reload()
        else:
            return True
        time.sleep(1)
    return False

@pytest.fixture(scope="module")
def real_container():
    container = start_sandbox(USER_ID)
    assert container is not None
    assert wait_for_container_ready(container), "Container did not start"
    yield container
    stop_sandbox(USER_ID)

def test_lint_code_success(real_container):
    result = lint_code(USER_ID, "x = 1\n")
    assert result["status"] == "success"
    assert "script.py" not in result["lint_output"]  # no issues expected

def test_lint_code_failure(real_container):
    result = lint_code(USER_ID, "x==1\n")  # should trigger linter
    assert result["status"] == "error"
    assert "script.py" in result["message"]

def test_execute_code_success(real_container):
    result = execute_code(USER_ID, "print('Hello from real test')")
    assert result["status"] == "success"
    assert "Hello from real test" in result["output_non_html"]

def test_execute_code_timeout(real_container):
    result = execute_code(USER_ID, "while True:\n  pass")
    assert result["status"] == "error"
    assert "10-second" in result["message"]  # from Timeout10sec!

def test_execute_code_crash(real_container):
    result = execute_code(USER_ID, "1/0")
    assert result["status"] == "error"
    assert  "Execution failed" in result["message"]
