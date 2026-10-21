import subprocess

def ping_server(target_ip):
    # REMEDIATED: Subprocess with argument array and shell=False
    return subprocess.run(["ping", "-c", "1", target_ip], capture_output=True, shell=False)

def execute_maintenance(script_name):
    # REMEDIATED: Argument list without shell=True
    return subprocess.run(["sh", f"scripts/{script_name}"], shell=False, capture_output=True)
