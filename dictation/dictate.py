#!/usr/bin/env python3
"""Push-to-talk-Diktat für macOS.

Taste gedrückt halten, sprechen, loslassen. Die Aufnahme wird lokal mit
faster-whisper in Text umgewandelt und an der Cursorposition eingefügt.
"""
import argparse
import subprocess
import sys
import threading
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from pynput import keyboard

SAMPLE_RATE = 16000
MIN_SECONDS = 0.25


def parse_args():
    parser = argparse.ArgumentParser(description="Diktieren mit einer Taste (macOS)")
    parser.add_argument("--key", default="f5", help="Taste zum Halten, z. B. f5, f6, alt_r")
    parser.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3")
    parser.add_argument("--language", default="de", help="Sprachcode, z. B. de oder en")
    return parser.parse_args()


def resolve_key(name):
    try:
        return getattr(keyboard.Key, name)
    except AttributeError:
        sys.exit(f"Unbekannte Taste: {name}")


class Recorder:
    def __init__(self):
        self.frames = []
        self.stream = None

    def start(self):
        self.frames = []
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self.stream.start()

    def _callback(self, indata, frames, time_info, status):
        self.frames.append(indata[:, 0].copy())

    def stop(self):
        self.stream.stop()
        self.stream.close()
        if not self.frames:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self.frames)


def transcribe(model, audio, language):
    if audio.size < SAMPLE_RATE * MIN_SECONDS:
        return ""
    segments, _ = model.transcribe(audio, language=language, vad_filter=True, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments).strip()


def paste(text):
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    time.sleep(0.05)
    controller = keyboard.Controller()
    controller.press(keyboard.Key.cmd)
    controller.press("v")
    controller.release("v")
    controller.release(keyboard.Key.cmd)


def main():
    args = parse_args()
    key = resolve_key(args.key)

    print(f"Lade Modell '{args.model}' ...")
    model = WhisperModel(args.model, device="auto", compute_type="int8")

    recorder = Recorder()
    recording = False

    def process(audio):
        text = transcribe(model, audio, args.language)
        if text:
            paste(text)
            print(f"→ {text}")
        else:
            print("(nichts erkannt)")

    def on_press(pressed):
        nonlocal recording
        if pressed == key and not recording:
            recording = True
            recorder.start()
            print("● Aufnahme läuft ...")

    def on_release(released):
        nonlocal recording
        if released == key and recording:
            recording = False
            audio = recorder.stop()
            threading.Thread(target=process, args=(audio,), daemon=True).start()

    print(f"Bereit. Taste {args.key} gedrückt halten zum Sprechen. Strg+C beendet.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBeendet.")
