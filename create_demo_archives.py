import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Define vulnerable files
VULNERABLE_FILES = {
    "auth/database.py": '''import sqlite3

# VULNERABILITY: Hardcoded AWS Access Key (Gitleaks / Semgrep)
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
DATABASE_URL = "sqlite:///users.db"

def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABILITY: SQL Injection via string formatting
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"Executing: {query}")
    cursor.execute(query)
    return cursor.fetchone()

def search_products(term):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABILITY: SQL Injection via concatenation
    sql = "SELECT * FROM products WHERE name LIKE '%" + term + "%'"
    cursor.execute(sql)
    return cursor.fetchall()
''',

    "services/diagnostics.py": '''import os
import subprocess

def ping_server(target_ip):
    # VULNERABILITY: Command Injection via os.system
    command = f"ping -c 1 {target_ip}"
    return os.system(command)

def execute_maintenance(script_name):
    # VULNERABILITY: Command Injection via shell=True
    return subprocess.run(f"sh scripts/{script_name}", shell=True, capture_output=True)
''',

    "controllers/file_manager.py": '''import os

def download_user_document(user_folder, filename):
    # VULNERABILITY: Path Traversal
    filepath = f"uploads/{user_folder}/{filename}"
    with open(filepath, "r") as f:
        return f.read()
''',

    "handlers/session_handler.py": '''import pickle
import ast

def restore_session(raw_bytes):
    # VULNERABILITY: Insecure Deserialization via pickle
    user_session = pickle.loads(raw_bytes)
    return user_session

def calculate_formula(user_expression):
    # VULNERABILITY: Code Injection via eval
    return eval(user_expression)
''',

    "frontend_api/server.js": '''const { exec } = require("child_process");

// VULNERABILITY: Hardcoded API secret
const STRIPE_SECRET_KEY = "api_key = \\"mock_stripe_test_XXXXXXXXXXXXXXXX\\"";

function runBackup(directory) {
    // VULNERABILITY: Node.js Command Injection
    exec(`tar -czf backup.tar.gz ${directory}`, (err, stdout) => {
        if (err) console.error(err);
    });
}

function getUserOrders(db, customerId) {
    // VULNERABILITY: SQL Injection in JavaScript
    const sql = `SELECT * FROM orders WHERE customer_id = '${customerId}'`;
    return db.query(sql);
}
'''
}

# Define remediated/fixed files for before-and-after diff verification
FIXED_FILES = {
    "auth/database.py": '''import os
import sqlite3

# REMEDIATED: Loaded securely from environment variable
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")

def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # REMEDIATED: Parameterized query prevents SQL Injection
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    return cursor.fetchone()

def search_products(term):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # REMEDIATED: Parameterized LIKE query
    sql = "SELECT * FROM products WHERE name LIKE ?"
    cursor.execute(sql, (f"%{term}%",))
    return cursor.fetchall()
''',

    "services/diagnostics.py": '''import subprocess

def ping_server(target_ip):
    # REMEDIATED: Subprocess with argument array and shell=False
    return subprocess.run(["ping", "-c", "1", target_ip], capture_output=True, shell=False)

def execute_maintenance(script_name):
    # REMEDIATED: Argument list without shell=True
    return subprocess.run(["sh", f"scripts/{script_name}"], shell=False, capture_output=True)
''',

    "controllers/file_manager.py": '''from pathlib import Path

def download_user_document(user_folder, filename):
    # REMEDIATED: Canonical path validation prevents Path Traversal
    base_dir = Path("uploads").resolve()
    target_path = (base_dir / user_folder / filename).resolve()
    
    if base_dir not in target_path.parents:
        raise PermissionError("Access denied: invalid file path traversal attempt")
        
    with open(target_path, "r") as f:
        return f.read()
''',

    "handlers/session_handler.py": '''import json

def restore_session(raw_json_str):
    # REMEDIATED: Safe JSON deserialization instead of pickle
    return json.loads(raw_json_str)

def calculate_formula(user_expression):
    # REMEDIATED: Safe literal evaluation
    import ast
    return ast.literal_eval(user_expression)
''',

    "frontend_api/server.js": '''const { execFile } = require("child_process");

// REMEDIATED: Read from environment variable
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;

function runBackup(directory) {
    // REMEDIATED: execFile with argument array prevents command injection
    execFile("tar", ["-czf", "backup.tar.gz", directory], (err, stdout) => {
        if (err) console.error(err);
    });
}

function getUserOrders(db, customerId) {
    // REMEDIATED: Parameterized query placeholder
    const sql = "SELECT * FROM orders WHERE customer_id = ?";
    return db.query(sql, [customerId]);
}
'''
}


def create_zip(filename: str, files_dict: dict, folder_name: str):
    zip_path = BASE_DIR / filename
    folder_path = BASE_DIR / folder_name

    # Create directory structure on disk as well
    for rel_path, content in files_dict.items():
        file_path = folder_path / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    # Write to zip archive
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in files_dict:
            file_on_disk = folder_path / rel_path
            zf.write(file_on_disk, arcname=rel_path)

    print(f"[OK] Created {filename} ({len(files_dict)} files)")
    return zip_path


if __name__ == "__main__":
    vulnerable_zip = create_zip("demo_vulnerable_project.zip", VULNERABLE_FILES, "demo_vulnerable_project")
    fixed_zip = create_zip("demo_fixed_project.zip", FIXED_FILES, "demo_fixed_project")
    print(f"\nAll test projects successfully created in: {BASE_DIR}")
