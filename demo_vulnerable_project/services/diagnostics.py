import os
import subprocess

def ping_server(target_ip):
    # VULNERABILITY: Command Injection via os.system
    command = f"ping -c 1 {target_ip}"
    return os.system(command)

def execute_maintenance(script_name):
    # VULNERABILITY: Command Injection via shell=True
    return subprocess.run(f"sh scripts/{script_name}", shell=True, capture_output=True)
