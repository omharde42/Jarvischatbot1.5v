from typing import Dict, Any

def summarize_text(text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#")]
    summary_sentences = lines[:3]
    summary = " ".join(summary_sentences)
    if not summary:
        summary = "No content to summarize."
    return {
        "success": True,
        "summary": summary,
        "spoken_response": f"Summary: {summary[:150]}"
    }
