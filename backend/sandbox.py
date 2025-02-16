import docker

client = docker.from_env()

def start_sandbox(user_id):
    container_name = f"sandbox_{user_id}"
    existing_containers = client.containers.list(all=True, filters={"name": container_name})
    
    if existing_containers:
        container = existing_containers[0]
        if container.status != "running":
            container.start()
        print(f"Reusing container {container.id} for user {user_id}")
    else:
        container = client.containers.run(
            "stormvogel",      #stormvogel container
            runtime="runsc",   #gvisor runtime
            detach=True,
            name=container_name,
            stdin_open=True,
            tty=True,
            security_opt=["no-new-privileges"],
            mem_limit="256m",  #memory usage, up to change
            cpu_quota=50000,   #cpu usage, up to change
        )
        print(f"Started new sandbox container {container.id} for user {user_id}")

    return container

def execute_code(user_id, code):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)
        exec_result = container.exec_run(f"python3 -c {code!r}", stdout=True, stderr=True)
        output = exec_result.output.decode()
        return {"status": "success", "output": output}
    except docker.errors.NotFound:
        return {"status": "error", "message": "Container not found"}

def stop_sandbox(user_id):
    container_name = f"sandbox_{user_id}"
    
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        print(f"Sandbox {container_name} stopped and removed.")
        return True
    except docker.errors.NotFound:
        print(f"Sandbox {container_name} not found.")
        return False

