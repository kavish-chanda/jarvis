import random
import threading
import tkinter as tk

META = {"id": "fun", "name": "Fun Pack", "version": "1.0", "author": "Kavish",
        "description": "Random fun facts, coin flips and dice. Say: 'flip a coin' or 'roll a dice'."}


def setup(api):
    t = api.theme
    body = api.add_card("FUN FACT")
    fact = tk.Label(body, text="Press the button", anchor="w", justify="left", wraplength=230,
                    fg=t["text"], bg=t["panel2"], font=("Segoe UI", 9))
    fact.pack(fill="x")

    def get_fact():
        return api.http_json("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en")["text"]

    def new():
        def work():
            try:
                text = get_fact()
            except Exception:
                text = "Couldn't reach the fact server."
            api.ui(lambda: fact.config(text=text))
        threading.Thread(target=work, daemon=True).start()

    tk.Button(body, text="New fact", command=new, bg=t["panel"], fg=t["text"], bd=0, pady=4,
              activebackground=t["accent"], cursor="hand2").pack(fill="x", pady=(6, 0))

    api.add_tool("fun_fact", "Tell the user a random fun fact", {}, lambda a: get_fact())
    api.add_command(r"\b(flip|toss) a coin\b", lambda m: "It's " + random.choice(["heads", "tails"]) + ".")
    api.add_command(r"\broll (?:a |an )?(?:d|die|dice)\s*(\d*)",
                    lambda m: f"You rolled a {random.randint(1, int(m.group(1) or 6))}.")
