import threading
import tkinter as tk
import urllib.parse

META = {"id": "translate", "name": "Translator", "version": "1.0", "author": "Kavish",
        "description": "Translate text. Say: 'how do you say good morning in Spanish'."}

LANGS = {"spanish": "es", "french": "fr", "german": "de", "hindi": "hi", "bengali": "bn", "japanese": "ja",
         "korean": "ko", "chinese": "zh-CN", "portuguese": "pt", "italian": "it", "russian": "ru",
         "arabic": "ar", "turkish": "tr", "dutch": "nl", "english": "en"}


def setup(api):
    t = api.theme

    def translate(text, lang):
        code = LANGS.get(str(lang).lower().strip(), str(lang).strip())
        url = ("https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(text)
               + "&langpair=en|" + urllib.parse.quote(code))
        return api.http_json(url)["responseData"]["translatedText"]

    body = api.add_card("TRANSLATOR")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.pack(fill="x", ipady=4)
    lang = tk.Entry(body, bg=t["panel"], fg=t["accent"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    lang.insert(0, "Spanish")
    lang.pack(fill="x", ipady=4, pady=(4, 0))
    out = tk.Label(body, text="English to the language above", anchor="w", justify="left", wraplength=230,
                   fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9))
    out.pack(fill="x", pady=(6, 0))

    def go(_e=None):
        def work():
            try:
                s = translate(entry.get(), lang.get())
            except Exception:
                s = "Couldn't translate that."
            api.ui(lambda: out.config(text=s, fg=t["text"]))
        threading.Thread(target=work, daemon=True).start()

    entry.bind("<Return>", go)
    api.add_tool("translate_text", "Translate English text into another language",
                 {"text": ("string", "the English text"), "language": ("string", "target language, e.g. Spanish")},
                 lambda a: translate(a["text"], a["language"]))
    api.add_command(r"how do you say (.+?) in (\w+)", lambda m: translate(m.group(1), m.group(2)))
