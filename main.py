# main.py

import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import threading
import time
import wave
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from playsound import playsound
import os
from pydub.utils import which
from pydub import AudioSegment

# Ensure ffmpeg is found
AudioSegment.converter = which("ffmpeg") or "./ffmpeg.exe"

LANGUAGES = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN"
}

AUDIO_FILE = "recorded.wav"
DB_FILE = "transcripts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            language TEXT,
            transcription TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(language, text):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transcripts (timestamp, language, transcription) VALUES (?, ?, ?)", 
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), language, text))
    conn.commit()
    conn.close()

def recognize_speech(selected_language):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 5

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    status_label.config(text="Recording...")

    # Start visualizer
    fig, ax = plt.subplots()
    x = np.arange(0, 2 * CHUNK, 2)
    line, = ax.plot(x, np.random.rand(CHUNK))
    ax.set_ylim(-30000, 30000)
    ax.set_xlim(0, CHUNK)
    plt.title("Live Audio Waveform")
    plt.xlabel("Samples")
    plt.ylabel("Amplitude")
    plt.pause(0.1)

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        np_data = np.frombuffer(data, dtype=np.int16)
        line.set_ydata(np_data)
        fig.canvas.draw()
        fig.canvas.flush_events()

    stream.stop_stream()
    stream.close()
    p.terminate()
    plt.close()

    wf = wave.open(AUDIO_FILE, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    recognizer = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE) as source:
        audio = recognizer.record(source)
        try:
            status_label.config(text="Recognizing...")
            text = recognizer.recognize_google(audio, language=selected_language)
            result_text.set(text)
            status_label.config(text="Done")
            save_to_db(selected_language, text)
        except sr.UnknownValueError:
            result_text.set("Could not understand audio.")
        except sr.RequestError as e:
            result_text.set(f"API error: {e}")
        except Exception as e:
            result_text.set(f"Error: {str(e)}")

def start_thread():
    selected_language = LANGUAGES[language_var.get()]
    threading.Thread(target=recognize_speech, args=(selected_language,)).start()

def play_audio():
    if os.path.exists(AUDIO_FILE):
        playsound(AUDIO_FILE)
    else:
        result_text.set("No audio found to play.")

# GUI setup
init_db()
root = tk.Tk()
root.title("🎙️ Voice to Text")
root.geometry("450x450")

result_text = tk.StringVar()
language_var = tk.StringVar(value="English")

tk.Label(root, text="Language:", font=("Helvetica", 12)).pack(pady=5)
ttk.Combobox(root, textvariable=language_var, values=list(LANGUAGES.keys()), state="readonly", width=20).pack()

tk.Button(root, text="🎤 Start Recording", command=start_thread, bg="lightblue", font=("Helvetica", 12)).pack(pady=10)
tk.Button(root, text="▶️ Play Last Audio", command=play_audio, bg="lightgreen", font=("Helvetica", 12)).pack(pady=5)

tk.Label(root, text="Transcribed Text:", font=("Helvetica", 12)).pack(pady=10)
tk.Label(root, textvariable=result_text, wraplength=400, font=("Helvetica", 11), bg="white", relief="sunken", width=50, height=5).pack(pady=10)

status_label = tk.Label(root, text="", font=("Helvetica", 10), fg="gray")
status_label.pack()

root.mainloop()