import docker
import logging
import re
import io
import tarfile
import subprocess
import threading
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

client = docker.from_env()

class ContainerManager:
    def __init__(self):
        self.container_timestamps = {}
        self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self.cleanup_thread.start()
    
    def register_container(self, user_id):
        """Register when a container was created/accessed"""
        self.container_timestamps[user_id] = datetime.now()
    
    def _periodic_cleanup(self):
        """Clean up containers older than 1 hour"""
        while True:
            try:
                current_time = datetime.now()
                expired_users = []
                
                for user_id, timestamp in self.container_timestamps.items():
                    if current_time - timestamp > timedelta(hours=1):
                        expired_users.append(user_id)
                
                for user_id in expired_users:
                    self._force_cleanup_container(user_id)
                    del self.container_timestamps[user_id]
                
                time.sleep(300)
            except Exception as e:
                logger.error("Periodic cleanup failed: %s", e)
    
    def _force_cleanup_container(self, user_id):
        """Force cleanup a specific container"""
        container_name = f"sandbox_{user_id}"
        try:
            container = client.containers.get(container_name)
            container.stop(timeout=1)
            container.remove()
            logger.info("Force cleaned up container for user %s", user_id)
        except docker.errors.NotFound:
            pass  # Container already gone
        except Exception as e:
            logger.error("Failed to force cleanup container for %s: %s", user_id, e)

container_manager = ContainerManager()

# Either reuses and existing container or creates a new one
def start_sandbox(user_id):
    container_manager.register_container(user_id)
    container_name = f"sandbox_{user_id}"
    existing_containers = client.containers.list(filters={"name": container_name})
    logger.info(existing_containers)
    
    if existing_containers:
        container = existing_containers[0]
        logger.info(f"Reusing container {container.id} for user {user_id}")
    else:
        container = client.containers.run(
            "stormvogel/stormvogel",
            runtime="runsc",
            detach=True,
            name=container_name,
            stdin_open=True,
            tty=True,
            security_opt=["no-new-privileges"],
            network_mode="none",
            mem_limit="512m",
            command="sh",
        )
        logger.info(f"Started new sandbox container {container.id} for user {user_id}")
    return container

# Matches HTML code, and separates it from the rest of the string
def separate_html(text):
    match = re.search(r'<!DOCTYPE html>.*?</html>', text, re.DOTALL | re.IGNORECASE)

    if match:
        html_content = match.group(0)  # Extract HTML content
        non_html_content = text.replace(html_content, "").strip()  # Remove HTML and clean up
    else:
        html_content = None
        non_html_content = text.strip()  # If no HTML, return the entire text as non-HTML

    return html_content, non_html_content

# Write code to a temporary file and send that to the container
def write_to_file(filename, code, container):
    tarstream = io.BytesIO()
    with tarfile.TarFile(fileobj=tarstream, mode="w") as tar:
        tarinfo = tarfile.TarInfo(filename)
        tarinfo.size = len(code.encode())
        tar.addfile(tarinfo, io.BytesIO(code.encode()))

    tarstream.seek(0)
    logger.debug(f"file{tarstream}")
    if container.put_archive("/", tarstream):
        logger.debug("File transfer success")
    else:
        logger.debug("File transfer failure")

