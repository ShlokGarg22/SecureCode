import sqlite3

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
