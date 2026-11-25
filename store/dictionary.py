import threading
import tkinter as tk

META = {"id": "dictionary", "name": "Dictionary", "version": "1.0", "author": "Kavish",
        "description": "Look up word definitions. Say: 'define serendipity'."}


def setup(api):
    t = api.theme

    def define(word):
        d = api.http_json("https://api.dictionaryapi.dev/api/v2/entries/en/" + word.strip().lower())
        m = d[0]["meanings"][0]
        return f"{word} ({m['partOfSpeech']}): {m['definitions'][0]['definition']}"

    body = api.add_card("DICTIONARY")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.pack(fill="x", ipady=4)
    out = tk.Label(body, text="Type a word, press Enter", anchor="w", justify="left", wraplength=230,
                   fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9))
    out.pack(fill="x", pady=(6, 0))

    def go(_e=None):
        word = entry.get().strip()
        if not word:
            return

        def work():
            try:
                text = define(word)
            except Exception:
                text = "No definition found."
            api.ui(lambda: out.config(text=text, fg=t["text"]))
        threading.Thread(target=work, daemon=True).start()

    entry.bind("<Return>", go)
    api.add_tool("define_word", "Get the dictionary definition of an English word",
                 {"word": ("string", "the word")}, lambda a: define(str(a.get("word", ""))))
    api.add_command(r"\bdefine (\w+)", lambda m: define(m.group(1)))
