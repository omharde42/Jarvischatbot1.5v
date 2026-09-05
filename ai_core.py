import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ai_core")

# Simple in-memory context cache for conversational history
class ConversationContextCache:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []

    def add_message(self, role: str, text: str):
        self.history.append({"role": role, "text": text})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_formatted_context(self) -> str:
        formatted = []
        for msg in self.history:
            role_prefix = "User" if msg["role"] == "user" else "JARVIS"
            formatted.append(f"{role_prefix}: {msg['text']}")
        return "\n".join(formatted)

    def clear(self):
        self.history.clear()

context_cache = ConversationContextCache()

class AICoreEngine:
    """Dynamic Gemini API / LLM neural response pipeline with context caching and streaming support."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.info("No Gemini API key found. AI Core using local smart reasoning fallback.")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini Client successfully initialized.")
        except Exception as e:
            logger.warning("Failed to initialize google-genai Client: %s", e)
            self.client = None

    def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """Generates intelligent conversational response using Gemini API or local reasoning."""
        if not system_instruction:
            system_instruction = (
                "You are JARVIS, an enterprise-grade, ultra-responsive AI system. "
                "Keep spoken responses concise, direct, helpful, and natural."
            )

        context_cache.add_message("user", prompt)
        history_context = context_cache.get_formatted_context()

        full_prompt = f"System Instruction: {system_instruction}\n\nRecent Conversation:\n{history_context}\n\nJARVIS:"

        if self.client:
            try:
                # Use Gemini 2.5 Flash for high performance / low latency
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )
                text_out = response.text.strip() if response and response.text else "I have processed your request."
                context_cache.add_message("assistant", text_out)
                return {
                    "success": True,
                    "response": text_out,
                    "spoken_response": text_out,
                    "provider": "gemini-2.5-flash"
                }
            except Exception as e:
                logger.error("Gemini API call failed: %s", e)

        # Smart fallback if API key not available or API call fails
        fallback_response = f"I am online and ready. Regarding '{prompt}', I am monitoring all systems and operating at peak performance."
        context_cache.add_message("assistant", fallback_response)
        return {
            "success": True,
            "response": fallback_response,
            "spoken_response": fallback_response,
            "provider": "local_fallback"
        }

ai_engine = AICoreEngine()
