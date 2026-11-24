"""
J.A.R.V.I.S - desktop app

Files that go in the same folder:
    jarvis_app.pyw   (this file)
    jarvis_logo.png  (logo shown in the app)
    jarvis_logo.ico  (window icon; also use it for your desktop shortcut)

Needs: SpeechRecognition, pyaudio, pyttsx3 (already installed for Python 3.12)
       Ollama running with the model pulled:  ollama pull llama3.2

How to talk to it:
    "Jarvis ..."        starts a conversation (say it once)
    keep talking        no need to say Jarvis again
    "thank you"         ends the conversation (back to waiting for "Jarvis")
    "Jarvis stop"       turns listening off completely
"""

import os
import re
import sys
import json
import math
import time
import queue
import random
import difflib
import threading
import datetime
import subprocess
import webbrowser
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import scrolledtext

import speech_recognition as sr
import pyttsx3

# Sharper text on high-DPI screens (Windows)
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ======================= CONFIG =======================
WAKE_WORD = "jarvis"
MODEL = "llama3.2"                       # must match: ollama pull llama3.2
OLLAMA_URL = "http://localhost:11434/api/chat"
CONVERSATION_TIMEOUT = 60                # seconds of silence before a conversation ends on its own

# Optional shortcuts that always win over the automatic app search.
# spoken name -> command to run
APP_OVERRIDES = {
    "file explorer": "explorer",
    "task manager": "taskmgr",
    "settings": "start ms-settings:",
    "command prompt": "start cmd",
    "calculator": "calc",
}

SYSTEM_PROMPT = (
    "You are Jarvis, a witty, helpful voice assistant. "
    "Keep replies short (1-3 sentences) because they are spoken aloud. "
    "No markdown, no lists, no emojis."
)

# When packaged as an exe, bundled files live in sys._MEIPASS
SCRIPT_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", SCRIPT_DIR), "Jarvis")
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "jarvis_settings.json")
LOGO_PNG = os.path.join(SCRIPT_DIR, "jarvis_logo.png")
LOGO_ICO = os.path.join(SCRIPT_DIR, "jarvis_logo.ico")

# Colors
BG = "#070b14"
PANEL = "#0d1424"
PANEL2 = "#131d33"
BORDER = "#1c2a48"
ACCENT = "#00d4ff"
TEXT = "#d6e4ff"
DIM = "#7a8aa8"
RED = "#ff4d5e"
# ======================================================


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in c)


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


BG_RGB = hex_to_rgb(BG)

# How the orb looks in each state
STATE_CFG = {
    "offline":      {"speed": 0.003, "base": 0.00, "color": hex_to_rgb("#3b4c6b")},
    "idle":         {"speed": 0.007, "base": 0.05, "color": hex_to_rgb("#00d4ff")},
    "conversation": {"speed": 0.011, "base": 0.10, "color": hex_to_rgb("#5effd0")},
    "thinking":     {"speed": 0.040, "base": 0.10, "color": hex_to_rgb("#ffb347")},
    "speaking":     {"speed": 0.014, "base": 0.22, "color": hex_to_rgb("#00e5ff")},
}


