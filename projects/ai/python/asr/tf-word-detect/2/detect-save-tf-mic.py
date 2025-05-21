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
    
    # Get prediction and confidence score
    prediction = clf.predict(features)[0]
    if hasattr(clf, "predict_proba"):  # Check if the classifier supports predict_proba
        probabilities = clf.predict_proba(features)[0]
        confidence = max(probabilities)
    else:
        confidence = "N/A"  # Confidence not available for this classifier
    
    duration = time.time() - start_time
    print(f"========================================= DETECTED WORD     : {prediction}")
    print(f"========================================= CONFIDENCE SCORE  : {confidence}")
    return prediction, confidence

if __name__ == "__main__":
    output_file = "rec.wav"
    record_audio(output_file)
    predict_word(output_file)
