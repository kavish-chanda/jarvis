import datetime
import tkinter as tk

META = {"id": "countdown", "name": "Countdowns", "version": "1.0", "author": "Kavish",
        "description": "Days until your events. Add 'Winter Break, 2026-12-19'. Ask: 'how many days until winter break?'"}


def setup(api):
    t = api.theme
    events = dict(api.get("events", {}))
    body = api.add_card("COUNTDOWNS")
    box = tk.Label(body, text="", anchor="w", justify="left", wraplength=230, fg=t["text"], bg=t["panel2"],
                   font=("Segoe UI", 10))
    box.pack(fill="x")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.pack(fill="x", pady=(6, 0), ipady=4)
    hint = tk.Label(body, text="Add: Name, YYYY-MM-DD", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 8), anchor="w")
    hint.pack(fill="x")

    def days(date_s):
        return (datetime.date.fromisoformat(date_s) - datetime.date.today()).days

    def render():
        lines = []
        for name, d in sorted(events.items(), key=lambda kv: kv[1]):
            n = days(d)
            lines.append(f"{name}: " + ("today!" if n == 0 else f"{n} days" if n > 0 else "passed"))
        box.config(text="\n".join(lines) or "No events yet")

    def add(name, date_s):
        datetime.date.fromisoformat(date_s)
        events[name] = date_s
        api.set("events", events)
        render()

    def find(key):
        for name, d in events.items():
            if key.lower().strip() in name.lower():
                return name, days(d)
        raise KeyError(key)

    def on_enter(_e):
        try:
            name, d = entry.get().rsplit(",", 1)
            add(name.strip(), d.strip())
            entry.delete(0, "end")
            hint.config(text="Add: Name, YYYY-MM-DD", fg=t["dim"])
        except Exception:
            hint.config(text="Use: Winter Break, 2026-12-19", fg=t["red"])

    def until(key):
        name, n = find(key)
        return f"{name} is today!" if n == 0 else f"{n} days until {name}." if n > 0 else f"{name} was {-n} days ago."

    entry.bind("<Return>", on_enter)
    api.add_tool("add_countdown", "Save an event date to count down to",
                 {"name": ("string", "event name"), "date": ("string", "date as YYYY-MM-DD")},
                 lambda a: (api.ui(lambda: add(a["name"], a["date"])), "Saved.")[1])
    api.add_tool("days_until", "Say how many days until a saved event", {"name": ("string", "event name")},
                 lambda a: until(a.get("name", "")))
    api.add_command(r"how many days (?:until|till|to) (.+)", lambda m: until(m.group(1)))
    render()
    api.after(3600000, render)
