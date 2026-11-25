import secrets
import string
import tkinter as tk

META = {"id": "password", "name": "Password Maker", "version": "1.0", "author": "Kavish",
        "description": "Makes a strong password and copies it to your clipboard. It is never read out loud."}


def setup(api):
    t = api.theme
    body = api.add_card("PASSWORD")
    length = tk.IntVar(value=16)
    row = tk.Frame(body, bg=t["panel2"])
    row.pack(fill="x")
    tk.Label(row, text="Length", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9)).pack(side="left")
    tk.Spinbox(row, from_=8, to=64, textvariable=length, width=4, bg=t["panel"], fg=t["text"], bd=0).pack(side="left", padx=6)
    out = tk.Label(body, text="Nothing generated yet", anchor="w", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9))

    def make(n):
        n = max(8, min(64, int(n)))
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
        pw = "".join(secrets.choice(alphabet) for _ in range(n))
        api.root.clipboard_clear()
        api.root.clipboard_append(pw)
        return n

    def click():
        n = make(length.get())
        out.config(text=f"Copied a {n}-character password", fg=t["accent"])

    tk.Button(body, text="Generate & copy", command=click, bg=t["panel"], fg=t["text"], bd=0, pady=4,
              activebackground=t["accent"], cursor="hand2").pack(fill="x", pady=(6, 0))
    out.pack(fill="x", pady=(4, 0))

    def tool(a):
        box = {}
        api.ui(lambda: box.update(n=make(a.get("length", 16))))
        return "A new password was copied to the clipboard. Do not read it out."

    api.add_tool("generate_password", "Make a strong password and copy it to the clipboard",
                 {"length": ("number", "characters, 8 to 64")}, tool)
