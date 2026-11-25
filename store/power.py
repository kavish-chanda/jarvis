import ctypes
import re
import socket
import subprocess
import threading
import tkinter as tk

META = {"id": "power", "name": "Power & Network", "version": "1.0", "author": "Kavish",
        "description": "Battery level, local IP and live ping. Ask: 'how is my battery?'"}


class PS(ctypes.Structure):
    _fields_ = [("ac", ctypes.c_ubyte), ("flag", ctypes.c_ubyte), ("pct", ctypes.c_ubyte),
                ("sflag", ctypes.c_ubyte), ("life", ctypes.c_ulong), ("full", ctypes.c_ulong)]


def battery():
    s = PS()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
    if s.flag == 128 or s.pct == 255:
        return None, s.ac == 1
    return s.pct, s.ac == 1


def local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "offline"


def ping():
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", "1500", "1.1.1.1"], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, creationflags=0x08000000, timeout=5)
        m = re.search(r"time[=<](\d+)ms", r.stdout)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def setup(api):
    t = api.theme
    body = api.add_card("POWER & NETWORK")
    info = tk.Label(body, text="...", anchor="w", justify="left", fg=t["text"], bg=t["panel2"],
                    font=("Consolas", 10))
    info.pack(fill="x")

    def batt_text():
        try:
            pct, plugged = battery()
        except Exception:
            return "unknown"
        if pct is None:
            return "Plugged in (no battery)"
        return f"{pct}%" + (" (charging)" if plugged else " (on battery)")

    def refresh():
        def work():
            p = ping()
            s = f"Battery {batt_text()}\nIP {local_ip()}\nPing {p} ms" if p is not None else \
                f"Battery {batt_text()}\nIP {local_ip()}\nPing offline"
            api.ui(lambda: info.config(text=s))
        threading.Thread(target=work, daemon=True).start()
        api.after(10000, refresh)

    api.add_tool("battery_status", "Check the PC battery level", {}, lambda a: "Battery is " + batt_text())
    api.add_tool("network_status", "Check internet connection speed to the web (ping)", {},
                 lambda a: f"Ping is {ping()} milliseconds." if ping() is not None else "No internet connection.")
    refresh()