# ======================= ORB =======================
class Orb(tk.Canvas):
    """Rotating sphere of dots + rings + voice bars. Reacts to Jarvis's state."""

    def __init__(self, master, app):
        super().__init__(master, bg=BG, highlightthickness=0)
        self.app = app
        self.t = 0.0
        self.angle = 0.0
        self.level = 0.0
        self.rgb = STATE_CFG["offline"]["color"]
        self.ripples = []
        self.last_ripple = 0.0

        n = 230
        golden = math.pi * (3 - math.sqrt(5))
        self.points = []
        for i in range(n):
            y = 1 - (i / (n - 1)) * 2
            r = math.sqrt(1 - y * y)
            th = golden * i
            self.points.append((math.cos(th) * r, y, math.sin(th) * r))

        self.after(33, self.tick)

    def tick(self):
        try:
            self.draw()
        except Exception:
            pass
        self.after(33, self.tick)

    def draw(self):
        app = self.app
        state = app.orb_state
        cfg = STATE_CFG.get(state, STATE_CFG["offline"])
        self.t += 0.033
        t = self.t

        # target "loudness" for this state
        target = cfg["base"]
        if state == "speaking":
            target += 0.30 * abs(math.sin(t * 9.0) * math.sin(t * 3.3 + 1.0)) + 0.10 * random.random()
        elif state == "thinking":
            target += 0.08 * math.sin(t * 10)
        else:
            target += 0.03 * math.sin(t * 2)
        self.level += (target - self.level) * 0.2
        level = max(0.0, self.level)

        self.rgb = mix(self.rgb, cfg["color"], 0.08)
        rgb = self.rgb
        self.angle += cfg["speed"]

        w = self.winfo_width()
        h = self.winfo_height()
        if w < 80 or h < 80:
            return
        self.delete("all")

        cx = w / 2
        cy = h * 0.42
        R = min(w * 0.30, h * 0.27) * (1 + level * 0.25)

        # soft glow behind the orb
        for k in range(6):
            r = R * (2.0 - k * 0.2)
            col = mix(BG_RGB, rgb, 0.015 + 0.012 * k + level * 0.05)
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=rgb_to_hex(col), outline="")

        # rotating HUD arcs
        ring_col = rgb_to_hex(mix(BG_RGB, rgb, 0.75))
        ring_dim = rgb_to_hex(mix(BG_RGB, rgb, 0.30))
        deg = math.degrees(self.angle)
        for rad_mul, width, spd, extent, offset, col in (
            (1.55, 3, 4.0, 70, 0, ring_col),
            (1.55, 3, 4.0, 40, 180, ring_col),
            (1.72, 2, -2.5, 110, 0, ring_dim),
            (1.72, 2, -2.5, 50, 180, ring_dim),
        ):
            r = R * rad_mul
            start = (deg * spd + offset) % 360
            self.create_arc(cx - r, cy - r, cx + r, cy + r, start=start, extent=extent,
                            style="arc", outline=col, width=width)

        # ripples while speaking
        if state == "speaking" and t - self.last_ripple > 0.55:
            self.ripples.append(t)
            self.last_ripple = t
        alive = []
        for born in self.ripples:
            age = t - born
            if age > 1.6:
                continue
            alive.append(born)
            r = R * (1.15 + age * 0.75)
            col = mix(BG_RGB, rgb, (1 - age / 1.6) * 0.7)
            self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=rgb_to_hex(col), width=2)
        self.ripples = alive

        # the dot sphere
        a = self.angle
        ca, sa = math.cos(a), math.sin(a)
        tilt = 0.4
        ct, st = math.cos(tilt), math.sin(tilt)
        proj = []
        for i, (x, y, z) in enumerate(self.points):
            if state == "speaking":
                wob = 1 + level * 0.30 * math.sin(t * 6 + i * 0.9)
            else:
                wob = 1 + level * 0.12 * math.sin(t * 3 + i * 0.5)
            x1 = x * ca + z * sa
            z1 = -x * sa + z * ca
            y1 = y * ct - z1 * st
            z2 = y * st + z1 * ct
            p = 3.0 / (3.0 - z2)
            sx = cx + x1 * R * wob * p
            sy = cy + y1 * R * wob * p
            proj.append((z2, sx, sy))
        proj.sort()
        for z2, sx, sy in proj:
            depth = (z2 + 1) / 2
            size = 1.0 + 2.6 * depth + level * 1.6 * depth
            col = mix(BG_RGB, rgb, 0.22 + 0.78 * depth)
            if depth > 0.8:
                col = mix(col, (255, 255, 255), (depth - 0.8) * 1.2)
            self.create_oval(sx - size, sy - size, sx + size, sy + size,
                             fill=rgb_to_hex(col), outline="")

        # voice bars
        wave_y = min(h - 110, cy + R * 1.95)
        bars = 41
        gap = max(8, min(16, w / 70))
        for i in range(bars):
            d = i - bars // 2
            envelope = 1 - abs(d) / (bars / 2 + 1)
            wiggle = 0.5 + 0.5 * abs(math.sin(t * 7 + i * 0.6) + 0.5 * math.sin(t * 11 + i * 1.3))
            hh = 3 + envelope * level * 230 * wiggle
            x = cx + d * gap
            col = mix(BG_RGB, rgb, 0.35 + 0.65 * envelope)
            self.create_line(x, wave_y - hh, x, wave_y + hh, width=4, capstyle="round",
                             fill=rgb_to_hex(col))

        # captions
        if app.caption_user:
            self.create_text(cx, wave_y + 48, text="You: " + app.caption_user, fill=DIM,
                             font=("Segoe UI", 11), width=w * 0.75, justify="center")
        if app.caption_jarvis:
            self.create_text(cx, wave_y + 90, text=app.caption_jarvis, fill=TEXT,
                             font=("Segoe UI", 14), width=w * 0.75, justify="center")


