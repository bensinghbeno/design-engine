import sys
import os
import queue
import sounddevice as sd
import vosk
import json

# Set model path
MODEL_PATH = "/home/ben/Documents/dev/design-engine/projects/ai/asr/vosk/models/vosk-model-small-en-us-0.15"

# Ensure model is downloaded
if not os.path.exists(MODEL_PATH):
    print("Please download a Vosk model and place it in the 'model' directory.")
    sys.exit(1)

# Load Vosk model
model = vosk.Model(MODEL_PATH)

audio_queue = queue.Queue()

# Callback function to capture audio
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

# Set up the audio stream
with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                       channels=1, callback=callback):
    recognizer = vosk.KaldiRecognizer(model, 16000)
    print("Listening...")

    while True:
        data = audio_queue.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if "text" in result and result["text"]:
                print("You said:", result["text"])
        else:
            partial_result = json.loads(recognizer.PartialResult())
            print("Partial:", partial_result.get("partial", ""))

