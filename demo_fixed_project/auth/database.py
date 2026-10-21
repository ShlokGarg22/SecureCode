import os
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
