import queue
import sounddevice as sd
import json
import os
import tempfile
import requests
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from playsound import playsound
import openai
from tkinter import Tk, Label
from PIL import Image, ImageTk

# === CONFIGURATION ===
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
DATA_FILE = "data.json"
SCOPE_FILE = "scope.json"
GIF_PATH = "res/question.gif"
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

# === IMAGE DISPLAY WINDOW ===
root = Tk()
root.title("Search Result")
label = Label(root)
label.pack()

def display_image(image_path):
    img = Image.open(image_path)
    img = img.resize((400, 400), Image.Resampling.LANCZOS)  # Use LANCZOS instead of ANTIALIAS
    img_tk = ImageTk.PhotoImage(img)
    label.config(image=img_tk)
    label.image = img_tk
    root.update()  # Ensure GUI refresh


# Start with the loading GIF
display_image(GIF_PATH)

def search_and_display_image(query):
    try:
        # Replace with a real image search API
        search_url = f"https://api.unsplash.com/photos/random?query={query}&client_id=AequTRHmxFgl1JjuIZo8rhOmByLoFAoQCh85DawCGT8"
        response = requests.get(search_url)
        response.raise_for_status()
        image_url = response.json()["urls"]["regular"]

        # Download the image
        image_response = requests.get(image_url, stream=True)
        image_response.raise_for_status()
        temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
        with open(temp_image_path, "wb") as f:
            f.write(image_response.content)

        # Display the downloaded image
        display_image(temp_image_path)
    except Exception as e:
        print("Error fetching image:", e)

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
    print(f"Assistant: Please ask questions about these topics:")
    print(f"Allowed topics: {topics_list}")

    topic_keywords = {
        "Animals": ["cat", "dog", "lion", "tiger", "elephant"],
        "Countries": ["India", "USA", "France", "Germany", "Japan"],
        "Superheroes": ["Superman", "Batman", "Spiderman", "Ironman", "Hulk"],
        "Cities": ["New York", "Paris", "Tokyo", "London", "Mumbai"],
        "Fruits": ["apple", "banana", "mango", "orange", "grape"]
    }

    for topic, keywords in topic_keywords.items():
        for keyword in keywords:
            if keyword.lower() in question.lower():
                print(f"Searching for an image related to: {keyword}")
                search_and_display_image(keyword)  # Use the specific keyword
                return f"Here is an image of a {keyword}."

    return "I'm sorry, please ask questions about these."

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
    root.after(100, main)  # Run the main loop alongside the Tkinter window
    root.mainloop()
