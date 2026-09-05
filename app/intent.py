import os
import re
import json
import asyncio
from typing import Dict, Any, Optional
from app.safety import safety_engine, RiskLevel
from skills import system, filesystem, browser, developer, git, voice, productivity, ai
import system_controls
from ai_core import ai_engine

class IntentParser:
    """Natural Language Intent Parser with Rule-Based Fallback + Gemini AI Provider Layer"""

    @staticmethod
    def parse(command_text: str) -> Dict[str, Any]:
        raw_text = command_text.strip()
        text = raw_text.lower()

        # Phone Lock / Unlock simulation handling
        if system_controls.phone_lock.awaiting_pin:
            # If awaiting PIN input, route to verify PIN
            return {"intent": "verify_phone_pin", "args": {"input_pin": raw_text}}

        if re.search(r"\b(lock (the )?phone|lock phone)\b", text):
            return {"intent": "lock_phone", "args": {}}

        if re.search(r"\b(open (the )?phone|unlock (the )?phone|open phone|unlock phone)\b", text):
            return {"intent": "unlock_phone", "args": {}}

        # System Power Commands
        if re.search(r"\b(shutdown pc|shutdown computer|shutdown system|power off pc|turn off pc|shutdown)\b", text):
            return {"intent": "system_power", "args": {"action": "shutdown"}}

        if re.search(r"\b(restart pc|restart computer|restart system|reboot pc|reboot)\b", text):
            return {"intent": "system_power", "args": {"action": "restart"}}

        if re.search(r"\b(sleep pc|sleep computer|sleep system)\b", text):
            return {"intent": "system_power", "args": {"action": "sleep"}}

        # YouTube Search Automation
        m = re.search(r"(?:open youtube and search|search youtube for|search on youtube|youtube search) (.+)", raw_text, re.IGNORECASE) or \
            re.search(r"search (.+) on youtube", raw_text, re.IGNORECASE)
        if m:
            return {"intent": "search_youtube", "args": {"topic": m.group(1).strip()}}

        # Launch applications
        m = re.search(r"launch (notepad|chrome|vs code|vscode|code|terminal|cmd|app) (.+)?", raw_text, re.IGNORECASE) or \
            re.search(r"open (notepad|chrome|vs code|vscode|terminal|cmd)", raw_text, re.IGNORECASE)
        if m:
            app_target = m.group(1).strip()
            return {"intent": "open_application", "args": {"target": app_target}}

        # 1. System Status & CPU
        if re.search(r"\b(cpu|processor)\b", text) and re.search(r"\b(usage|status|most|top|using)\b", text):
            if "most" in text or "top" in text or "using the most" in text:
                return {"intent": "get_top_cpu", "args": {}}
            return {"intent": "get_system_status", "args": {}}

        if re.search(r"\b(system status|system info|telemetry|ram|memory)\b", text):
            return {"intent": "get_system_status", "args": {}}

        # 2. Filesystem Operations
        if re.search(r"\b(what files|list files|show files|list directory|what's in this folder|what is in this folder)\b", text):
            return {"intent": "list_files", "args": {"directory": "."}}

        m = re.search(r"search (?:my )?(?:files|project|folder) for (.+)", raw_text, re.IGNORECASE) or re.search(r"find file (.+)", raw_text, re.IGNORECASE)
        if m:
            return {"intent": "search_files", "args": {"query": m.group(1).strip()}}

        m = re.search(r"create (?:a )?new folder (?:(?:called|named)\s+)?(.+)", raw_text, re.IGNORECASE) or re.search(r"make directory (.+)", raw_text, re.IGNORECASE)
        if m:
            folder_name = m.group(1).strip().strip("'\"")
            return {"intent": "create_folder", "args": {"folder_name": folder_name}}

        m = re.search(r"create (?:a )?file (?:(?:called|named)\s+)?([^\s]+)", raw_text, re.IGNORECASE)
        if m:
            file_name = m.group(1).strip().strip("'\"")
            return {"intent": "create_file", "args": {"filepath": file_name, "content": ""}}

        m = re.search(r"read (?:the )?file (.+)", raw_text, re.IGNORECASE) or re.search(r"show (?:content of )?file (.+)", raw_text, re.IGNORECASE)
        if m:
            filepath = m.group(1).strip().strip("'\"")
            return {"intent": "read_file", "args": {"filepath": filepath}}

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

        # Default conversational query using Neural AI pipeline
        return {"intent": "general_ai_query", "args": {"query": command_text}}


