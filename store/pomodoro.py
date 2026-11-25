import time
import tkinter as tk

META = {"id": "pomodoro", "name": "Focus Timer", "version": "1.0", "author": "Kavish",
        "description": "Pomodoro focus timer card. Say: 'start a 25 minute focus session'."}


def setup(api):
    t = api.theme
    body = api.add_card("FOCUS TIMER")
    label = tk.Label(body, text="25:00", font=("Consolas", 26, "bold"), fg=t["accent"], bg=t["panel2"])
    label.pack(anchor="w")
    st = {"end": None, "mins": 25}

    def tick():
        if st["end"]:
            left = int(st["end"] - time.time())
            if left <= 0:
                st["end"] = None
                label.config(text="DONE")
                api.speak("Focus session complete. Take a break.")
            else:
                label.config(text=f"{left // 60:02d}:{left % 60:02d}")
        api.after(500, tick)

    def start(mins=25):
        st["mins"] = mins
        st["end"] = time.time() + mins * 60

    def reset():
        st["end"] = None
        label.config(text=f"{st['mins']:02d}:00")

    row = tk.Frame(body, bg=t["panel2"])
    row.pack(fill="x", pady=(6, 0))
    for text, cmd in (("25 min", lambda: start(25)), ("50 min", lambda: start(50)), ("Reset", reset)):
        tk.Button(row, text=text, command=cmd, bg=t["panel"], fg=t["text"], bd=0, padx=8,
                  activebackground=t["accent"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))

    api.add_tool("start_focus_session", "Start a focus (pomodoro) timer",
                 {"minutes": ("number", "length in minutes")},
                 lambda a: start(int(float(a.get("minutes", 25)))) or "Focus session started.")
    tick()
