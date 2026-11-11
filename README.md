# SchreibtischAssistent

Modularer Raspberry-Pi-Schreibtischassistent mit Tkinter-Dashboard, Wetter,
Spotify-Link, optionaler Kamera-/Emotionserkennung und Push-to-talk-Sprachassistent.

## Hinweis
Die Emotionserkennung schätzt sichtbare Gesichtsausdrücke und kann nicht zuverlässig
feststellen, wie sich eine Person tatsächlich fühlt. Die Kamera läuft nach dem
Programmstart im Hintergrund. Für Mikrofonaufnahmen muss ausdrücklich der
„Mit mir sprechen“-Button gedrückt werden.

## Installation auf Raspberry Pi OS

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-full python3-tk \
  python3-picamera2 python3-opencv python3-numpy python3-pyaudio \
  portaudio19-dev espeak-ng python3-pil
```

Im Projektordner:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Öffne `.env` und trage deinen Gemini-Schlüssel ein. Teile diese Datei niemals
und lade sie nicht zu GitHub hoch.

Lege das Modell `emotion-ferplus-12-int8.onnx` in `models/` ab.

Start:

```bash
python main.py
```

## Hinweise
- Wetterdaten kommen von Open-Meteo; Internet ist erforderlich.
- Spracherkennung nutzt den Google-Web-Spracherkennungsdienst von SpeechRecognition.
- Gemini benötigt einen gültigen API-Schlüssel und Internet.
- Falls die Kamera oder das ONNX-Modell nicht verfügbar ist, bleibt das Dashboard
  grundsätzlich bedienbar; der Fehler wird im Terminal ausgegeben.
