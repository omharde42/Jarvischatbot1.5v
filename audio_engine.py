import sys
import time
import logging
import threading
from typing import Callable, Optional, List

logger = logging.getLogger("audio_engine")

class TTSEngine:
    """Thread-safe Text-to-Speech engine tuning using pyttsx3 with collision prevention."""

    def __init__(self, rate: int = 175, volume: float = 0.95):
        self.rate = rate
        self.volume = volume
        self.tts_lock = threading.Lock()
        self._engine = None

    def _get_engine(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            # Try to select a natural voice if available
            voices = engine.getProperty("voices")
            if voices:
                for v in voices:
                    if "english" in v.name.lower() or "david" in v.name.lower() or "zira" in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
            return engine
        except Exception as e:
            logger.warning("pyttsx3 engine initialization error: %s", e)
            return None

    def speak(self, text: str):
        """Thread-safe speech synthesis."""
        if not text or not text.strip():
            return

        with self.tts_lock:
            engine = self._get_engine()
            if engine:
                try:
                    logger.info("JARVIS Speaking: %s", text)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as e:
                    logger.error("TTS runtime error during speech output: %s", e)
            else:
                logger.info("[Console Speech Fallback] JARVIS: %s", text)

tts_engine = TTSEngine()

class WakeWordListener:
    """Continuous, non-blocking hands-free background listener with auto-recovery."""

    def __init__(self, wake_words: Optional[List[str]] = None):
        self.wake_words = [w.lower() for w in (wake_words or ["jarvis", "hey jarvis"])]
        self.is_listening = False

    def listen_and_recognize(self, timeout: int = 5, phrase_time_limit: int = 7) -> Optional[str]:
        """Listens from microphone with ambient noise tuning and auto-recovery."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                text = recognizer.recognize_google(audio)
                return text.strip().lower()
        except Exception as e:
            # Silently handle common speech recognition exceptions without crashing
            error_type = type(e).__name__
            if "WaitTimeoutError" in error_type or "UnknownValueError" in error_type:
                return None
            elif "RequestError" in error_type:
                logger.warning("Speech recognition network request dropped: %s", e)
                return None
            else:
                logger.debug("Audio recognition loop exception: %s", e)
                return None

    def start_hands_free_loop(self, on_wake_word_detected: Callable[[str], None], stop_check_fn: Optional[Callable[[], bool]] = None):
        """Runs continuous listening loop in a thread-safe, non-blocking manner."""
        self.is_listening = True
        logger.info("Continuous wake-word listener active. Listening for: %s", self.wake_words)

        while self.is_listening:
            if stop_check_fn and stop_check_fn():
                break

            spoken_text = self.listen_and_recognize(timeout=4, phrase_time_limit=6)
            if spoken_text:
                logger.debug("Heard input: %s", spoken_text)
                for wake_word in self.wake_words:
                    if wake_word in spoken_text:
                        logger.info("Wake word detected in input: '%s'", spoken_text)
                        # Extract query payload after wake word if present
                        payload = spoken_text.split(wake_word, 1)[-1].strip()
                        on_wake_word_detected(payload if payload else spoken_text)
                        break

            time.sleep(0.1)

wake_listener = WakeWordListener()
