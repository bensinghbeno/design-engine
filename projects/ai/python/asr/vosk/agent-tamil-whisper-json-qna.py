import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import openai
from gtts import gTTS
from playsound import playsound
import tempfile
import os


openai.api_key = "REDACTED"  

# Load Whisper model
model = whisper.load_model("base")

def record_audio(duration=5, samplerate=16000):
    print("🎙️ Recording started...")
    audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()
    print("✅ Recording complete.")
    return audio, samplerate

def save_wav(audio, samplerate):
    audio = np.int16((audio / np.max(np.abs(audio))) * 32767)  # Normalize
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, samplerate, audio)
        return f.name

def transcribe_tamil(audio_path):
    print("🧠 Transcribing with Whisper...")
    result = model.transcribe(audio_path, language="ta")
    print("📜 Transcribed Text:", result["text"])
    return result["text"]

def ask_openai(prompt):
    print("🤖 Querying OpenAI...")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "நீ தமிழ் மொழியில் பதிலளிக்க வேண்டிய ஒரு உதவியாளர்."},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message['content'].strip()
    print("🤖 பதில்:", answer)
    return answer

def speak_tamil(text):
    print("🔊 பேசுகிறது...")
    tts = gTTS(text=text, lang='ta')
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tts.save(f.name)
        playsound(f.name)
        os.remove(f.name)

def main():
    try:
        audio, sr = record_audio()
        audio_path = save_wav(audio, sr)
        question = transcribe_tamil(audio_path)

        if question.strip():
            answer = ask_openai(question)
            speak_tamil(answer)
        else:
            print("⚠️ உரை அடையாளம் காண முடியவில்லை.")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == "__main__":
    main()

