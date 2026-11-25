import tkinter as tk

META = {"id": "todo", "name": "To-Do List", "version": "1.0", "author": "Kavish",
        "description": "A saved to-do list card. Say: 'add buy cables to my to-do list'."}


def setup(api):
    t = api.theme
    body = api.add_card("TO-DO")
    items = list(api.get("items", []))
    box = tk.Frame(body, bg=t["panel2"])
    box.pack(fill="x")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.pack(fill="x", pady=(6, 0), ipady=4)

    def render():
        for w in box.winfo_children():
            w.destroy()
        for i, text in enumerate(items):
            row = tk.Frame(box, bg=t["panel2"])
            row.pack(fill="x", pady=1)
            tk.Button(row, text="\u2713", command=lambda i=i: remove(i), bg=t["panel"], fg=t["accent"],
                      bd=0, width=2, cursor="hand2").pack(side="left")
            tk.Label(row, text=text, anchor="w", justify="left", wraplength=190, fg=t["text"],
                     bg=t["panel2"], font=("Segoe UI", 10)).pack(side="left", padx=6)
        if not items:
            tk.Label(box, text="Nothing to do", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 10)).pack(anchor="w")

    def add(text):
        items.append(text)
        api.set("items", items)
        render()

    def remove(i):
        if 0 <= i < len(items):
            items.pop(i)
            api.set("items", items)
            render()

    def on_enter(_e):
        text = entry.get().strip()
        if text:
            add(text)
            entry.delete(0, "end")

    def complete(a):
        key = str(a.get("text", "")).lower()
        for i, item in enumerate(items):
            if key and key in item.lower():
                api.ui(lambda i=i: remove(i))
                return f"Checked off {item}."
        return "I couldn't find that item."

    entry.bind("<Return>", on_enter)
    api.add_tool("add_todo", "Add an item to the user's to-do list", {"text": ("string", "the task")},
                 lambda a: (api.ui(lambda: add(str(a.get("text", "")))), "Added.")[1])
    api.add_tool("list_todos", "Read out the user's to-do list", {},
                 lambda a: ", ".join(items) if items else "The list is empty.")
    api.add_tool("complete_todo", "Check off an item on the to-do list", {"text": ("string", "part of the task")}, complete)
    render()
