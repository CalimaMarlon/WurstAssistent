import os
import threading
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai
import subprocess


class VoiceAssistant:
    """Push-to-talk: Das Mikrofon wird nur durch den Dashboard-Button aktiviert."""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.history = []
        self._busy = False
        self._lock = threading.Lock()

    def listen_once(self, callback):
        with self._lock:
            if self._busy:
                callback("Der Sprachassistent arbeitet bereits.")
                return
            self._busy = True

        threading.Thread(
            target=self._listen_worker, args=(callback,), daemon=True
        ).start()

    def _listen_worker(self, callback):
        try:
            if self.client is None:
                callback("GEMINI_API_KEY fehlt. Bitte .env-Datei einrichten.")
                return

            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            prompt = recognizer.recognize_google(audio, language="de-DE")
            if any(word in prompt.lower() for word in ("tschüss", "schüss", "auf wiedersehen")):
                answer = "Auf Wiedersehen!"
            else:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                answer = response.text or "Ich konnte leider keine Antwort erzeugen."

            self.speak(answer)
            callback(f"Du: {prompt} | Assistent: {answer}")
        except sr.WaitTimeoutError:
            callback("Ich habe nichts gehört. Drücke den Button und versuche es erneut.")
        except sr.UnknownValueError:
            callback("Ich habe dich nicht verstanden. Bitte versuche es erneut.")
        except Exception as exc:
            print("Sprachassistent-Fehler:", exc)
            callback(f"Fehler beim Sprachassistenten: {exc}")
        finally:
            with self._lock:
                self._busy = False

    @staticmethod
    def speak(text):
        print("ASSISTENT:", text)
        try:
            subprocess.run(
                ["espeak-ng", "-v", "de", "-s", "145", text],
                check=False, timeout=60
            )
        except Exception as exc:
            print("Sprachausgabe-Fehler:", exc)

    def stop(self):
        pass
