import os
import shlex
import subprocess
from typing import Dict, Any, Optional

active_dev_servers = {}

def search_code(query: str, root_dir: str = ".") -> Dict[str, Any]:
    try:
        matches = []
        for root, dirs, files in os.walk(root_dir):
            if ".git" in dirs: dirs.remove(".git")
            if "node_modules" in dirs: dirs.remove("node_modules")
            for f in files:
                if f.endswith((".py", ".js", ".ts", ".html", ".css", ".json", ".md")):
                    filepath = os.path.join(root, f)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as file_content:
                            for idx, line in enumerate(file_content, 1):
                                if query.lower() in line.lower():
                                    rel_path = os.path.relpath(filepath, root_dir)
                                    matches.append({
                                        "file": rel_path,
                                        "line": idx,
                                        "content": line.strip()
                                    })
                                    if len(matches) >= 30:
                                        break
                    except Exception:
                        pass
                if len(matches) >= 30:
                    break
            if len(matches) >= 30:
                break
        spoken = f"Found {len(matches)} code occurrences of {query}." if matches else f"No occurrences of {query} found in codebase."
        return {
            "success": True,
            "query": query,
            "matches": matches,
            "spoken_response": spoken
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Error searching code."}

def explain_error(error_message: str) -> Dict[str, Any]:
    msg = error_message.strip()
    explanation = "An unexpected error occurred."

    if "ModuleNotFoundError" in msg or "Cannot find module" in msg:
        explanation = "A missing library or module was referenced. Try running `pip install` or `npm install` for the missing dependency."
    elif "SyntaxError" in msg:
        explanation = "There is a syntax error in your code, such as a missing parenthesis, bracket, or invalid keyword."
    elif "PermissionError" in msg or "EACCES" in msg:
        explanation = "The current process lacks sufficient permissions to read, write, or execute the resource."
    elif "ConnectionRefusedError" in msg or "ECONNREFUSED" in msg:
        explanation = "The connection attempt was refused. Check if the target service or port is active and accessible."
    elif "KeyError" in msg or "TypeError" in msg:
        explanation = "An invalid key access or data type mismatch occurred in the script."
    else:
        explanation = f"Error details: {msg}. Check terminal logs or stack trace for exact line numbers."

    return {
        "success": True,
        "error_message": msg,
        "explanation": explanation,
        "spoken_response": explanation
    }

def start_dev_server(command: str = "npm start") -> Dict[str, Any]:
    try:
        proc = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        active_dev_servers[command] = proc.pid
        return {
            "success": True,
            "command": command,
            "pid": proc.pid,
            "spoken_response": f"Started development server using {command}."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to start development server."}

def stop_dev_server(command: Optional[str] = None) -> Dict[str, Any]:
    try:
        if not active_dev_servers:
            return {"success": False, "message": "No active development servers recorded.", "spoken_response": "No active servers found to stop."}

        targets = (
            [(command, active_dev_servers[command])]
            if command in active_dev_servers
            else list(active_dev_servers.items()) if command is None else []
        )
        if not targets:
            return {
                "success": False,
                "message": f"No active development server recorded for {command}.",
                "spoken_response": "No matching active server found to stop.",
            }

        stopped = []
        for cmd, pid in targets:
            try:
                os.kill(pid, 9)
                stopped.append(cmd)
                del active_dev_servers[cmd]
            except Exception:
                pass
        return {
            "success": True,
            "stopped": stopped,
            "spoken_response": "Stopped active development servers."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to stop development server."}
