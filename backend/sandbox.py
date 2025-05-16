import docker
import logging
import re
import html
import io
import tarfile
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = docker.from_env()

def start_sandbox(user_id):
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
            mem_limit="256m",
            cpu_quota=50000,
        )
        logger.info(f"Started new sandbox container {container.id} for user {user_id}")
    return container

def separate_html(text):
    match = re.search(r'<!DOCTYPE html>.*?</html>', text, re.DOTALL | re.IGNORECASE)

    if match:
        html_content = match.group(0)  # Extract HTML content
        non_html_content = text.replace(html_content, "").strip()  # Remove HTML and clean up
    else:
        html_content = None
        non_html_content = text.strip()  # If no HTML, return the entire text as non-HTML

    return html_content, non_html_content

def write_file_to_container(src_path, container):
    tarstream = io.BytesIO()
    with tarfile.open(fileobj=tarstream, mode='w') as tar:
        tar.add(src_path, arcname=os.path.basename(src_path))    
    tarstream.seek(0)
    if container.put_archive("/", tarstream):
        logger.debug(f"Wrote {src_path} to {container.id}:/")
    else:
        logger.debug("File transfer failure")

def write_to_file(code, container):
    tarstream = io.BytesIO()
    with tarfile.TarFile(fileobj=tarstream, mode="w") as tar:
        tarinfo = tarfile.TarInfo("script.py")
        tarinfo.size = len(code.encode())
        tar.addfile(tarinfo, io.BytesIO(code.encode()))

    tarstream.seek(0)
    logger.debug(f"file{tarstream}")
    if container.put_archive("/", tarstream):
        logger.debug("File transfer success")
    else:
        logger.debug("File transfer failure")

def execute_code(user_id, code):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)
        container.restart(timeout=0)

        exec_results = container.exec_run("pgrep -fa python")
        exec_output = exec_results.output.decode()

        logger.debug(f"These processes are executing in container: {exec_output}")
        while "script.py" in exec_output:
            logger.debug(f"Different Python file running in container{exec_output}")
            exec_results = container.exec_run("pgrep -fa python")
            exec_output = exec_results.output.decode()

        logger.debug(f"Executing code for {user_id}: {repr(code)}")
        
        write_to_file(code, container)

        # Use the Linux timeout command to enforce a 30-second limit
        exec_result = container.exec_run(
            ["timeout", "30", "python3", "/script.py"], 
            stdout=True, stderr=True
        )
        output = exec_result.output.decode()

        if exec_result.exit_code == 124:  # 124 is the exit code for timeout
            logger.debug("Execution timed out!")
            return {"status": "error", "message": "Execution exceeded 10-second time limit, force quit"}

        if exec_result.exit_code == 0:
            logger.debug(f"Execution output: exit_code={exec_result.exit_code}, output={output}")
            #separate output from debug information
            iframe_html, logs = separate_html(output)
            return {"status": "success", "output_html": iframe_html , "output_non_html": logs}
        else:
            return {"status": "error", "message": f"Execution failed: {output}"}

    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found")
        return {"status": "error", "message": "Container not found"}
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        return {"status": "error", "message": f"Execution failed: {str(e)}"}

def lint_code(user_id, code):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)
        container.restart(timeout=0)

        logger.debug(f"Linting code for {user_id}: {repr(code)}")
        
        # Use a heredoc to write the code, ensuring proper termination
        file_path = "/script.py"
        write_to_file(code, container)
        
        # Run Ruff with the correct file path
        exec_result = container.exec_run(["ruff", "check", "--no-fix", file_path], stdout=True, stderr=True)
        output = exec_result.output.decode()
        logger.debug(f"Linting output: exit_code={exec_result.exit_code}, output={output}")

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
