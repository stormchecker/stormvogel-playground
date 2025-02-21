import docker
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = docker.from_env()

def start_sandbox(user_id):
    container_name = f"sandbox_{user_id}"
    existing_containers = client.containers.list(all=True, filters={"name": container_name})
    
    if existing_containers:
        container = existing_containers[0]
        if container.status != "running":
            container.start()
        logger.info(f"Reusing container {container.id} for user {user_id}")
    else:
        container = client.containers.run(
            "stormvogel",
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

def execute_code(user_id, code):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)
        logger.debug(f"Executing code for {user_id}: {repr(code)}")
        
        # Use a heredoc to write the code, ensuring proper termination
        write_cmd = f"cat << 'EOF' > /tmp/script.py\n{code}\nEOF"
        logger.debug(f"Write command: {write_cmd}")
        write_result = container.exec_run(["sh", "-c", write_cmd], stdout=True, stderr=True)
        write_output = write_result.output.decode()
        logger.debug(f"Write result: exit_code={write_result.exit_code}, output={write_output}")
        if write_result.exit_code != 0:
            return {"status": "error", "message": f"Failed to write code: {write_output}"}
        
        # Execute the script
        exec_result = container.exec_run("python3 /tmp/script.py", stdout=True, stderr=True)
        output = exec_result.output.decode()
        logger.debug(f"Execution output: exit_code={exec_result.exit_code}, output={output}")
        
        # Clean up
        container.exec_run("rm /tmp/script.py")
        
        if exec_result.exit_code == 0:
            return {"status": "success", "output": output}
        else:
            return {"status": "error", "message": f"Execution failed: {output}"}
    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found")
        return {"status": "error", "message": "Container not found"}
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        return {"status": "error", "message": f"Execution failed: {str(e)}"}

def stop_sandbox(user_id):
    container_name = f"sandbox_{user_id}"
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        logger.info(f"Sandbox {container_name} stopped and removed.")
        return True
    except docker.errors.NotFound:
        logger.warning(f"Sandbox {container_name} not found.")
        return False