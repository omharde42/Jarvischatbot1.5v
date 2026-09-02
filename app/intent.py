import os
import re
import json
import requests
from typing import Dict, Any, Optional
from app.safety import safety_engine, RiskLevel
from skills import system, filesystem, browser, developer, git, voice, productivity, ai

# Pluggable LLM client if API keys are set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class IntentParser:
    """Natural Language Intent Parser with Rule-Based Fallback + LLM Provider Layer"""

    @staticmethod
    def parse(command_text: str) -> Dict[str, Any]:
        raw_text = command_text.strip()
        text = raw_text.lower()

        # 1. System Status & CPU
        if re.search(r"\b(cpu|processor)\b", text) and re.search(r"\b(usage|status|most|top|using)\b", text):
            if "most" in text or "top" in text or "using the most" in text:
                return {"intent": "get_top_cpu", "args": {}}
            return {"intent": "get_system_status", "args": {}}

        if re.search(r"\b(system status|system info|telemetry|ram|memory)\b", text):
            return {"intent": "get_system_status", "args": {}}

        # 2. Filesystem Operations
        # List files
        if re.search(r"\b(what files|list files|show files|list directory|what's in this folder|what is in this folder)\b", text):
            return {"intent": "list_files", "args": {"directory": "."}}

        # Search files
        m = re.search(r"search (?:my )?(?:files|project|folder) for (.+)", raw_text, re.IGNORECASE) or re.search(r"find file (.+)", raw_text, re.IGNORECASE)
        if m:
            return {"intent": "search_files", "args": {"query": m.group(1).strip()}}

        # Create folder
        m = re.search(r"create (?:a )?new folder (?:called|named )?(.+)", raw_text, re.IGNORECASE) or re.search(r"make directory (.+)", raw_text, re.IGNORECASE)
        if m:
            folder_name = m.group(1).strip().strip("'\"")
            return {"intent": "create_folder", "args": {"folder_name": folder_name}}

        # Create file
        m = re.search(r"create (?:a )?file (?:called|named )?([^\s]+)", raw_text, re.IGNORECASE)
        if m:
            file_name = m.group(1).strip().strip("'\"")
            return {"intent": "create_file", "args": {"filepath": file_name, "content": ""}}

        # Read file
        m = re.search(r"read (?:the )?file (.+)", raw_text, re.IGNORECASE) or re.search(r"show (?:content of )?file (.+)", raw_text, re.IGNORECASE)
        if m:
            filepath = m.group(1).strip().strip("'\"")
            return {"intent": "read_file", "args": {"filepath": filepath}}

        # Delete file/folder
        m = re.search(r"delete (?:file|folder|path) (.+)", raw_text, re.IGNORECASE) or re.search(r"remove (?:file|folder|path) (.+)", raw_text, re.IGNORECASE)
        if m:
            target = m.group(1).strip().strip("'\"")
            return {"intent": "delete_file", "args": {"target_path": target}}

        # 3. Browser & Search
        m = re.search(r"search (?:the )?web for (.+)", raw_text, re.IGNORECASE) or re.search(r"google (.+)", raw_text, re.IGNORECASE)
        if m:
            return {"intent": "search_web", "args": {"query": m.group(1).strip()}}

        m = re.search(r"open (?:website|url|site) (.+)", raw_text, re.IGNORECASE) or re.search(r"open (https?://[^\s]+|github\.com[^\s]*|google\.com[^\s]*)", raw_text, re.IGNORECASE)
        if m:
            url = m.group(1).strip()
            return {"intent": "open_url", "args": {"url": url}}

        # Open common app shortcuts
        if "open github" in text:
            return {"intent": "open_url", "args": {"url": "https://github.com"}}
        if "open vs code" in text or "open vscode" in text or "open code" in text:
            return {"intent": "open_application", "args": {"target": "Visual Studio Code"}}
        if "open chrome" in text or "open browser" in text:
            return {"intent": "open_url", "args": {"url": "https://google.com"}}

        # 4. Development Operations
        m = re.search(r"search (?:source )?code for (.+)", raw_text, re.IGNORECASE) or re.search(r"find code (.+)", raw_text, re.IGNORECASE)
        if m:
            return {"intent": "search_code", "args": {"query": m.group(1).strip()}}

        if "explain" in text and ("error" in text or "exception" in text or "traceback" in text):
            return {"intent": "explain_error", "args": {"error_message": command_text}}

        if "start" in text and ("server" in text or "dev server" in text or "development server" in text):
            return {"intent": "start_dev_server", "args": {"command": "npm start"}}

        if "stop" in text and ("server" in text or "dev server" in text or "development server" in text):
            return {"intent": "stop_dev_server", "args": {}}

        # 5. Git Operations
        if "git status" in text or "project status" in text or "check repo" in text:
            return {"intent": "git_status", "args": {}}

        if "git log" in text or "recent commits" in text:
            return {"intent": "git_log", "args": {}}

        # 6. Productivity & Reminders
        m = re.search(r"set (?:a )?reminder (?:to |for )?(.+)", raw_text, re.IGNORECASE) or re.search(r"remind me to (.+)", raw_text, re.IGNORECASE)
        if m:
            return {"intent": "set_reminder", "args": {"text": m.group(1).strip()}}

        # Default conversational query
        return {"intent": "general_query", "args": {"query": command_text}}


