import re
import threading
import tkinter as tk

META = {"id": "converter", "name": "Currency Converter", "version": "1.0", "author": "Kavish",
        "description": "Convert money. Say: 'convert 100 USD to EUR'. Uses live rates."}


def setup(api):
    t = api.theme

    def convert(amount, frm, to):
        frm, to = frm.upper(), to.upper()
        rate = api.http_json(f"https://open.er-api.com/v6/latest/{frm}")["rates"][to]
        return f"{amount:g} {frm} is {amount * rate:,.2f} {to}."

    body = api.add_card("CONVERTER")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.insert(0, "100 USD to EUR")
    entry.pack(fill="x", ipady=4)
    out = tk.Label(body, text="", anchor="w", justify="left", wraplength=230, fg=t["accent"], bg=t["panel2"],
                   font=("Segoe UI", 10))
    out.pack(fill="x", pady=(6, 0))

    def go(_e=None):
        m = re.match(r"\s*([\d.]+)\s*(\w{3})\s*(?:to|in|into)?\s*(\w{3})", entry.get())
        if not m:
            out.config(text="Try: 100 USD to EUR")
            return

        def work():
            try:
                text = convert(float(m.group(1)), m.group(2), m.group(3))
            except Exception:
                text = "Couldn't convert that."
            api.ui(lambda: out.config(text=text))
        threading.Thread(target=work, daemon=True).start()

    entry.bind("<Return>", go)
    api.add_tool("convert_currency", "Convert money between currencies using live rates",
                 {"amount": ("number", "amount"), "from_currency": ("string", "3-letter code like USD"),
                  "to_currency": ("string", "3-letter code like EUR")},
                 lambda a: convert(float(a["amount"]), a["from_currency"], a["to_currency"]))
    api.add_command(r"convert ([\d.]+) (\w{3}) (?:to|into) (\w{3})",
                    lambda m: convert(float(m.group(1)), m.group(2), m.group(3)))
