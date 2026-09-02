import uuid
import time
from enum import Enum
from typing import Dict, Any, Callable, Optional, Tuple

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class PendingAction:
    def __init__(self, action_id: str, description: str, func: Callable, kwargs: dict, timeout_seconds: int = 60):
        self.action_id = action_id
        self.description = description
        self.func = func
        self.kwargs = kwargs
        self.created_at = time.time()
        self.timeout_seconds = timeout_seconds

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.timeout_seconds

class SafetyEngine:
    def __init__(self):
        self.pending_actions: Dict[str, PendingAction] = {}

    def cleanup_expired(self):
        expired_keys = [token for token, action in self.pending_actions.items() if action.is_expired()]
        for token in expired_keys:
            del self.pending_actions[token]

    def register_pending_action(self, description: str, func: Callable, kwargs: dict) -> str:
        self.cleanup_expired()
        token = str(uuid.uuid4())[:8]
        self.pending_actions[token] = PendingAction(token, description, func, kwargs)
        return token

    def process_confirmation(self, token: str, confirmed: bool) -> Dict[str, Any]:
        self.cleanup_expired()
        if token not in self.pending_actions:
            return {
                "success": False,
                "error": "Confirmation request expired or not found.",
                "spoken_response": "The confirmation request has expired or was not found."
            }

        action = self.pending_actions.pop(token)
        if not confirmed:
            return {
                "success": False,
                "canceled": True,
                "message": f"Action canceled: {action.description}",
                "spoken_response": f"Canceled {action.description}."
            }

        try:
            result = action.func(**action.kwargs)
            if isinstance(result, dict):
                return result
            return {
                "success": True,
                "result": result,
                "spoken_response": f"Successfully completed: {action.description}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "spoken_response": f"Failed to execute {action.description}: {str(e)}"
            }

    @staticmethod
    def classify_action(intent: str, args: dict) -> RiskLevel:
        high_risk_intents = [
            "delete_file",
            "delete_folder",
            "format_disk",
            "modify_security",
            "run_destructive_command",
            "git_hard_reset"
        ]

        medium_risk_intents = [
            "install_package",
            "run_script",
            "modify_config",
            "git_commit",
            "git_push",
            "stop_server"
        ]

        if intent in high_risk_intents:
            return RiskLevel.HIGH
        elif intent in medium_risk_intents:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

safety_engine = SafetyEngine()
