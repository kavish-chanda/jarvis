import threading
import tkinter as tk
import xml.etree.ElementTree as ET

META = {"id": "news", "name": "News Headlines", "version": "1.0", "author": "Kavish",
        "description": "Top world headlines card. Say: 'what is the news?'"}
FEED = "https://feeds.bbci.co.uk/news/rss.xml"


def setup(api):
    t = api.theme
    body = api.add_card("NEWS")
    labels = [tk.Label(body, text="", anchor="w", justify="left", wraplength=230, fg=t["text"],
                       bg=t["panel2"], font=("Segoe UI", 9)) for _ in range(5)]
    for lab in labels:
        lab.pack(fill="x", pady=2)

    def headlines():
        root = ET.fromstring(api.http_get(FEED))
        return [i.findtext("title") for i in root.iter("item")][:5]

    def refresh():
        def work():
            try:
                h = headlines()
                api.ui(lambda: [lab.config(text="\u25b8 " + x) for lab, x in zip(labels, h)])
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()
        api.after(600000, refresh)

    api.add_tool("get_news", "Get the top news headlines right now", {}, lambda a: "; ".join(headlines()))
    api.add_command(r"\b(what'?s|tell me|read me) (the )?(news|headlines)\b",
                    lambda m: "Here are the headlines. " + "; ".join(headlines()[:4]))
    refresh()
