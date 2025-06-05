import speech_recognition as sr
import os
from datetime import datetime

DATA_DIR = 'training_data'
os.makedirs(DATA_DIR, exist_ok=True)

# Save audio to a WAV file
def save_wav_file(audio, filename):
    with open(filename, 'wb') as f:
        f.write(audio.get_wav_data())

# Save the transcription to a text file
def save_transcription(text, filename):
    with open(filename, 'w') as f:
        f.write(text)

def recognize_and_save():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)
        print("Listening... Speak now!")
        audio = recognizer.listen(source)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    wav_path = os.path.join(DATA_DIR, f"{timestamp}.wav")
    txt_path = os.path.join(DATA_DIR, f"{timestamp}.txt")

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        save_wav_file(audio, wav_path)
        save_transcription(text, txt_path)
        print(f"Saved audio to {wav_path} and transcription to {txt_path}")
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

if __name__ == "__main__":
    recognize_and_save()
