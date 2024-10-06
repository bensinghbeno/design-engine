import sys
import pyttsx3
import threading

def speak_text(text):
    engine = pyttsx3.init()
    
    # Get available voices
    voices = engine.getProperty('voices')
    
    # Set female voice
    female_voice = None
    for voice in voices:
        if "female" in voice.name.lower():
            female_voice = voice
            break
    
    if female_voice:
        engine.setProperty('voice', female_voice.id)
    else:
        print("No female voice found. Using default voice.")
    
    # Set speech rate (optional, adjust as needed)
    engine.setProperty('rate', 150)
    
    # Speak the text
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def speak_text_async(text):
    thread = threading.Thread(target=speak_text, args=(text,))
    thread.start()
    return thread

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_text = " ".join(sys.argv[1:])
        thread = speak_text_async(input_text)
        print("Speech started in background.")
        
        # Your main program can continue here
        # For example:
        print("Main program is running while speech is playing.")
        
        # If you want to wait for the speech to finish before exiting, uncomment the next line:
        # thread.join()
    else:
        print("Please provide text as a command line argument.")