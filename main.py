import cv2
import numpy as np
import onnxruntime as ort
import time
import subprocess
import random

from collections import deque
from picamera2 import Picamera2


# =====================================
# SCHREIBTISCHASSISTENT
# RASPBERRY PI 5
# =====================================


# EINSTELLUNGEN

MODEL_PFAD = "models/emotion-ferplus-12-int8.onnx"

KAMERA_BREITE = 640
KAMERA_HOEHE = 480

SICHERHEIT = 0.50

WARTEZEIT = 15

VERLAUF_GROESSE = 20

MINDEST_EMOTIONEN = 12


# =====================================
# EMOTIONEN
# =====================================

EMOTIONEN = [
    "NEUTRAL",
    "GLUECKLICH",
    "UEBERRASCHT",
    "TRAURIG",
    "SAUER",
    "EKEL",
    "ANGST",
    "VERACHTUNG"
]


# =====================================
# MOTIVATIONSSPRUECHE
# =====================================

SPRUECHE = {

    "TRAURIG": [
        "Kopf hoch! Du bist staerker als du denkst!",
        "Gib nicht auf! Jeder Tag ist eine neue Chance!",
        "Du schaffst das!",
        "Auch schlechte Tage gehen vorbei!"
    ],

    "SAUER": [
        "Atme tief durch!",
        "Bleib ruhig! Du schaffst das!",
        "Lass dich nicht unterkriegen!"
    ],

    "GLUECKLICH": [
        "Super! Behalte dein Laecheln!",
        "Deine gute Laune steckt an!",
        "Schoen, dass du gut drauf bist!"
    ],

    "NEUTRAL": [
        "Schoen, dass du da bist!",
        "Willkommen zurueck!",
        "Ich bin bereit!"
    ],

    "UEBERRASCHT": [
        "Na, das war wohl eine Ueberraschung!",
        "Was gibt es Neues?"
    ],

    "EKEL": [
        "Alles gut!"
    ],

    "ANGST": [
        "Du schaffst das!",
        "Bleib ruhig! Schritt fuer Schritt!"
    ],

    "VERACHTUNG": [
        "Ein neuer Tag, eine neue Chance!"
    ]
}


# =====================================
# FARBEN
# =====================================

FARBEN = {

    "GLUECKLICH": (0, 255, 0),
    "TRAURIG": (255, 0, 0),
    "SAUER": (0, 0, 255),
    "NEUTRAL": (255, 255, 255),
    "ANGST": (255, 0, 255),
    "UEBERRASCHT": (0, 255, 255),
    "EKEL": (0, 165, 255),
    "VERACHTUNG": (255, 255, 0)

}


# =====================================
# SPRACHAUSGABE
# =====================================

sprech_prozess = None


def sprechen(text):

    global sprech_prozess

    print("ASSISTENT:", text)

    try:

        if sprech_prozess is not None:

            if sprech_prozess.poll() is None:
                return

        sprech_prozess = subprocess.Popen([
            "espeak-ng",
            "-v", "de",
            "-s", "145",
            text
        ])

    except Exception as fehler:

        print("Sprachfehler:", fehler)


# =====================================
# KAMERA STARTEN
# =====================================

def kamera_starten():

    print("Starte Kamera...")

    kamera = Picamera2()

    config = kamera.create_preview_configuration(
        main={
            "size": (KAMERA_BREITE, KAMERA_HOEHE),
            "format": "RGB888"
        }
    )

    kamera.configure(config)

    kamera.start()

    time.sleep(2)

    print("Kamera gestartet!")

    return kamera


# =====================================
# GESICHTSERKENNUNG
# =====================================

def gesicht_laden():

    gesicht = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )

    if gesicht.empty():

        raise RuntimeError(
            "Gesichtserkennung konnte nicht geladen werden!"
        )

    return gesicht


# =====================================
# KI MODELL LADEN
# =====================================

def ki_laden():

    print("Lade Emotion-KI...")

    ki = ort.InferenceSession(
        MODEL_PFAD,
        providers=["CPUExecutionProvider"]
    )

    eingabe = ki.get_inputs()[0]

    print("KI erfolgreich geladen!")
    print("Eingabe:", eingabe.name)
    print("Form:", eingabe.shape)
    print("Datentyp:", eingabe.type)

    return ki


# =====================================
# EMOTION ERKENNEN
# =====================================

