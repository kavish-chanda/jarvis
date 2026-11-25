import datetime
import os
import subprocess
import threading
import tkinter as tk

META = {"id": "screenshot", "name": "Screenshot", "version": "1.0", "author": "Kavish",
        "description": "Capture your screen. Say: 'take a screenshot'. Saves to Pictures/Jarvis."}


def shot():
    folder = os.path.join(os.path.expanduser("~"), "Pictures", "Jarvis")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, datetime.datetime.now().strftime("shot-%Y%m%d-%H%M%S.png"))
    ps = ("Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
          "$b=[System.Windows.Forms.SystemInformation]::VirtualScreen;"
          "$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;"
          "$g=[System.Drawing.Graphics]::FromImage($bmp);"
          "$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);"
          "$bmp.Save('" + path.replace("'", "''") + "')")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], stdin=subprocess.DEVNULL,
                   capture_output=True, creationflags=0x08000000, timeout=30)
    return path if os.path.exists(path) else None


def setup(api):
    t = api.theme
    body = api.add_card("SCREENSHOT")
    out = tk.Label(body, text="Saved to Pictures/Jarvis", anchor="w", fg=t["dim"], bg=t["panel2"],
                   font=("Segoe UI", 9))

    def capture():
        def work():
            p = shot()
            api.ui(lambda: out.config(text=("Saved " + os.path.basename(p)) if p else "Capture failed"))
        threading.Thread(target=work, daemon=True).start()

    tk.Button(body, text="Capture screen", command=capture, bg=t["panel"], fg=t["text"], bd=0, pady=5,
              activebackground=t["accent"], cursor="hand2").pack(fill="x")
    out.pack(fill="x", pady=(6, 0))

    def take(*_a):
        p = shot()
        return f"Screenshot saved as {os.path.basename(p)}." if p else "I couldn't take the screenshot."

    api.add_tool("take_screenshot", "Take a screenshot of the whole screen", {}, take)
    api.add_command(r"\b(take|capture) (a )?screenshot\b", take)
