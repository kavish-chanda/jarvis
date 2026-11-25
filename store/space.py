import threading
import tkinter as tk

META = {"id": "space", "name": "ISS Tracker", "version": "1.0", "author": "Kavish",
        "description": "Live International Space Station position and who is in space right now."}


def setup(api):
    t = api.theme
    body = api.add_card("ISS TRACKER")
    info = tk.Label(body, text="Locating...", anchor="w", justify="left", fg=t["text"], bg=t["panel2"],
                    font=("Consolas", 10))
    info.pack(fill="x")

    def iss():
        d = api.http_json("https://api.wheretheiss.at/v1/satellites/25544")
        lat, lon = d["latitude"], d["longitude"]
        place = f"{abs(lat):.1f}\u00b0{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}\u00b0{'E' if lon >= 0 else 'W'}"
        return place, d["velocity"], d["altitude"]

    def refresh():
        def work():
            try:
                place, vel, alt = iss()
                s = f"{place}\n{vel:,.0f} km/h at {alt:,.0f} km"
            except Exception:
                s = "ISS data unavailable"
            api.ui(lambda: info.config(text=s))
        threading.Thread(target=work, daemon=True).start()
        api.after(10000, refresh)

    def crew(_a=None):
        d = api.http_json("http://api.open-notify.org/astros.json")
        return f"{d['number']} people are in space right now: " + ", ".join(p["name"] for p in d["people"])

    def where(_a=None):
        place, vel, alt = iss()
        return f"The space station is over {place}, moving at {vel:,.0f} kilometers per hour."

    api.add_tool("where_is_iss", "Say where the International Space Station is right now", {}, where)
    api.add_tool("people_in_space", "List who is in space right now", {}, crew)
    refresh()
