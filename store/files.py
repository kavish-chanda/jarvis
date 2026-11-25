import os
import threading
import time
import tkinter as tk

META = {"id": "files", "name": "File Finder", "version": "1.0", "author": "Kavish",
        "description": "Find and open your documents, pictures and videos. Say: 'find file homework'."}

SAFE = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".wav", ".docx", ".xlsx", ".pptx",
        ".md", ".csv", ".mov", ".mkv", ".webp"}
HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, p) for p in ("Desktop", "Documents", "Downloads", "Pictures", "Videos", "Music",
                                         "OneDrive")]


def find(name, limit=6):
    name, hits, end = name.lower().strip(), [], time.time() + 5
    for root in ROOTS:
        for folder, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "AppData")]
            for f in files:
                if name in f.lower() and os.path.splitext(f)[1].lower() in SAFE:
                    hits.append(os.path.join(folder, f))
                    if len(hits) >= limit:
                        return hits
            if time.time() > end:
                return hits
    return hits


def open_safe(path):
    path = os.path.abspath(path)
    if not path.startswith(HOME) or os.path.splitext(path)[1].lower() not in SAFE:
        return "I only open documents, pictures, music and videos in your user folder."
    os.startfile(path)
    return "Opening " + os.path.basename(path) + "."


def setup(api):
    t = api.theme
    body = api.add_card("FILE FINDER")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.pack(fill="x", ipady=4)
    box = tk.Frame(body, bg=t["panel2"])
    box.pack(fill="x", pady=(6, 0))

    def show(hits):
        for w in box.winfo_children():
            w.destroy()
        for h in hits:
            tk.Button(box, text=os.path.basename(h)[:34], anchor="w", bg=t["panel"], fg=t["text"], bd=0,
                      font=("Segoe UI", 9), cursor="hand2", activebackground=t["accent"],
                      command=lambda p=h: open_safe(p)).pack(fill="x", pady=1)
        if not hits:
            tk.Label(box, text="No matches", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9)).pack(anchor="w")

    def go(_e=None):
        key = entry.get()
        if key.strip():
            threading.Thread(target=lambda: (lambda h: api.ui(lambda: show(h)))(find(key)), daemon=True).start()

    entry.bind("<Return>", go)

    def tool_find(a):
        hits = find(str(a.get("name", "")))
        api.ui(lambda: show(hits))
        return "\n".join(hits) or "No matching files."

    api.add_tool("find_file", "Search the user's Documents, Desktop, Downloads and media folders for a file by name",
                 {"name": ("string", "part of the file name")}, tool_find)
    api.add_tool("open_file", "Open a document, picture, music or video file by full path",
                 {"path": ("string", "full file path")}, lambda a: open_safe(str(a.get("path", ""))))
    api.add_command(r"\bfind (?:the |my )?file (?:called |named )?(.+)",
                    lambda m: (lambda h: (api.ui(lambda: show(h)), "I found " + ", ".join(os.path.basename(x) for x in h[:3]) + "." if h else "I didn't find a matching file.")[1])(find(m.group(1))))
