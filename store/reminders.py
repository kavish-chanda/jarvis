import time
import tkinter as tk

META = {"id": "reminders", "name": "Health Reminders", "version": "1.0", "author": "Kavish",
        "description": "Spoken reminders to drink water, stretch and rest your eyes. Toggle them on the card."}

ITEMS = [("water", "Drink water", 45, "Time to drink some water."),
         ("stretch", "Stretch", 60, "Stand up and stretch for a minute."),
         ("eyes", "Rest eyes", 30, "Look away from the screen for twenty seconds.")]


def setup(api):
    t = api.theme
    body = api.add_card("REMINDERS")
    due, vars_ = {}, {}

    def toggle(key, mins):
        api.set("on_" + key, vars_[key].get())
        due[key] = time.time() + mins * 60

    for key, label, mins, _msg in ITEMS:
        vars_[key] = tk.BooleanVar(value=api.get("on_" + key, False))
        due[key] = time.time() + mins * 60
        tk.Checkbutton(body, text=f"{label} (every {mins}m)", variable=vars_[key],
                       command=lambda k=key, m=mins: toggle(k, m), anchor="w", bg=t["panel2"], fg=t["text"],
                       selectcolor=t["panel"], activebackground=t["panel2"], activeforeground=t["text"], bd=0,
                       highlightthickness=0, font=("Segoe UI", 9)).pack(fill="x")

    def tick():
        now = time.time()
        for key, _label, mins, msg in ITEMS:
            if vars_[key].get() and now >= due[key]:
                due[key] = now + mins * 60
                api.speak(msg)
        api.after(15000, tick)

    tick()