def erkenne_emotion(gesicht_bild, ki):

    klein = cv2.resize(
        gesicht_bild,
        (64, 64)
    )

    bild = klein.astype(np.float32)

    bild = bild.reshape(
        1, 1, 64, 64
    )

    eingabe = ki.get_inputs()[0]

    if eingabe.type == "tensor(uint8)":

        bild = bild.astype(np.uint8)

    elif eingabe.type == "tensor(int8)":

        bild = bild.astype(np.int8)

    ergebnis = ki.run(
        None,
        {eingabe.name: bild}
    )

    werte = np.asarray(
        ergebnis[0]
    ).flatten().astype(np.float64)

    # Softmax

    werte = np.exp(
        werte - np.max(werte)
    )

    werte = werte / np.sum(werte)

    index = np.argmax(werte)

    emotion = EMOTIONEN[index]

    sicherheit = float(werte[index])

    return emotion, sicherheit


# =====================================
# HAUPTPROGRAMM
# =====================================

def main():

    kamera = None

    try:

        print("==============================")
        print(" SCHREIBTISCHASSISTENT")
        print("==============================")

        kamera = kamera_starten()

        gesicht = gesicht_laden()

        ki = ki_laden()

        verlauf = deque(
            maxlen=VERLAUF_GROESSE
        )

        letzte_emotion = ""

        letzte_ansage = 0

        print("KI ist bereit!")

        sprechen("Hallo! Ich bin dein Schreibtischassistent.")

        # =================================
        # HAUPTSCHLEIFE
        # =================================

        while True:

            bild = kamera.capture_array()

            grau = cv2.cvtColor(
                bild,
                cv2.COLOR_RGB2GRAY
            )

            gesichter = gesicht.detectMultiScale(
                grau,
                scaleFactor=1.1,
                minNeighbors=6,
                minSize=(80, 80)
            )

            erkannte_emotion = "KEIN GESICHT"

            for (x, y, w, h) in gesichter:

                gesicht_bild = grau[
                    y:y+h,
                    x:x+w
                ]

                emotion, sicherheit = erkenne_emotion(
                    gesicht_bild,
                    ki
                )

                if sicherheit >= SICHERHEIT:

                    verlauf.append(emotion)

                # =================================
                # STABILE EMOTION
                # =================================

                if len(verlauf) >= 15:

                    aktuelle_emotion = max(
                        set(verlauf),
                        key=verlauf.count
                    )

                    anzahl = verlauf.count(
                        aktuelle_emotion
                    )

                    if anzahl >= MINDEST_EMOTIONEN:

                        erkannte_emotion = aktuelle_emotion

                        if (
                            aktuelle_emotion != letzte_emotion
                            and time.time() - letzte_ansage > WARTEZEIT
                        ):

                            spruch = random.choice(
                                SPRUECHE.get(
                                    aktuelle_emotion,
                                    SPRUECHE["NEUTRAL"]
                                )
                            )

                            sprechen(spruch)

                            letzte_emotion = aktuelle_emotion

                            letzte_ansage = time.time()

                else:

                    erkannte_emotion = emotion

                # =================================
                # GESICHT MARKIEREN
                # =================================

                farbe = FARBEN.get(
                    emotion,
                    (255, 255, 255)
                )

                cv2.rectangle(
                    bild,
                    (x, y),
                    (x+w, y+h),
                    farbe,
                    2
                )

                cv2.putText(
                    bild,
                    emotion,
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    farbe,
                    2
                )

                cv2.putText(
                    bild,
                    "KI: {:.0f}%".format(
                        sicherheit * 100
                    ),
                    (x, y+h+25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    farbe,
                    2
                )

            # =================================
            # STATUS
            # =================================

            cv2.putText(
                bild,
                "SCHREIBTISCH ASSISTENT",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            cv2.putText(
                bild,
                "Emotion: " + erkannte_emotion,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            # =================================
            # BILD ANZEIGEN
            # =================================

            cv2.imshow(
                "Schreibtischassistent",
                cv2.cvtColor(
                    bild,
                    cv2.COLOR_RGB2BGR
                )
            )

            if cv2.waitKey(1) & 0xFF == 27:

                break

    except KeyboardInterrupt:

        print("Programm beendet.")

    except Exception as fehler:

        print("FEHLER:", fehler)

    finally:

        if kamera is not None:

            kamera.stop()

        cv2.destroyAllWindows()

        print("Schreibtischassistent beendet!")


if __name__ == "__main__":

    main()