async def parse_and_execute(command_text: str, context: Optional[dict] = None) -> Dict[str, Any]:
    parsed = IntentParser.parse(command_text)
    intent = parsed["intent"]
    args = parsed["args"]

    risk_level = safety_engine.classify_action(intent, args)

    # Router logic
    if risk_level == RiskLevel.HIGH:
        # High Risk requires confirmation
        if intent == "delete_file":
            target = args.get("target_path", "specified path")
            desc = f"delete '{target}'"
            func = filesystem.delete_path
            token = safety_engine.register_pending_action(desc, func, args)
            return {
                "success": False,
                "requires_confirmation": True,
                "confirmation_token": token,
                "intent": intent,
                "risk_level": risk_level,
                "prompt": f"JARVIS wants to delete '{target}'. Do you want me to continue?",
                "spoken_response": f"This will permanently delete {target}. Do you want me to continue?"
            }

    # Execute Low and Medium Risk directly
    if intent == "get_system_status":
        res = system.get_system_status_summary()
    elif intent == "get_top_cpu":
        res = system.get_top_cpu_app()
    elif intent == "list_files":
        res = filesystem.list_files(args.get("directory", "."))
    elif intent == "search_files":
        res = filesystem.search_files(args.get("query", ""))
    elif intent == "create_folder":
        res = filesystem.create_folder(args.get("folder_name", "New Folder"))
    elif intent == "create_file":
        res = filesystem.create_file(args.get("filepath", "new_file.txt"), args.get("content", ""))
    elif intent == "read_file":
        res = filesystem.read_file(args.get("filepath", ""))
    elif intent == "open_url":
        res = browser.open_url(args.get("url", ""))
    elif intent == "search_web":
        res = browser.search_web(args.get("query", ""))
    elif intent == "open_application":
        app_name = args.get("target", "Application")
        res = {
            "success": True,
            "target": app_name,
            "spoken_response": f"Opening {app_name}."
        }
    elif intent == "search_code":
        res = developer.search_code(args.get("query", ""))
    elif intent == "explain_error":
        res = developer.explain_error(args.get("error_message", ""))
    elif intent == "start_dev_server":
        res = developer.start_dev_server(args.get("command", "npm start"))
    elif intent == "stop_dev_server":
        res = developer.stop_dev_server()
    elif intent == "git_status":
        res = git.get_git_status()
    elif intent == "git_log":
        res = git.get_git_log()
    elif intent == "set_reminder":
        res = productivity.set_reminder(args.get("text", ""))
    else:
        # General query / response
        spoken = f"I processed your command: '{command_text}'"
        res = {
            "success": True,
            "query": command_text,
            "spoken_response": spoken
        }

    res["intent"] = intent
    res["risk_level"] = risk_level
    return res
