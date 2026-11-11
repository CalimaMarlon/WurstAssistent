import cv2
import numpy as np
import time
import subprocess
import random

from collections import deque
from picamera2 import Picamera2


# ==========================================
# SCHREIBTISCHASSISTENT - RASPBERRY PI 5
# ==========================================


# ==========================================
# EINSTELLUNGEN
# ==========================================

KAMERA_BREITE = 640
KAMERA_HOEHE = 480

ERKENNUNGS_SICHERHEIT = 0.50

WARTEZEIT = 15

VERLAUF_GROESSE = 20

MINDEST_EMOTIONEN = 12

KI_AKTIV = True
SPRACHE_AKTIV = True


# ==========================================
# EMOTIONEN
# ==========================================

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


# ==========================================
# MOTIVATIONSSPRUECHE
# ==========================================

SPRUECHE = {

    "TRAURIG": [
        "Kopf hoch! Du bist staerker als du denkst!",
        "Gib nicht auf! Jeder neue Tag ist eine Chance!",
        "Du schaffst das! Glaub an dich!",
        "Auch schlechte Tage gehen vorbei!"
    ],

    "SAUER": [
        "Atme tief durch! Du hast alles im Griff!",
        "Bleib ruhig! Du kannst alles schaffen!",
        "Lass dich nicht unterkriegen!"
    ],

    "GLUECKLICH": [
        "Super! Behalte dein Laecheln!",
        "Deine gute Laune steckt an!",
        "Schoen, dass du so gut drauf bist!"
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
        "Alles gut! Atme einmal tief durch!"
    ],

    "ANGST": [
        "Du schaffst das! Schritt fuer Schritt!",
        "Bleib ruhig, du bist nicht allein!"
    ],

    "VERACHTUNG": [
        "Ein neuer Tag, eine neue Chance!"
    ]
}


# ==========================================
# FARBEN
# ==========================================

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


# ==========================================
# SPRACHAUSGABE
# ==========================================

def sprechen(text):

    if not SPRACHE_AKTIV:
        return

    print("ASSISTENT:", text)

    try:

        subprocess.Popen([
            "espeak-ng",
            "-v", "de",
            "-s", "145",
            text
        ])

    except Exception as fehler:

        print("Sprachfehler:", fehler)


# ==========================================
# KAMERA STARTEN
# ==========================================

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


# ==========================================
# GESICHTSERKENNUNG LADEN
# ==========================================

def gesichtserkennung_laden():

    print("Lade Gesichtserkennung...")

    gesicht = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )

    if gesicht.empty():

        raise RuntimeError(
            "Gesichtserkennung konnte nicht geladen werden!"
        )

    print("Gesichtserkennung geladen!")

    return gesicht


# ==========================================
# KI MODELL LADEN
# ==========================================

def ki_laden():

    print("Lade KI-Modell...")

    ki = cv2.dnn.readNetFromONNX(
        "models/emotion-ferplus-8.onnx"
    )

    print("KI-Modell geladen!")

    return ki


# ==========================================
# EMOTION ERKENNEN
# ==========================================

def erkenne_emotion(gesicht_bild, ki):

    klein = cv2.resize(
        gesicht_bild,
        (64, 64)
    )

    blob = klein.astype(np.float32)

    blob = blob.reshape(
        1, 1, 64, 64
    )

    ki.setInput(blob)

    ergebnis = ki.forward()

    werte = ergebnis.flatten()

    # Softmax

    werte = np.exp(
        werte - np.max(werte)
    )

    werte = werte / np.sum(werte)

    index = np.argmax(werte)

    emotion = EMOTIONEN[index]

    sicherheit = float(werte[index])

    return emotion, sicherheit


# ==========================================
# HAUPTPROGRAMM
# ==========================================

def main():

    print()
    print("================================")
    print(" SCHREIBTISCHASSISTENT")
    print(" RASPBERRY PI 5")
    print("================================")
    print()

    kamera = None

    try:

        # Kamera starten

        kamera = kamera_starten()

        # Gesichtserkennung laden

        gesicht = gesichtserkennung_laden()

        # KI laden

        ki = ki_laden()

        # Verlauf speichern

        verlauf = deque(
            maxlen=VERLAUF_GROESSE
        )

        letzte_ansage = 0

        letzte_emotion = ""

        print()
        print("KI MOTIVATIONSASSISTENT GESTARTET!")
        print("Druecke ESC zum Beenden.")
        print()

        # ==================================
        # HAUPTSCHLEIFE
        # ==================================

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

                emotion = "NEUTRAL"

                sicherheit = 0

                if KI_AKTIV:

                    emotion, sicherheit = erkenne_emotion(
                        gesicht_bild,
                        ki
                    )

                # Emotion speichern

                if sicherheit >= ERKENNUNGS_SICHERHEIT:

                    verlauf.append(emotion)

                # ==================================
                # STABILE EMOTION ERMITTELN
                # ==================================

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

                            letzte_ansage = time.time()

                            letzte_emotion = aktuelle_emotion

                else:

                    erkannte_emotion = emotion

                # ==================================
                # GESICHT MARKIEREN
                # ==================================

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

            # ==================================
            # STATUS ANZEIGEN
            # ==================================

            cv2.putText(
                bild,
                "SCHREIBTISCHASSISTENT",
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

            # ==================================
            # BILD ANZEIGEN
            # ==================================

            cv2.imshow(
                "Mein KI Motivationsassistent",
                cv2.cvtColor(
                    bild,
                    cv2.COLOR_RGB2BGR
                )
            )

            # ESC beendet das Programm

            if cv2.waitKey(1) & 0xFF == 27:

                break

    except KeyboardInterrupt:

        print("Programm wird beendet...")

    except Exception as fehler:

        print("FEHLER:", fehler)

    finally:

        if kamera is not None:

            kamera.stop()

        cv2.destroyAllWindows()

        print("Schreibtischassistent beendet!")


# ==========================================
# PROGRAMM STARTEN
# ==========================================

if __name__ == "__main__":

    main()
