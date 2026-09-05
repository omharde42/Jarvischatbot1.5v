import os
import sys
import asyncio
import logging
import signal
import threading
from typing import Optional

from audio_engine import tts_engine, wake_listener
from app.intent import parse_and_execute

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("jarvis_main")

class JarvisAssistant:
    """Enterprise-grade JARVIS Voice Assistant main controller."""

    def __init__(self):
        self.is_running = False

    def speak(self, text: str):
        print(f"\n🤖 JARVIS: {text}")
        tts_engine.speak(text)

    def process_command(self, command: str):
        clean_cmd = command.strip()
        if not clean_cmd:
            return

        print(f"\n👤 User: {clean_cmd}")

        # Check for explicit exit or stop command
        if clean_cmd.lower() in ["exit", "stop", "quit", "goodbye", "bye jarvis", "stop jarvis"]:
            self.speak("Goodbye, sir. Shutting down assistant services.")
            self.stop()
            return

        try:
            # Process command synchronously using event loop run
            result = asyncio.run(parse_and_execute(clean_cmd))
            response_text = result.get("spoken_response") or result.get("response") or "Command processed."
            self.speak(response_text)

            # If action requires confirmation
            if result.get("requires_confirmation"):
                token = result.get("confirmation_token")
                print(f"🔒 Confirmation Required Token: {token}")

        except Exception as e:
            logger.exception("Error processing command: %s", e)
            self.speak("I encountered an error while processing that command.")

    def start_voice_loop(self):
        """Starts continuous non-blocking wake word loop with auto-recovery."""
        self.speak("JARVIS system online and ready. Listening for wake word 'Jarvis'...")
        self.is_running = True

        def on_wake(payload: str):
            if not payload:
                self.speak("Yes sir? How can I assist you?")
                # Listen for the follow-up query
                query = wake_listener.listen_and_recognize(timeout=5, phrase_time_limit=8)
                if query:
                    self.process_command(query)
                else:
                    self.speak("I didn't catch that. Please call me again when needed.")
            else:
                self.process_command(payload)

        wake_listener.start_hands_free_loop(
            on_wake_word_detected=on_wake,
            stop_check_fn=lambda: not self.is_running
        )

    def start_cli_interactive(self):
        """CLI text interaction mode for headless / non-audio environments."""
        self.speak("JARVIS system online in interactive terminal mode. Type 'exit' to quit.")
        self.is_running = True

        while self.is_running:
            try:
                user_input = input("\n🎙 Input Command (or press Enter): ").strip()
                if not user_input:
                    continue
                self.process_command(user_input)
            except (KeyboardInterrupt, EOFError):
                print("\nShutting down...")
                self.stop()
                break

    def stop(self):
        self.is_running = False
        wake_listener.is_listening = False

def main():
    assistant = JarvisAssistant()

    # Handle termination signals cleanly
    def signal_handler(sig, frame):
        logger.info("Termination signal received. Exiting JARVIS.")
        assistant.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if "--voice" in sys.argv:
        assistant.start_voice_loop()
    else:
        assistant.start_cli_interactive()

if __name__ == "__main__":
    main()
