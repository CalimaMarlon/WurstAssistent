import queue
import tkinter as tk
from datetime import datetime
from modules.display.weather import get_weather
from config.settings import (
    BACKGROUND, FOREGROUND, ACCENT, WEATHER_REFRESH_MS
)


class Dashboard:
    def __init__(self, root, assistant, camera, spotify):
        self.root = root
        self.assistant = assistant
        self.camera = camera
        self.spotify = spotify
        self.events = queue.Queue()

        title = tk.Label(root, text="SCHREIBTISCHASSISTENT",
                         font=("Arial", 22, "bold"),
                         fg=FOREGROUND, bg=BACKGROUND)
        title.pack(pady=(12, 4))

        self.clock = tk.Label(root, font=("Arial", 15),
                              fg=FOREGROUND, bg=BACKGROUND)
        self.clock.pack()

        self.weather = tk.Label(root, text="Wetter wird geladen...",
                                font=("Arial", 14), fg=ACCENT,
                                bg=BACKGROUND, justify="center")
        self.weather.pack(pady=10)

        self.emotion = tk.Label(root, text="Kamera: noch nicht gestartet",
                                font=("Arial", 12), fg=FOREGROUND,
                                bg=BACKGROUND)
        self.emotion.pack(pady=5)

        buttons = tk.Frame(root, bg=BACKGROUND)
        buttons.pack(pady=8)

        tk.Button(buttons, text="🎤 Mit mir sprechen",
                  font=("Arial", 15, "bold"),
                  command=self.on_talk).pack(side="left", padx=6)

        tk.Button(buttons, text="Spotify öffnen",
                  font=("Arial", 13), bg="#1DB954", fg="white",
                  command=self.spotify.open).pack(side="left", padx=6)

        tk.Button(buttons, text="Wetter aktualisieren",
                  font=("Arial", 12),
                  command=self.refresh_weather).pack(side="left", padx=6)

        self.status = tk.Label(root, text="Bereit",
                               font=("Arial", 11), fg=FOREGROUND,
                               bg=BACKGROUND)
        self.status.pack(pady=6)

    def start(self):
        self.update_clock()
        self.refresh_weather()
        self.camera.start()
        self.root.after(200, self.poll_events)

    def update_clock(self):
        self.clock.config(text=datetime.now().strftime("%d.%m.%Y   %H:%M:%S"))
        self.root.after(1000, self.update_clock)

    def refresh_weather(self):
        self.weather.config(text="Wetter wird geladen...")
        # Netzwerkanfrage nicht im Tkinter-Hauptthread ausführen.
        import threading
        def worker():
            result = get_weather()
            self.events.put(("weather", result))
        threading.Thread(target=worker, daemon=True).start()
        self.root.after(WEATHER_REFRESH_MS, self.refresh_weather)

    def on_talk(self):
        self.status.config(text="Mikrofon wird aktiviert – bitte sprechen...")
        self.assistant.listen_once(
            callback=lambda message: self.events.put(("assistant", message))
        )

    def poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "weather":
                    self.weather.config(text=value)
                elif kind == "assistant":
                    self.status.config(text=value)
        except queue.Empty:
            pass

        emotion = self.camera.latest_emotion
        if emotion:
            self.emotion.config(text=f"Kamera: {emotion}")
        self.root.after(200, self.poll_events)
