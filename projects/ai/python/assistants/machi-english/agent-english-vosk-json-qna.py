import queue
import sounddevice as sd
import json
import os
import tempfile
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from playsound import playsound
import openai

# === CONFIGURATION ===
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
DATA_FILE = "data.json"
SCOPE_FILE = "scope.json"
openai.api_key = os.getenv("OPENAI_API_KEY")

# === INITIALIZE MODELS ===
q = queue.Queue()
model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

# === LOAD DATA CONTEXT ===
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
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
        tts.save(fp.name)
        playsound(fp.name)

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
        "You are a helpful voice assistant. Only answer questions within these topics: "
        f"{topics_list}. If unrelated, respond with: 'I'm sorry, please ask questions about these.'."
    )

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
    reply = response['choices'][0]['message']['content'].strip()
    return reply

def main():
    while True:
        query = listen()
        if query:
            reply = ask_gpt(query)
            if "I'm sorry" in reply:
                print("Assistant: I'm sorry, please ask questions about these.")
                speak("I'm sorry, please ask questions about these.")
                print(f"Allowed topics :::::::::::: {', '.join(topic_scope)}")
            else:
                print(f"Assistant: {reply}")
                speak(reply)

if __name__ == "__main__":
    main()
