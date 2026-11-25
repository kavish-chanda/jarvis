import threading
import time
import tkinter as tk

META = {"id": "scenes", "name": "Scenes", "version": "1.0", "author": "Kavish",
        "description": "Open a group of apps with one command. Save 'gaming: steam, discord', then say 'start gaming mode'."}


def setup(api):
    t = api.theme
    scenes = dict(api.get("scenes", {}))
    body = api.add_card("SCENES")
    box = tk.Frame(body, bg=t["panel2"])
    box.pack(fill="x")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.pack(fill="x", pady=(6, 0), ipady=4)
    tk.Label(body, text="Save: name: app, app, app", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 8),
             anchor="w").pack(fill="x")

    def run(name):
        apps = scenes.get(str(name).lower().strip())
        if apps is None:
            raise KeyError(name)

        def work():
            for a in apps:
                api.open_app(a)
                time.sleep(1.2)
        threading.Thread(target=work, daemon=True).start()
        return f"Starting {name} mode."

    def save():
        api.set("scenes", scenes)

    def delete(name):
        scenes.pop(name, None)
        save()
        render()

    def render():
        for w in box.winfo_children():
            w.destroy()
        for name in scenes:
            row = tk.Frame(box, bg=t["panel2"])
            row.pack(fill="x", pady=1)
            tk.Button(row, text=name.title(), command=lambda n=name: run(n), bg=t["panel"], fg=t["text"], bd=0,
                      anchor="w", cursor="hand2", activebackground=t["accent"]).pack(side="left", fill="x", expand=True)
            tk.Button(row, text="x", command=lambda n=name: delete(n), bg=t["panel"], fg=t["dim"], bd=0,
                      width=2, cursor="hand2").pack(side="right", padx=(4, 0))

    def on_enter(_e):
        if ":" in entry.get():
            name, apps = entry.get().split(":", 1)
            items = [x.strip() for x in apps.split(",") if x.strip()]
            if name.strip() and items:
                scenes[name.strip().lower()] = items
                save()
                render()
                entry.delete(0, "end")

    entry.bind("<Return>", on_enter)
    api.add_tool("run_scene", "Open a saved group of apps (a scene) such as gaming mode",
                 {"name": ("string", "scene name, e.g. gaming")}, lambda a: run(a.get("name", "")))
    api.add_tool("list_scenes", "List the user's saved scenes", {},
                 lambda a: ", ".join(scenes) or "No scenes saved yet.")
    api.add_command(r"\b(?:activate|start|enable|launch|run) (?:the )?(.+?) (?:mode|scene)\b",
                    lambda m: run(m.group(1)))
    render()
