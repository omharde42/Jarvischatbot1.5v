import subprocess
from typing import Dict, Any

def get_git_status() -> Dict[str, Any]:
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        changes = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]

        branch_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
        branch = branch_res.stdout.strip()

        if changes:
            spoken = f"Git is on branch {branch} with {len(changes)} modified files."
        else:
            spoken = f"Git working tree clean on branch {branch}."

        return {
            "success": True,
            "branch": branch,
            "modified_files": changes,
            "clean": len(changes) == 0,
            "spoken_response": spoken
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to get Git status."}

def get_git_log(limit: int = 5) -> Dict[str, Any]:
    try:
        res = subprocess.run(["git", "log", f"-n{limit}", "--oneline"], capture_output=True, text=True, check=True)
        commits = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
        return {
            "success": True,
            "commits": commits,
            "spoken_response": f"Retrieved last {len(commits)} git commits."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to retrieve git log."}
