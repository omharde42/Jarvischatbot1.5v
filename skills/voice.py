from typing import Dict, Any

def format_voice_response(text: str) -> Dict[str, Any]:
    clean_text = text.strip()
    return {
        "success": True,
        "spoken_response": clean_text
    }
