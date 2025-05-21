import os
import subprocess
import librosa
import numpy as np
import joblib
import time

# Load model once (global)
MODEL_PATH = "svm_yes_no_model.joblib"
print("📦 Loading model...")
clf = joblib.load(MODEL_PATH)
print("✅ Model loaded.")

def record_audio(filename="rec.wav", duration=4, rate=16000):
    print(f"🎤 Recording for {duration} seconds...")
    command = [
        "arecord",
        "-r", str(rate),
        "-f", "S16_LE",
        "-c", "1",
        "-d", str(duration),
        filename
    ]
    subprocess.run(command)
    print(f"✅ Saved recording as '{filename}'")

def extract_mfcc(path):
    y, sr = librosa.load(path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfcc.T, axis=0)

def predict_word(audio_file):
    print(f"🔍 Predicting word from '{audio_file}'...")
    start_time = time.time()
    features = extract_mfcc(audio_file).reshape(1, -1)
    prediction = clf.predict(features)[0]
    duration = time.time() - start_time
    print(f"🗣️ Detected word: {prediction}  (⏱️ {duration:.2f}s)")
    return prediction

if __name__ == "__main__":
    output_file = "rec.wav"
    record_audio(output_file)
    predict_word(output_file)
