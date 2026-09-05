import os
import sys
import re
import logging
import platform
import subprocess
import webbrowser
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger("system_controls")

class PhoneLockState:
    """Simulated phone lock and passkey verification state machine."""

    def __init__(self, pin: str = "1234"):
        self.pin = pin
        self.is_phone_locked = False
        self.awaiting_pin = False

    def lock_phone(self) -> Dict[str, Any]:
        self.is_phone_locked = True
        self.awaiting_pin = False
        return {
            "success": True,
            "is_phone_locked": True,
            "spoken_response": "Phone locked."
        }

    def request_unlock(self) -> Dict[str, Any]:
        if not self.is_phone_locked:
            return {
                "success": True,
                "is_phone_locked": False,
                "spoken_response": "Phone is already unlocked."
            }
        self.awaiting_pin = True
        return {
            "success": True,
            "is_phone_locked": True,
            "awaiting_pin": True,
            "spoken_response": "Please tell me the PIN to unlock the phone."
        }

    def verify_pin(self, input_pin: str) -> Dict[str, Any]:
        clean_pin = "".join(re.findall(r"\d+", str(input_pin)))
        if clean_pin == self.pin:
            self.is_phone_locked = False
            self.awaiting_pin = False
            return {
                "success": True,
                "is_phone_locked": False,
                "awaiting_pin": False,
                "spoken_response": "PIN correct. Phone unlocked."
            }
        else:
            return {
                "success": False,
                "is_phone_locked": True,
                "awaiting_pin": True,
                "spoken_response": "Incorrect PIN. Access denied."
            }

phone_lock = PhoneLockState()

def execute_system_power(action: str) -> Dict[str, Any]:
    """Executes cross-platform system power commands (shutdown, restart, sleep) cleanly."""
    os_name = platform.system().lower()
    action = action.lower()

    try:
        if action == "shutdown":
            if "windows" in os_name:
                cmd = ["shutdown", "/s", "/t", "1"]
            elif "darwin" in os_name:
                cmd = ["sudo", "shutdown", "-h", "now"]
            else:
                cmd = ["shutdown", "-h", "now"]
            spoken = "Shutting down system."

        elif action == "restart":
            if "windows" in os_name:
                cmd = ["shutdown", "/r", "/t", "1"]
            elif "darwin" in os_name:
                cmd = ["sudo", "shutdown", "-r", "now"]
            else:
                cmd = ["shutdown", "-r", "now"]
            spoken = "Restarting system."

        elif action == "sleep":
            if "windows" in os_name:
                cmd = ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
            elif "darwin" in os_name:
                cmd = ["pmset", "sleepnow"]
            else:
                cmd = ["systemctl", "suspend"]
            spoken = "Putting system to sleep."
        else:
            return {"success": False, "error": f"Unknown system power action '{action}'.", "spoken_response": f"Unknown power command {action}."}

        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "action": action, "spoken_response": spoken}

    except Exception as e:
        logger.error("Error executing system power command '%s': %s", action, e)
        return {"success": False, "error": str(e), "spoken_response": f"Failed to execute system {action}."}

def launch_app(app_name: str) -> Dict[str, Any]:
    """Subprocess trigger to launch desktop applications cleanly without freezing main loop."""
    app_lower = app_name.lower().strip()
    os_name = platform.system().lower()

    try:
        if "notepad" in app_lower:
            cmd = ["notepad"] if "windows" in os_name else ["gedit"]
        elif "code" in app_lower or "vs code" in app_lower or "vscode" in app_lower:
            cmd = ["code"]
        elif "chrome" in app_lower or "browser" in app_lower:
            webbrowser.open("https://www.google.com")
            return {"success": True, "app": "Chrome", "spoken_response": "Launching Chrome."}
        elif "terminal" in app_lower or "cmd" in app_lower or "shell" in app_lower:
            if "windows" in os_name:
                cmd = ["cmd.exe", "/c", "start"]
            elif "darwin" in os_name:
                cmd = ["open", "-a", "Terminal"]
            else:
                cmd = ["x-terminal-emulator"]
        else:
            cmd = [app_lower]

        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "app": app_name, "spoken_response": f"Launching {app_name}."}

    except Exception as e:
        logger.error("Error launching app '%s': %s", app_name, e)
        return {"success": False, "error": str(e), "spoken_response": f"Could not launch application {app_name}."}

def search_youtube(topic: str) -> Dict[str, Any]:
    """Parses query parameters and triggers YouTube search results page."""
    try:
        clean_topic = topic.strip()
        encoded_query = urllib.parse.quote_plus(clean_topic)
        youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        webbrowser.open(youtube_url)
        return {
            "success": True,
            "topic": clean_topic,
            "url": youtube_url,
            "spoken_response": f"Searching YouTube for {clean_topic}."
        }
    except Exception as e:
        logger.error("Error launching YouTube search for '%s': %s", topic, e)
        return {"success": False, "error": str(e), "spoken_response": "Failed to open YouTube search."}
