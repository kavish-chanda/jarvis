"""
Jarvis - voice assistant (Windows-friendly), brain runs locally with Ollama

Setup:
    1. Install Ollama from ollama.com and let it run in the background
    2. In Command Prompt:  ollama pull llama3.2
    3. pip install SpeechRecognition pyaudio pyttsx3   (use: py -3.12 -m pip install ...)

Run:
    py -3.12 jarvis.py

Say "Jarvis" followed by your command, e.g.:
    "Jarvis open chrome"
    "Jarvis play lofi beats"
    "Jarvis search for Gorilla Tag mods"
    "Jarvis what time is it"
    "Jarvis tell me a joke"      (goes to the AI brain)
    "Jarvis goodbye"             (quits)
"""

import sys
import json
import datetime
import subprocess
import webbrowser
import urllib.parse
import urllib.request

import speech_recognition as sr
import pyttsx3

# ---------------- CONFIG ----------------
WAKE_WORD = "jarvis"
MODEL = "llama3.2"  # must match the model you pulled with: ollama pull llama3.2
OLLAMA_URL = "http://localhost:11434/api/chat"

# Add your own apps here: spoken name -> command to run
APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "chrome": "start chrome",
    "edge": "start msedge",
    "discord": "start discord:",
    "spotify": "start spotify:",
    "steam": "start steam:",
    "file explorer": "explorer",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "settings": "start ms-settings:",
    "command prompt": "start cmd",
}

SYSTEM_PROMPT = (
    "You are Jarvis, a witty, helpful voice assistant. "
    "Keep replies short (1-3 sentences) because they are spoken aloud. "
    "No markdown, no lists, no emojis."
)
# ----------------------------------------

recognizer = sr.Recognizer()
history = [{"role": "system", "content": SYSTEM_PROMPT}]


def speak(text):
    print(f"Jarvis: {text}")
    # Re-create the engine each time; avoids pyttsx3 hanging on Windows
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def listen(timeout=None, phrase_limit=8):
    """Listen on the mic and return lowercase text, or '' if nothing understood."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return ""
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        print("Speech service unavailable (check your internet).")
        return ""


def ask_brain(question):
    history.append({"role": "user", "content": question})
    payload = json.dumps({
        "model": MODEL,
        "messages": history,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        answer = data["message"]["content"].strip()
    except Exception as e:
        print(f"[Ollama error] {e}")
        print("Is Ollama running, and did you run: ollama pull " + MODEL + " ?")
        history.pop()
        return "Sorry, I couldn't reach my brain right now."
    history.append({"role": "assistant", "content": answer})
    # keep memory from growing forever (system prompt + last 10 messages)
    if len(history) > 11:
        del history[1:-10]
    return answer


def open_app(name):
    for key, cmd in APPS.items():
        if key in name:
            subprocess.Popen(cmd, shell=True)
            return f"Opening {key}."
    return None


def handle_command(cmd):
    """Return (reply, keep_running)."""
    if not cmd:
        return "Yes?", True

    if any(w in cmd for w in ("goodbye", "shut down", "exit", "quit", "stop listening")):
        return "Goodbye, Kavish.", False

    if "time" in cmd and ("what" in cmd or "tell" in cmd):
        return datetime.datetime.now().strftime("It's %I:%M %p."), True

    if "date" in cmd or "what day" in cmd:
        return datetime.datetime.now().strftime("It's %A, %B %d."), True

    if cmd.startswith("open "):
        result = open_app(cmd[5:])
        if result:
            return result, True
        # not a known app: try as a website
        site = cmd[5:].replace(" ", "")
        webbrowser.open(f"https://{site}.com")
        return f"Opening {site} dot com.", True

    if cmd.startswith("play "):
        query = urllib.parse.quote(cmd[5:])
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Searching YouTube for {cmd[5:]}.", True

    if cmd.startswith("search for ") or cmd.startswith("search "):
        q = cmd.split("search for ", 1)[-1] if cmd.startswith("search for ") else cmd[7:]
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
        return f"Searching for {q}.", True

    # Anything else goes to the AI brain
    return ask_brain(cmd), True


def main():
    speak("Jarvis online.")
    running = True
    while running:
        print("Listening for wake word...")
        heard = listen(timeout=None, phrase_limit=8)
        if not heard:
            continue
        print(f"Heard: {heard}")
        if WAKE_WORD not in heard:
            continue

        # Command said in the same breath: "jarvis open chrome"
        command = heard.split(WAKE_WORD, 1)[1].strip()
        if not command:
            speak("Yes?")
            command = listen(timeout=6, phrase_limit=10)

        reply, running = handle_command(command)
        speak(reply)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")