import datetime
import threading
import tkinter as tk
import urllib.parse

META = {"id": "forecast", "name": "3-Day Forecast", "version": "1.0", "author": "Kavish",
        "description": "Weather forecast card with sunrise, sunset and moon phase. Say: 'what's the forecast?'"}


def setup(api):
    t = api.theme
    body = api.add_card("FORECAST")
    rows = [tk.Label(body, text="", anchor="w", fg=t["text"], bg=t["panel2"], font=("Consolas", 9)) for _ in range(4)]
    for r in rows:
        r.pack(fill="x")

    def fetch(city=""):
        return api.http_json("https://wttr.in/" + urllib.parse.quote(city) + "?format=j1")

    def line(x):
        day = datetime.date.fromisoformat(x["date"]).strftime("%a")
        return f"{day}  {x['mintempF']}-{x['maxtempF']}F  {x['hourly'][4]['weatherDesc'][0]['value']}"

    def show(d):
        for r, x in zip(rows, d["weather"][:3]):
            r.config(text=line(x))
        a = d["weather"][0]["astronomy"][0]
        rows[3].config(text=f"Sun {a['sunrise']} - {a['sunset']}\nMoon: {a['moon_phase']}", fg=t["dim"], justify="left")

    def refresh():
        def work():
            try:
                d = fetch()
                api.ui(lambda: show(d))
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()
        api.after(1800000, refresh)

    def summary(city=""):
        d = fetch(city)
        return "Forecast. " + ". ".join(line(x) for x in d["weather"][:3])

    api.add_tool("get_forecast", "Get the 3 day weather forecast. Leave city empty for the user's location",
                 {"city": ("string", "city or empty")}, lambda a: summary(a.get("city", "")))
    api.add_command(r"\bforecast\b", lambda m: summary())
    refresh()
