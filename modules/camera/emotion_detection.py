import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from picamera2 import Picamera2

from config.settings import (
    CAMERA_WIDTH, CAMERA_HEIGHT, MODEL_PATH, EMOTION_CONFIDENCE
)


EMOTIONS = [
    "NEUTRAL", "GLUECKLICH", "UEBERRASCHT", "TRAURIG",
    "SAUER", "EKEL", "ANGST", "VERACHTUNG"
]


class EmotionDetection:
    """Liest Kamera und Emotionen in einem Hintergrund-Thread."""

    def __init__(self):
        self.latest_emotion = "wird vorbereitet"
        self._running = False
        self._thread = None
        self._camera = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        try:
            model_file = Path(MODEL_PATH)
            if not model_file.exists():
                self.latest_emotion = "Modell fehlt (siehe models/)"
                return

            face_detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            if face_detector.empty():
                raise RuntimeError("OpenCV-Gesichtsklassifikator fehlt")

            session = ort.InferenceSession(
                str(model_file), providers=["CPUExecutionProvider"]
            )
            input_info = session.get_inputs()[0]

            self._camera = Picamera2()
            config = self._camera.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
            )
            self._camera.configure(config)
            self._camera.start()
            time.sleep(2)

            history = deque(maxlen=20)
            while self._running:
                frame = self._camera.capture_array()
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                faces = face_detector.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=6, minSize=(80, 80)
                )

                if len(faces) == 0:
                    self.latest_emotion = "kein Gesicht erkannt"
                else:
                    x, y, w, h = faces[0]
                    face = cv2.resize(gray[y:y+h, x:x+w], (64, 64))
                    tensor = face.astype(np.float32).reshape(1, 1, 64, 64)

                    if input_info.type == "tensor(uint8)":
                        tensor = tensor.astype(np.uint8)
                    elif input_info.type == "tensor(int8)":
                        tensor = tensor.astype(np.int8)

                    output = session.run(None, {input_info.name: tensor})
                    scores = np.asarray(output[0]).flatten().astype(np.float64)
                    scores = np.exp(scores - np.max(scores))
                    scores /= np.sum(scores)
                    idx = int(np.argmax(scores))
                    if float(scores[idx]) >= EMOTION_CONFIDENCE:
                        history.append(EMOTIONS[idx])
                    if history:
                        self.latest_emotion = max(set(history), key=history.count)
                    else:
                        self.latest_emotion = "Ausdruck nicht sicher erkannt"

                time.sleep(0.08)

        except Exception as exc:
            print("Kamerafehler:", exc)
            self.latest_emotion = f"Kamera nicht verfügbar: {exc}"
        finally:
            if self._camera is not None:
                try:
                    self._camera.stop()
                except Exception:
                    pass
                self._camera = None

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
