import os
import json
import sqlite3
import subprocess
from pathlib import Path

# Safe: Loaded from environment variables
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID")


def get_user_profile(user_id: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SAFE: Parameterized query protects against SQL Injection
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchall()


def ping_host(host_ip: str):
    # SAFE: Subprocess with argument array and shell=False
    return subprocess.run(["ping", "-c", "1", host_ip], capture_output=True, shell=False)


def load_session_state(json_data: str):
    # SAFE: Safe JSON deserialization instead of pickle
    return json.loads(json_data)


def read_user_report(filename: str):
    # SAFE: Canonical path validation to prevent path traversal
    base_dir = Path("reports").resolve()
    target_file = (base_dir / filename).resolve()
    
    if base_dir not in target_file.parents:
        raise ValueError("Invalid path access attempted")
        
    with open(target_file, "r") as f:
        return f.read()