# ======================= APP =======================
class JarvisApp:
    def __init__(self, root):
        self.root = root
        root.title("Jarvis")
        root.geometry("1220x760")
        root.minsize(980, 620)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        try:
            root.iconbitmap(LOGO_ICO)
        except Exception:
            pass

        # state shared with the worker thread
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.running = False
        self.conversation = False
        self.orb_state = "offline"
        self.caption_user = ""
        self.caption_jarvis = 'Press START, then say "Jarvis".'
        self.speak_lock = threading.Lock()
        self.speak_enabled = True
        self.recognizer = sr.Recognizer()
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.start_apps = {}          # lowercase name -> (display name, app id)
        self.settings = self.load_settings()
        self.mic_index = None
        self.mic_map = {}

        self.build_ui()
        self.refresh_mics()
        self.poll_queue()
        self.tick_clock()
        threading.Thread(target=self.load_start_apps, daemon=True).start()

    # ---------- settings ----------
    def load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_settings(self):
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f)
        except Exception:
            pass

    # ---------- UI ----------
    def build_ui(self):
        root = self.root
        root.grid_columnconfigure(0, weight=0)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=0)
        root.grid_rowconfigure(0, weight=1)

        self.build_left(root)
        self.build_center(root)
        self.build_right(root)

    # ----- left sidebar -----
    def build_left(self, root):
        left = tk.Frame(root, bg=PANEL, width=270)
        left.grid(row=0, column=0, sticky="ns")
        left.grid_propagate(False)

        self.logo_img = None
        try:
            img = tk.PhotoImage(file=LOGO_PNG)
            self.logo_img = img.subsample(2, 2)
            tk.Label(left, image=self.logo_img, bg=PANEL).pack(pady=(24, 4))
        except Exception:
            pass

        tk.Label(left, text="J.A.R.V.I.S", font=("Segoe UI", 20, "bold"),
                 fg=ACCENT, bg=PANEL).pack()

        self.status = tk.Label(left, text="Offline", font=("Segoe UI", 11, "bold"),
                               fg=DIM, bg=PANEL)
        self.status.pack(pady=(10, 0))
        self.mode_label = tk.Label(left, text="", font=("Segoe UI", 10), fg=DIM, bg=PANEL)
        self.mode_label.pack(pady=(0, 14))

        self.button = tk.Button(left, text="START", font=("Segoe UI", 14, "bold"),
                                fg=BG, bg=ACCENT, activebackground=ACCENT, bd=0,
                                width=16, height=1, cursor="hand2", command=self.toggle)
        self.button.pack(pady=(0, 18))

        tk.Label(left, text="MICROPHONE", font=("Segoe UI", 9, "bold"),
                 fg=DIM, bg=PANEL, anchor="w").pack(fill="x", padx=22)
        mic_row = tk.Frame(left, bg=PANEL)
        mic_row.pack(fill="x", padx=22, pady=(4, 0))
        self.mic_var = tk.StringVar()
        self.mic_menu = tk.OptionMenu(mic_row, self.mic_var, "")
        self.mic_menu.config(bg=PANEL2, fg=TEXT, activebackground=BORDER, activeforeground=TEXT,
                             highlightthickness=0, bd=0, relief="flat", anchor="w",
                             font=("Segoe UI", 9), width=22)
        self.mic_menu["menu"].config(bg=PANEL2, fg=TEXT, activebackground=ACCENT,
                                     activeforeground=BG, font=("Segoe UI", 9))
        self.mic_menu.pack(side="left", fill="x", expand=True)
        tk.Button(mic_row, text="\u21bb", bg=PANEL2, fg=TEXT, bd=0, cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  command=self.refresh_mics).pack(side="left", padx=(6, 0), ipadx=6)

        self.speak_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Speak replies out loud", variable=self.speak_var,
                       command=lambda: setattr(self, "speak_enabled", self.speak_var.get()),
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2, activebackground=PANEL,
                       activeforeground=TEXT, bd=0, highlightthickness=0,
                       font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(16, 0))

        hint = ('Say "Jarvis" to begin.\n'
                'Keep talking, no need to repeat it.\n'
                '"Thank you" ends the chat.\n'
                '"Jarvis stop" turns me off.')
        tk.Label(left, text=hint, font=("Segoe UI", 9), fg=DIM, bg=PANEL,
                 justify="left", anchor="w").pack(side="bottom", fill="x", padx=22, pady=20)

    # ----- center (orb / chat) -----
    def build_center(self, root):
        center = tk.Frame(root, bg=BG)
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        tabs = tk.Frame(center, bg=BG)
        tabs.grid(row=0, column=0, sticky="ew", pady=(14, 0))
        self.tab_orb = tk.Button(tabs, text="ORB", font=("Segoe UI", 10, "bold"), bd=0, width=10,
                                 cursor="hand2", command=lambda: self.show_view("orb"))
        self.tab_chat = tk.Button(tabs, text="CHAT", font=("Segoe UI", 10, "bold"), bd=0, width=10,
                                  cursor="hand2", command=lambda: self.show_view("chat"))
        self.tab_orb.pack(side="left", padx=(24, 4))
        self.tab_chat.pack(side="left")

        body = tk.Frame(center, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        # orb view
        self.orb = Orb(body, self)
        self.orb.grid(row=0, column=0, sticky="nsew")

        # chat view
        self.chat_frame = tk.Frame(body, bg=BG)
        self.chat_frame.grid(row=0, column=0, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_box = scrolledtext.ScrolledText(
            self.chat_frame, bg=PANEL, fg=TEXT, font=("Consolas", 11), bd=0, wrap="word",
            state="disabled", padx=14, pady=12, insertbackground=TEXT)
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.chat_box.tag_config("you", foreground=ACCENT)
        self.chat_box.tag_config("jarvis", foreground="#ffffff")
        self.chat_box.tag_config("sys", foreground=DIM)

        entry_row = tk.Frame(self.chat_frame, bg=BG)
        entry_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 18))
        entry_row.grid_columnconfigure(0, weight=1)
        self.entry = tk.Entry(entry_row, bg=PANEL2, fg=TEXT, insertbackground=TEXT, bd=0,
                              font=("Segoe UI", 12), relief="flat")
        self.entry.grid(row=0, column=0, sticky="ew", ipady=9, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send_typed())
        tk.Button(entry_row, text="SEND", font=("Segoe UI", 10, "bold"), bg=ACCENT, fg=BG,
                  activebackground=ACCENT, bd=0, width=9, cursor="hand2",
                  command=self.send_typed).grid(row=0, column=1, ipady=6)

        self.show_view("orb")

    def show_view(self, which):
        if which == "orb":
            tk.Misc.tkraise(self.orb)  # Canvas overrides tkraise (it raises canvas items), so call Misc's
        else:
            self.chat_frame.tkraise()
            self.entry.focus_set()
        for btn, name in ((self.tab_orb, "orb"), (self.tab_chat, "chat")):
            if name == which:
                btn.config(bg=ACCENT, fg=BG, activebackground=ACCENT)
            else:
                btn.config(bg=PANEL2, fg=TEXT, activebackground=BORDER)

    # ----- right panel (modules) -----
    def build_right(self, root):
        right = tk.Frame(root, bg=PANEL, width=250)
        right.grid(row=0, column=2, sticky="ns")
        right.grid_propagate(False)

        tk.Label(right, text="MODULES", font=("Segoe UI", 9, "bold"), fg=DIM, bg=PANEL,
                 anchor="w").pack(fill="x", padx=18, pady=(22, 6))
        self.modules = tk.Frame(right, bg=PANEL)
        self.modules.pack(fill="both", expand=True, padx=14)

        # ---- ADD NEW MODULES HERE: call self.add_card("Title", "text") ----
        _, self.clock_label = self.add_card("CLOCK", "", big=True)
        _, self.last_heard_label = self.add_card("LAST HEARD", "-")
        self.add_card("EMPTY SLOT", "Add a module here\n(weather, music, stats...)", dim=True)
        self.add_card("EMPTY SLOT", "Add a module here", dim=True)
        self.add_card("EMPTY SLOT", "Add a module here", dim=True)

    def add_card(self, title, body, big=False, dim=False):
        card = tk.Frame(self.modules, bg=PANEL2, highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x", pady=6)
        tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), fg=DIM, bg=PANEL2,
                 anchor="w").pack(fill="x", padx=12, pady=(8, 0))
        label = tk.Label(card, text=body, bg=PANEL2, anchor="w", justify="left",
                         fg=DIM if dim else TEXT, wraplength=200,
                         font=("Segoe UI", 20, "bold") if big else ("Segoe UI", 10))
        label.pack(fill="x", padx=12, pady=(2, 10))
        return card, label

    def tick_clock(self):
        now = datetime.datetime.now()
        self.clock_label.config(text=now.strftime("%I:%M %p").lstrip("0"))
        self.root.after(1000, self.tick_clock)

    # ---------- microphones ----------
    def refresh_mics(self):
        mics = [("Default microphone", None)]
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            hosts = {i: pa.get_host_api_info_by_index(i)["name"]
                     for i in range(pa.get_host_api_count())}
            found = []
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    found.append((info["name"], i, hosts.get(info["hostApi"], "")))
            pa.terminate()
            mme = [f for f in found if "MME" in f[2]]
            for name, idx, _ in (mme or found):
                mics.append((name, idx))
        except Exception:
            try:
                for idx, name in enumerate(sr.Microphone.list_microphone_names()):
                    mics.append((name, idx))
            except Exception:
                pass

        # make labels unique
        self.mic_map = {}
        for name, idx in mics:
            label = name if name not in self.mic_map else f"{name} ({idx})"
            self.mic_map[label] = idx

        menu = self.mic_menu["menu"]
        menu.delete(0, "end")
        for label in self.mic_map:
            menu.add_command(label=label, command=lambda l=label: self.pick_mic(l))

        saved = self.settings.get("mic")
        self.pick_mic(saved if saved in self.mic_map else "Default microphone", save=False)

    def pick_mic(self, label, save=True):
        self.mic_var.set(label if len(label) <= 34 else label[:33] + "\u2026")
        self.mic_index = self.mic_map.get(label)
        if save:
            self.settings["mic"] = label
            self.save_settings()
            self.log("sys", f"Microphone set to: {label}")

    # ---------- start / stop ----------
    def toggle(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.button.config(state="disabled")
            self.status.config(text="Stopping...")
        else:
            self.stop_event.clear()
            self.running = True
            self.orb_state = "idle"
            self.thread = threading.Thread(target=self.run_loop, daemon=True)
            self.thread.start()

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()

    def base_state(self):
        if self.conversation:
            return "conversation"
        return "idle" if self.running else "offline"

    # ---------- queue (worker -> UI) ----------
    def log(self, kind, text):
        self.q.put(("log", kind, text))

    def poll_queue(self):
        try:
            while True:
                item = self.q.get_nowait()
                if item[0] == "log":
                    _, kind, text = item
                    self.append_chat(kind, text)
                    if kind == "you":
                        self.caption_user = text
                        self.last_heard_label.config(text=text)
                    elif kind == "jarvis":
                        self.caption_jarvis = text
                elif item[0] == "state" and item[1] == "stopped":
                    self.button.config(state="normal")
        except queue.Empty:
            pass

        # keep sidebar labels in sync
        if self.running:
            self.status.config(text="ONLINE", fg=ACCENT)
            self.mode_label.config(text="In conversation" if self.conversation
                                   else 'Waiting for "Jarvis"')
            if self.button["state"] == "normal":
                self.button.config(text="STOP", bg=RED, activebackground=RED)
        else:
            self.status.config(text="Offline", fg=DIM)
            self.mode_label.config(text="")
            self.button.config(text="START", bg=ACCENT, activebackground=ACCENT)
        self.root.after(100, self.poll_queue)

    def append_chat(self, kind, text):
        prefix = {"you": "You: ", "jarvis": "Jarvis: ", "sys": ""}.get(kind, "")
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", prefix + text + "\n\n", kind)
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    # ---------- typed chat ----------
    def send_typed(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.log("you", text)
        threading.Thread(target=self.typed_worker, args=(text,), daemon=True).start()

    def typed_worker(self, text):
        self.com_init()
        try:
            reply = self.handle_command(text.lower())
            self.speak(reply)
        except Exception as e:
            self.log("sys", f"[Error] {e}")

    # ---------- voice ----------
    @staticmethod
    def com_init():
        # Needed so the voice engine works from a background thread on Windows
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

    def speak(self, text):
        self.log("jarvis", text)
        if not self.speak_enabled:
            return
        with self.speak_lock:
            self.orb_state = "speaking"
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 180)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            finally:
                self.orb_state = self.base_state()

    def listen(self, timeout=None, phrase_limit=10):
        with sr.Microphone(device_index=self.mic_index) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = self.recognizer.listen(source, timeout=timeout,
                                               phrase_time_limit=phrase_limit)
            except sr.WaitTimeoutError:
                return ""
        try:
            return self.recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            self.log("sys", "Speech service unavailable (check your internet).")
            return ""

    # ---------- brain ----------
    def ask_brain(self, question):
        self.orb_state = "thinking"
        self.history.append({"role": "user", "content": question})
        payload = json.dumps({"model": MODEL, "messages": self.history,
                              "stream": False}).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            answer = data["message"]["content"].strip()
        except Exception as e:
            self.log("sys", f"[Ollama error] {e}")
            self.log("sys", f"Is Ollama running, and did you run: ollama pull {MODEL} ?")
            self.history.pop()
            self.orb_state = self.base_state()
            return "Sorry, I couldn't reach my brain right now."
        self.history.append({"role": "assistant", "content": answer})
        if len(self.history) > 11:
            del self.history[1:-10]
        return answer

    # ---------- opening apps ----------
    def load_start_apps(self):
        """Ask Windows for every app in the Start menu (classic + Store apps)."""
        try:
            ps = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
                  "Get-StartApps | ConvertTo-Json -Compress")
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, encoding="utf-8", timeout=40,
                stdin=subprocess.DEVNULL, creationflags=0x08000000)
            data = json.loads(out.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = (item.get("Name") or "").strip()
                app_id = (item.get("AppID") or "").strip()
                if name and app_id:
                    self.start_apps[name.lower()] = (name, app_id)
            self.log("sys", f"Found {len(self.start_apps)} apps I can open by voice.")
        except Exception as e:
            self.log("sys", f"[App scan failed] {e}")

    @staticmethod
    def launch(cmd, shell=False):
        subprocess.Popen(cmd, shell=shell, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=0x08000000 if shell else 0)

    def open_app(self, spoken):
        """Return a spoken reply if an app was opened, else None."""
        words = [w for w in re.sub(r"[^a-z0-9+# ]", " ", spoken.lower()).split()
                 if w not in ("the", "app", "application", "program", "please", "for", "me")]
        name = " ".join(words)
        if not name:
            return None

        for key, cmd in APP_OVERRIDES.items():
            if key == name or key in name:
                self.launch(cmd, shell=True)
                return f"Opening {key}."

        names = list(self.start_apps)
        match = None
        if name in self.start_apps:
            match = name
        if not match:
            contains = [n for n in names if name in n]
            if contains:
                match = min(contains, key=len)
        if not match:
            inside = [n for n in names if len(n) >= 3 and n in name]
            if inside:
                match = max(inside, key=len)
        if not match:
            close = difflib.get_close_matches(name, names, n=1, cutoff=0.6)
            if close:
                match = close[0]
        if not match:
            return None

        display, app_id = self.start_apps[match]
        try:
            if os.path.exists(app_id):
                os.startfile(app_id)
            else:
                self.launch(["explorer.exe", "shell:AppsFolder\\" + app_id])
        except Exception as e:
            self.log("sys", f"[Launch error] {e}")
            return f"I found {display} but couldn't open it."
        return f"Opening {display}."

    # ---------- commands ----------
    def handle_command(self, cmd):
        """Return the reply to speak."""
        cmd = cmd.strip()
        if not cmd:
            return "Yes?"

        if "time" in cmd and ("what" in cmd or "tell" in cmd):
            return datetime.datetime.now().strftime("It's %I:%M %p.").replace("It's 0", "It's ")

        if "date" in cmd or "what day" in cmd:
            return datetime.datetime.now().strftime("It's %A, %B %d.")

        for prefix in ("open ", "launch "):
            if cmd.startswith(prefix):
                target = cmd[len(prefix):]
                reply = self.open_app(target)
                if reply:
                    return reply
                site = re.sub(r"[^a-z0-9]", "", target)
                if site:
                    webbrowser.open(f"https://{site}.com")
                    return f"I couldn't find an app called {target}, so I'm trying it as a website."
                return "I didn't catch what to open."

        if cmd.startswith("play "):
            webbrowser.open("https://www.youtube.com/results?search_query="
                            + urllib.parse.quote(cmd[5:]))
            return f"Searching YouTube for {cmd[5:]}."

        if cmd.startswith("search for ") or cmd.startswith("search "):
            q = cmd[11:] if cmd.startswith("search for ") else cmd[7:]
            webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(q))
            return f"Searching for {q}."

        return self.ask_brain(cmd)

    # ---------- main voice loop ----------
    def run_loop(self):
        self.com_init()
        self.conversation = False
        last_activity = time.time()
        try:
            self.speak("Jarvis online.")
            while not self.stop_event.is_set():
                heard = self.listen(timeout=2, phrase_limit=10)
                if self.stop_event.is_set():
                    break

                if self.conversation and time.time() - last_activity > CONVERSATION_TIMEOUT:
                    self.conversation = False
                    self.orb_state = self.base_state()
                    self.log("sys", "Conversation timed out. Say \"Jarvis\" to start again.")

                if not heard:
                    continue

                # "Jarvis stop" works any time
                if re.search(r"\bjarvis\b\W*\bstop\b", heard):
                    self.log("you", heard)
                    self.speak("Shutting down. Goodbye.")
                    break

                if not self.conversation:
                    if WAKE_WORD not in heard:
                        continue
                    command = heard.split(WAKE_WORD, 1)[1].strip()
                    self.conversation = True
                    self.orb_state = "conversation"
                    self.log("you", heard)
                    last_activity = time.time()
                    if not command:
                        self.speak("Yes?")
                        last_activity = time.time()
                        continue
                else:
                    command = re.sub(r"^\s*jarvis\W*", "", heard).strip()
                    self.log("you", heard)
                    last_activity = time.time()

                if re.search(r"\bthank(s| you)\b", command):
                    self.speak("You're welcome.")
                    self.conversation = False
                    self.orb_state = self.base_state()
                    continue

                reply = self.handle_command(command)
                self.speak(reply)
                last_activity = time.time()
        except Exception as e:
            self.log("sys", f"[Error] {e}")
        finally:
            self.running = False
            self.conversation = False
            self.orb_state = "offline"
            self.log("sys", "--- Jarvis stopped ---")
            self.q.put(("state", "stopped"))


if __name__ == "__main__":
    root = tk.Tk()
    JarvisApp(root)
    root.mainloop()