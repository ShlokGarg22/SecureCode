from pathlib import Path

def download_user_document(user_folder, filename):
    # REMEDIATED: Canonical path validation prevents Path Traversal
    base_dir = Path("uploads").resolve()
    target_path = (base_dir / user_folder / filename).resolve()
    
    if base_dir not in target_path.parents:
        raise PermissionError("Access denied: invalid file path traversal attempt")
        
    with open(target_path, "r") as f:
        return f.read()
