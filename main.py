import tkinter as tk
from modules.display.dashboard import Dashboard
from modules.voice_assistant.assistant import VoiceAssistant
from modules.camera.emotion_detection import EmotionDetection
from modules.spotify.spotify import Spotify
from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT, BACKGROUND


def main():
    root = tk.Tk()
    root.title("SchreibtischAssistent")
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.configure(bg=BACKGROUND)

    assistant = VoiceAssistant()
    camera = EmotionDetection()
    spotify = Spotify()
    app = Dashboard(root, assistant, camera, spotify)

    def close():
        camera.stop()
        assistant.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    app.start()
    root.mainloop()


if __name__ == "__main__":
    main()
