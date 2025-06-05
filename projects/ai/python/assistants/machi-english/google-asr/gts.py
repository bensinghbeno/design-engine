import speech_recognition as sr
import os
from datetime import datetime
import time
import collections

DATA_DIR = 'training_data'
os.makedirs(DATA_DIR, exist_ok=True)

WAKE_WORDS = ["hey machi", "hello machi", "machi"]

# Save audio to a WAV file
def save_wav_file(audio, filename):
    with open(filename, 'wb') as f:
        f.write(audio.get_wav_data())

# Save the transcription to a text file
def save_transcription(text, filename):
    with open(filename, 'w') as f:
        f.write(text)

# Listen and buffer audio in real-time to detect wake word and record follow-up
def recognize_and_save():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)

    print("Listening continuously for wake word...")
    buffer = collections.deque(maxlen=10)  # 10 recent phrases
    wake_detected = False
    wake_word_text = ""

    while not wake_detected:
        with mic as source:
            audio = recognizer.listen(source, phrase_time_limit=5)  # increased duration

        try:
            text = recognizer.recognize_google(audio).lower()
            print("Heard:", text)
            for wake in WAKE_WORDS:
                if wake in text:
                    print("Wake word detected!")
                    wake_word_text = wake
                    wake_detected = True
                    break
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"Google API error: {e}")
            continue

    # After wake word is detected, capture longer command input
    print("Listening for command after wake word...")
    with mic as source:
        audio_followup = recognizer.listen(source, phrase_time_limit=6)

    all_audio = sr.AudioData(
        audio_followup.get_raw_data(),
        audio_followup.sample_rate,
        audio_followup.sample_width
    )

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    wav_path = os.path.join(DATA_DIR, f"{timestamp}.wav")
    txt_path = os.path.join(DATA_DIR, f"{timestamp}.txt")

    try:
        print("Recognizing full input...")
        full_text = recognizer.recognize_google(all_audio)
        print("You said:", full_text)
        save_wav_file(all_audio, wav_path)
        save_transcription(full_text, txt_path)
        print(f"Saved audio to {wav_path} and transcription to {txt_path}")
    except sr.UnknownValueError:
        print("Could not understand full input")
    except sr.RequestError as e:
        print(f"Google API error: {e}")

if __name__ == "__main__":
    recognize_and_save()
