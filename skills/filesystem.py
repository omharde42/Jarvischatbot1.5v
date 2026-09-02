import os
import shutil
from typing import Dict, Any

def list_files(directory: str = ".") -> Dict[str, Any]:
    try:
        target_dir = os.path.abspath(directory)
        if not os.path.exists(target_dir):
            return {
                "success": False,
                "error": f"Directory '{directory}' not found.",
                "spoken_response": f"I couldn't find the directory {directory}."
            }

        items = os.listdir(target_dir)
        files = [f for f in items if os.path.isfile(os.path.join(target_dir, f))]
        folders = [f for f in items if os.path.isdir(os.path.join(target_dir, f))]

        spoken = f"Found {len(files)} files and {len(folders)} folders in {os.path.basename(target_dir) or 'current directory'}."
        return {
            "success": True,
            "directory": target_dir,
            "files": files,
            "folders": folders,
            "spoken_response": spoken
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to list directory contents."}

def read_file(filepath: str) -> Dict[str, Any]:
    try:
        path = os.path.abspath(filepath)
        if not os.path.exists(path):
            return {"success": False, "error": f"File '{filepath}' not found.", "spoken_response": f"I couldn't find that file."}

        if os.path.getsize(path) > 100 * 1024:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2000) + "\n... [content truncated]"
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        filename = os.path.basename(path)
        return {
            "success": True,
            "filepath": path,
            "content": content,
            "spoken_response": f"Read content from {filename}."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to read the file."}

def create_folder(folder_name: str) -> Dict[str, Any]:
    try:
        path = os.path.abspath(folder_name)
        os.makedirs(path, exist_ok=True)
        name = os.path.basename(path)
        return {
            "success": True,
            "path": path,
            "spoken_response": f"Created folder called {name}."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to create folder."}

def create_file(filepath: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
    try:
        path = os.path.abspath(filepath)
        if os.path.exists(path) and not overwrite:
            return {
                "success": False,
                "error": f"File '{filepath}' already exists. Overwrite confirmation required.",
                "spoken_response": f"File {os.path.basename(path)} already exists."
            }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        name = os.path.basename(path)
        action_str = "Overwrote" if overwrite else "Created"
        return {
            "success": True,
            "filepath": path,
            "spoken_response": f"{action_str} file {name}."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to create file."}

def search_files(query: str, root_dir: str = ".") -> Dict[str, Any]:
    try:
        matches = []
        for root, dirs, files in os.walk(root_dir):
            if ".git" in dirs:
                dirs.remove(".git")
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            for f in files:
                if query.lower() in f.lower():
                    matches.append(os.path.relpath(os.path.join(root, f), root_dir))

        if matches:
            spoken = f"Found {len(matches)} matching files for {query}."
        else:
            spoken = f"No files matching {query} were found."

        return {
            "success": True,
            "query": query,
            "matches": matches,
            "spoken_response": spoken
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Error searching files."}

def delete_path(target_path: str) -> Dict[str, Any]:
    try:
        path = os.path.abspath(target_path)
        if not os.path.exists(path):
            return {"success": False, "error": "Path does not exist.", "spoken_response": "File or folder does not exist."}

        name = os.path.basename(path)
        if os.path.isdir(path):
            shutil.rmtree(path)
            spoken = f"Deleted folder {name}."
        else:
            os.remove(path)
            spoken = f"Deleted file {name}."

        return {
            "success": True,
            "path": path,
            "spoken_response": spoken
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": f"Failed to delete: {str(e)}"}
