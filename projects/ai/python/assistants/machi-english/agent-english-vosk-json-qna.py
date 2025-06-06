import queue
import json
import os
import tempfile
import requests
from gtts import gTTS
from playsound import playsound
import openai
from tkinter import Tk, Label
from PIL import Image, ImageTk
import sys
import speech_recognition as sr
from bs4 import BeautifulSoup

# === CONFIGURATION ===
DATA_FILE = "data.json"
SCOPE_FILE = "scope.json"
GIF_PATH = "res/question.gif"
openai.api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"  # Replace with your Google API key
GOOGLE_CSE_ID = "YOUR_GOOGLE_CSE_ID"  # Replace with your Custom Search Engine ID

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
    img = img.resize((400, 400), Image.Resampling.LANCZOS)  # Use LANCZOS for resizing
    img_tk = ImageTk.PhotoImage(img)
    label.config(image=img_tk)
    label.image = img_tk
    root.update()  # Ensure GUI refresh

# Start with the loading GIF
display_image(GIF_PATH)

from bs4 import BeautifulSoup

def search_and_display_image(query):
    GOOGLE_API_KEY = "AIzaSyCHkMwQIwPo5ARcwxVl2-8xYPOT5k5rhgM"
    GOOGLE_CSE_ID = "f353698d81ef5475f"

    def google_image_search(query):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "searchType": "image",
            "num": 1,
        }

        try:
            print(f"Searching for: {query}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            image_url = data["items"][0]["link"]
            print(f"Found image: {image_url}")
            return image_url
        except Exception as e:
            print(f"Error: {e}")
            return None

    def download_and_show_image(image_url):
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                f.write(response.content)
                img = Image.open(f.name)
                img.show()
        except Exception as e:
            print(f"Image load error: {e}")

    image_url = google_image_search(query)
    if image_url:
        download_and_show_image(image_url)

def speak(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
        tts.save(fp.name)
        playsound(fp.name)

def listen():
    print("🎙️ Say something...")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            if text.lower() == "quit":  # Check for the "quit" command
                quit_application()  # Call the quit function
            return text
        except sr.UnknownValueError:
            print("Google ASR could not understand the audio.")
        except sr.RequestError as e:
            print(f"Google ASR request error: {e}")

def ask_gpt(question):
    print(f"You said: {question}")

    # Build system prompt to instruct GPT to extract the keyword
    system_prompt = (
        "You're an assistant that extracts the key subject from a spoken request "
        "to search for an image. Return ONLY the subject as a short phrase, without any explanation. "
        "Examples:\n"
        "- 'show me actor tom cruise' → 'tom cruise'\n"
        "- 'can you show me a banana' → 'banana'\n"
        "- 'I want to see the Eiffel Tower' → 'Eiffel Tower'\n"
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # free tier model and widely accessible
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0
        )
        keyword = completion.choices[0].message['content'].strip()
        print(f"Extracted keyword: {keyword}")

        search_and_display_image(keyword)
        return f"Here is an image of {keyword}."
    except Exception as e:
        print("Error calling GPT:", e)
        return "Sorry, I couldn't understand your request."

def quit_application(event=None):
    """Close the application gracefully."""
    print("Exiting application...")
    root.destroy()  # Close the Tkinter window
    sys.exit(0)  # Exit the program

def main():
    root.bind('<q>', quit_application)  # Bind the 'q' key to quit the application
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
