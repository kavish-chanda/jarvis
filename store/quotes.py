import threading
import tkinter as tk

META = {"id": "quotes", "name": "Daily Quotes", "version": "1.0", "author": "Kavish",
        "description": "Inspirational quotes card. Say: 'inspire me'."}


def setup(api):
    t = api.theme
    body = api.add_card("QUOTE")
    text = tk.Label(body, text="Press New quote", anchor="w", justify="left", wraplength=230,
                    fg=t["text"], bg=t["panel2"], font=("Segoe UI", 10, "italic"))
    text.pack(fill="x")

    def get():
        q = api.http_json("https://zenquotes.io/api/random")[0]
        return f"{q['q']} - {q['a']}"

    def new():
        def work():
            try:
                s = get()
            except Exception:
                s = "Couldn't reach the quote server."
            api.ui(lambda: text.config(text=s))
        threading.Thread(target=work, daemon=True).start()

    tk.Button(body, text="New quote", command=new, bg=t["panel"], fg=t["text"], bd=0, pady=4,
              activebackground=t["accent"], cursor="hand2").pack(fill="x", pady=(6, 0))
    api.add_tool("get_quote", "Get an inspirational quote", {}, lambda a: get())
    api.add_command(r"\b(inspire me|give me a quote|motivate me)\b", lambda m: get())
    new()
