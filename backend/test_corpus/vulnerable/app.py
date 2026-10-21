import os
import sqlite3
import pickle

# Hardcoded fake credential for testing (Gitleaks / Semgrep test)
FAKE_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"


def get_user_profile(user_id: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABILITY 1: SQL Injection
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    return cursor.fetchall()


def ping_host(host_ip: str):
    # VULNERABILITY 2: Command Injection
    command = f"ping -c 1 {host_ip}"
    return os.system(command)


def load_session_state(serialized_data: bytes):
    # VULNERABILITY 3: Insecure Deserialization
    return pickle.loads(serialized_data)


def read_user_report(filename: str):
    # VULNERABILITY 4: Path Traversal
    filepath = f"reports/{filename}"
    with open(filepath, "r") as f:
        return f.read()
