import os

def download_user_document(user_folder, filename):
    # VULNERABILITY: Path Traversal
    filepath = f"uploads/{user_folder}/{filename}"
    with open(filepath, "r") as f:
        return f.read()
