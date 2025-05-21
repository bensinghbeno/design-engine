import queue
import sounddevice as sd
import json
import pyttsx3
from vosk import Model, KaldiRecognizer
import openai

# === CONFIGURATION ===
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
DATA_FILE = "data.json"  # vehicle data file
openai.api_key = "REDACTED"  


# === INITIALIZE MODELS ===
q = queue.Queue()
model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, 16000)
tts = pyttsx3.init()

# === LOAD DATA CONTEXT ===
try:
    with open(DATA_FILE, "r") as f:
        vehicle_data = json.load(f)
except Exception as e:
    print("Error loading JSON data:", e)
    vehicle_data = {}

def speak(text):
    print(f"Assistant: {text}")
    tts.say(text)
    tts.runAndWait()

def callback(indata, frames, time, status):
    if status:
        print("Error:", status)
    q.put(bytes(indata))

def listen():
    print("🎙️ Say something...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                return result.get("text", "")

def ask_gpt(question):
    print(f"You said: {question}")
    
    system_prompt = (
        "You are a helpful voice assistant that can answer questions using the following vehicle data. "
        "If the user question matches any of these keys or sounds related, answer directly using the value. "
        "Otherwise, try to answer normally."
    )
    
    # Format the JSON key-values into readable lines
    context = "\n".join([f"{k}: {v}" for k, v in vehicle_data.items()])
    
    messages = [
        {"role": "system", "content": system_prompt + "\n\nVehicle Data:\n" + context},
        {"role": "user", "content": question}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # or "gpt-3.5-turbo", etc.
        messages=messages,
        temperature=0.3
    )
    return response['choices'][0]['message']['content'].strip()

def main():
    while True:
        query = listen()
        if query:
            answer = ask_gpt(query)
            speak(answer)

if __name__ == "__main__":
    main()

