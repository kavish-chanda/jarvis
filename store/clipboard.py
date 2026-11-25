import tkinter as tk

META = {"id": "clipboard", "name": "Clipboard History", "version": "1.0", "author": "Kavish",
        "description": "Keeps your last 5 copied texts. Click one to copy it again."}


def setup(api):
    t = api.theme
    body = api.add_card("CLIPBOARD")
    hist, last = [], {"v": ""}
    box = tk.Frame(body, bg=t["panel2"])
    box.pack(fill="x")

    def render():
        for w in box.winfo_children():
            w.destroy()
        for text in hist:
            tk.Button(box, text=text[:34].replace("\n", " "), anchor="w", bg=t["panel"], fg=t["text"], bd=0,
                      font=("Segoe UI", 9), cursor="hand2", activebackground=t["accent"],
                      command=lambda x=text: (api.root.clipboard_clear(), api.root.clipboard_append(x))
                      ).pack(fill="x", pady=1)
        if not hist:
            tk.Label(box, text="Copy something...", fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9)).pack(anchor="w")

    def poll():
        try:
            cur = api.root.clipboard_get()
        except Exception:
            cur = ""
        if cur and cur != last["v"] and len(cur) < 500:
            last["v"] = cur
            if cur in hist:
                hist.remove(cur)
            hist.insert(0, cur)
            del hist[5:]
            render()
        api.after(1000, poll)

    api.add_tool("read_clipboard", "Read the text the user last copied", {},
                 lambda a: last["v"][:500] or "The clipboard is empty.")
    render()
    poll()
