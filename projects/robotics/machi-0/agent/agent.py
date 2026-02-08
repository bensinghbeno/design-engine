import os
import json
import requests
import speech_recognition as sr
from openai import OpenAI
import subprocess

# --- CONFIGURATION ---
CONTEXT_FILE = 'context.json'
with open(CONTEXT_FILE, 'r') as f:
    context_data = json.load(f)

# Initialize Ollama client
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

def trigger_looi(emotion):
    try:
        requests.get(f"http://localhost:5000/emotion/{emotion}")
    except:
        pass

def speak(text):
    trigger_looi("talking")
    
    # Use the EXACT name from your ls output
    model_name = "en-us-lessac-medium.onnx"
    
    # Building the command with the correct filename
    command = f'echo "{text}" | piper --model ./{model_name} --output_raw | play -t raw -r 22050 -e signed-integer -b 16 -c 1 -'
    
    import subprocess
    subprocess.run(command, shell=True)
    
    trigger_looi("default")

def talk_to_agent(user_input):
    system_prompt = f"""
    You are {context_data['name']}. Context: {json.dumps(context_data)}.
    Keep responses concise (1-2 sentences). 
    If you are happy/smiling, start with [HAPPY].
    If you are angry, start with [ANGRY].
    """
    
    response = client.chat.completions.create(
        model="llama3",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_input}]
    )
    
    answer = response.choices[0].message.content
    
    # Parse emotion and clean text
    if "[HAPPY]" in answer:
        trigger_looi("happy")
        answer = answer.replace("[HAPPY]", "")
    elif "[ANGRY]" in answer:
        trigger_looi("angry")
        answer = answer.replace("[ANGRY]", "")

    print(f"Looi: {answer}")
    speak(answer)

# --- MAIN LOOP ---
r = sr.Recognizer()
with sr.Microphone() as source:
    # Adjust for ambient noise
    r.adjust_for_ambient_noise(source)
    print("Looi is listening (Speak now)...")
    while True:
        try:
            audio = r.listen(source)
            text = r.recognize_google(audio)
            print(f"Ben: {text}")
            talk_to_agent(text)
        except Exception as e:
            continue