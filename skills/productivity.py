import time
from typing import Dict, Any, List

reminders: List[Dict[str, Any]] = []

def set_reminder(text: str, delay_minutes: float = 0) -> Dict[str, Any]:
    reminder_item = {
        "text": text,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + delay_minutes * 60))
    }
    reminders.append(reminder_item)
    return {
        "success": True,
        "reminder": reminder_item,
        "spoken_response": f"Reminder set: {text}"
    }

def get_reminders() -> Dict[str, Any]:
    return {
        "success": True,
        "reminders": reminders,
        "spoken_response": f"You have {len(reminders)} active reminders."
    }
