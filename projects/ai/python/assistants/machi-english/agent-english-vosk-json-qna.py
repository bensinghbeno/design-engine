import queue
import sounddevice as sd
import json
import pyttsx3
from vosk import Model, KaldiRecognizer
import openai
import os

# === CONFIGURATION ===
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
DATA_FILE = "data.json"  # additional context if needed
SCOPE_FILE = "scope.json"  # contains allowed topics
openai.api_key = os.getenv("OPENAI_API_KEY")

# === INITIALIZE MODELS ===
q = queue.Queue()
model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, 16000)
tts = pyttsx3.init()

# === LOAD DATA CONTEXT (Optional) ===
try:
    with open(DATA_FILE, "r") as f:
        extra_data = json.load(f)
except Exception as e:
    print("Error loading data.json:", e)
    extra_data = {}

# === LOAD TOPIC SCOPE ===
try:
    with open(SCOPE_FILE, "r") as f:
        topic_scope = json.load(f).get("topics", [])
except Exception as e:
    print("Error loading scope.json:", e)
    topic_scope = []

def speak(text):
    print(f"Assistant: {text}")
    voices = tts.getProperty('voices')
    tts.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
    tts.setProperty('rate', 200)
    tts.setProperty('volume', 0.9)
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

    topics_list = ", ".join(topic_scope)
    system_prompt = (
        "You are a helpful voice assistant. Only answer questions that fall within the following topics: "
        f"{topics_list}. If the question is unrelated to these topics, politely respond that you're limited to these subjects."
    )

    # Optionally include extra data (like vehicle info, etc.)
    context = "\n".join([f"{k}: {v}" for k, v in extra_data.items()])

    messages = [
        {"role": "system", "content": system_prompt + "\n\n" + context},
        {"role": "user", "content": question}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
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