# Executes a specified file in the container and returns the result if succesful
def execute_code(user_id, code):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)

        exec_results = container.exec_run("pgrep -fa python")
        exec_output = exec_results.output.decode()

        logger.debug(f"These processes are executing in container: {exec_output}")
        while "script.py" in exec_output:
            logger.debug(f"Different Python file running in container{exec_output}")
            exec_results = container.exec_run("pgrep -fa python")
            exec_output = exec_results.output.decode()

        logger.debug(f"Executing code for {user_id}: {repr(code)}")
        
        write_to_file("script.py", code, container)

        # Read the content from resources/playground.py and write it into the container
        with open("resources/playground.py", "r", encoding="utf-8") as f:
            playground_code = f.read()
            write_to_file("playground.py", playground_code, container)

        # Container.exec_run does not have an timeout, so we use subprocess here
        # exec_result = container.exec_run(
        #     ["timeout", "30", "python3", "/script.py"], 
        #     stdout=True, stderr=True
        # )
        result = subprocess.run(
            ["docker", "exec", container.name, "timeout", "30s", "python3", "/script.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=40
        )

        output = result.stdout + result.stderr
        exit_code = result.returncode

        container.restart(timeout=0)

        if exit_code == 124:  # 124 is the exit code for bash timeout command
            logger.debug("Execution timed out!")
            return {"status": "error", "message": "Execution exceeded 30-second time limit, force quit"}

        if exit_code == 0:
            logger.debug(f"Execution output: exit_code={exit_code}, output={output}")
            # Separate output from debug information
            iframe_html, logs = separate_html(output)
            return {"status": "success", "output_html": iframe_html , "output_non_html": logs}
        else:
            return {"status": "error", "message": f"Execution failed: {output}"}

    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found")
        return {"status": "error", "message": "Container not found"}
    except subprocess.TimeoutExpired:
        logger.debug("External timeout triggered")
        return {"status": "error", "message": "External timeout was triggered, abnormal termination"}
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        return {"status": "error", "message": f"Execution failed: {str(e)}"}

# Similar to execute code but, uses ruff command to provide linting feedback for the file
def lint_code(user_id, code):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)

        logger.debug(f"Linting code for {user_id}: {repr(code)}")
        
        # Use a heredoc to write the code, ensuring proper termination
        file_path = "/script.py"
        write_to_file(code, container)
        
        # Run Ruff with the correct file path
        exec_result = container.exec_run(["ruff", "check", "--no-fix", file_path], stdout=True, stderr=True)
        output = exec_result.output.decode()
        logger.debug(f"Linting output: exit_code={exec_result.exit_code}, output={output}")

        container.restart(timeout=0)

        if exec_result.exit_code == 0:
            return {"status": "success", "lint_output": output.strip()}
        else:
            return {"status": "error", "message": output}
    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found")
        return {"status": "error", "message": "Container not found"}
    except Exception as e:
        logger.error(f"Linting failed: {str(e)}")
        return {"status": "error", "message": f"Linting failed: {str(e)}"}

# Stops the container and removes it
def stop_sandbox(user_id):
    container_name = f"sandbox_{user_id}"
    try:
        container = client.containers.get(container_name)
        container.stop(timeout=1)
        container.remove()
        logger.info(f"Sandbox {container_name} stopped and removed.")
        return True
    except docker.errors.NotFound:
        logger.warning(f"Sandbox {container_name} not found.")
        return False

# Saves code from a tab, puts to a temporary file and sends to specified container
def save_tabs(user_id, tabs):
    container_name = f"sandbox_{user_id}"

    try:
        container = client.containers.get(container_name)

        # Create a tar archive of the tabs data
        tarstream = io.BytesIO()
        with tarfile.open(fileobj=tarstream, mode='w') as tar:
            for tab_name, tab_content in tabs.items():
                tab_info = tarfile.TarInfo(name=tab_name)  
                tab_info.size = len(tab_content.encode())
                tar.addfile(tab_info, io.BytesIO(tab_content.encode()))
        tarstream.seek(0)

        # Transfer the tar archive to the container, save it in the same directory as the script
        if container.put_archive("/app", tarstream):
            logger.debug(f"Tabs saved successfully in container {container_name}")
            return {"status": "success", "message": "Tabs saved successfully"}
        else:
            logger.error(f"Failed to save tabs in container {container_name}")
            return {"status": "error", "message": "Failed to save tabs in container"}

    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found")
        return {"status": "error", "message": "Container not found"}
    except Exception as e:
        logger.error(f"Failed to save tabs: {str(e)}")
        return {"status": "error", "message": f"Failed to save tabs: {str(e)}"}