async def parse_and_execute(command_text: str, context: Optional[dict] = None) -> Dict[str, Any]:
    parsed = IntentParser.parse(command_text)
    intent = parsed["intent"]
    args = parsed["args"]

    if intent == "create_file":
        filepath = args.get("filepath", "new_file.txt")
        if os.path.exists(os.path.abspath(filepath)):
            risk_level = RiskLevel.HIGH
        else:
            risk_level = safety_engine.classify_action(intent, args)
    else:
        risk_level = safety_engine.classify_action(intent, args)

    # Router logic for High Risk confirmation flow
    if risk_level == RiskLevel.HIGH:
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
        elif intent == "create_file":
            filepath = args.get("filepath", "new_file.txt")
            desc = f"overwrite file '{filepath}'"
            confirm_args = dict(args)
            confirm_args["overwrite"] = True
            func = filesystem.create_file
            token = safety_engine.register_pending_action(desc, func, confirm_args)
            return {
                "success": False,
                "requires_confirmation": True,
                "confirmation_token": token,
                "intent": intent,
                "risk_level": risk_level,
                "prompt": f"File '{filepath}' already exists. Do you want to overwrite it?",
                "spoken_response": f"File {filepath} already exists. Do you want me to overwrite it?"
            }
        elif intent == "system_power":
            action = args.get("action", "shutdown")
            desc = f"execute system {action}"
            func = system_controls.execute_system_power
            token = safety_engine.register_pending_action(desc, func, args)
            return {
                "success": False,
                "requires_confirmation": True,
                "confirmation_token": token,
                "intent": intent,
                "risk_level": risk_level,
                "prompt": f"JARVIS wants to execute system {action}. Do you want me to proceed?",
                "spoken_response": f"Are you sure you want to {action} the system?"
            }
        else:
            return {
                "success": False,
                "intent": intent,
                "risk_level": risk_level,
                "error": f"High-risk action '{intent}' is not supported or missing confirmation handler.",
                "spoken_response": f"Execution of high-risk action {intent} was denied."
            }

    # Execute Low and Medium Risk directly
    if intent == "lock_phone":
        res = system_controls.phone_lock.lock_phone()
    elif intent == "unlock_phone":
        res = system_controls.phone_lock.request_unlock()
    elif intent == "verify_phone_pin":
        res = system_controls.phone_lock.verify_pin(args.get("input_pin", ""))
    elif intent == "search_youtube":
        res = await asyncio.to_thread(system_controls.search_youtube, args.get("topic", ""))
    elif intent == "get_system_status":
        res = await asyncio.to_thread(system.get_system_status_summary)
    elif intent == "get_top_cpu":
        res = await asyncio.to_thread(system.get_top_cpu_app)
    elif intent == "list_files":
        res = await asyncio.to_thread(filesystem.list_files, args.get("directory", "."))
    elif intent == "search_files":
        res = await asyncio.to_thread(filesystem.search_files, args.get("query", ""))
    elif intent == "create_folder":
        res = await asyncio.to_thread(filesystem.create_folder, args.get("folder_name", "New Folder"))
    elif intent == "create_file":
        res = await asyncio.to_thread(
            filesystem.create_file,
            args.get("filepath", "new_file.txt"),
            args.get("content", ""),
            args.get("overwrite", False)
        )
    elif intent == "read_file":
        res = await asyncio.to_thread(filesystem.read_file, args.get("filepath", ""))
    elif intent == "open_url":
        res = await asyncio.to_thread(browser.open_url, args.get("url", ""))
    elif intent == "search_web":
        res = await asyncio.to_thread(browser.search_web, args.get("query", ""))
    elif intent == "open_application":
        res = await asyncio.to_thread(system_controls.launch_app, args.get("target", "Application"))
    elif intent == "search_code":
        res = await asyncio.to_thread(developer.search_code, args.get("query", ""))
    elif intent == "explain_error":
        res = await asyncio.to_thread(developer.explain_error, args.get("error_message", ""))
    elif intent == "start_dev_server":
        res = await asyncio.to_thread(developer.start_dev_server, args.get("command", "npm start"))
    elif intent == "stop_dev_server":
        res = await asyncio.to_thread(developer.stop_dev_server, args.get("command"))
    elif intent == "git_status":
        res = await asyncio.to_thread(git.get_git_status)
    elif intent == "git_log":
        res = await asyncio.to_thread(git.get_git_log)
    elif intent == "set_reminder":
        res = await asyncio.to_thread(productivity.set_reminder, args.get("text", ""))
    else:
        # General query / response via Gemini AI engine
        res = await asyncio.to_thread(ai_engine.generate_response, args.get("query", command_text))

    res["intent"] = intent
    res["risk_level"] = risk_level
    return res
