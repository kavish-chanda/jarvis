import tkinter as tk

META = {"id": "units", "name": "Unit Converter", "version": "1.0", "author": "Kavish",
        "description": "Length, weight, volume, speed and temperature. Say: 'convert 5 miles to km'."}

LEN = {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "yd": 0.9144, "ft": 0.3048, "in": 0.0254}
MASS = {"kg": 1, "g": 0.001, "lb": 0.45359237, "oz": 0.0283495}
VOL = {"l": 1, "ml": 0.001, "gal": 3.78541, "cup": 0.236588}
SPEED = {"mph": 0.44704, "kph": 0.277778, "mps": 1}
ALIAS = {"meter": "m", "meters": "m", "kilometer": "km", "kilometers": "km", "centimeter": "cm",
         "centimeters": "cm", "millimeters": "mm", "mile": "mi", "miles": "mi", "yard": "yd", "yards": "yd",
         "foot": "ft", "feet": "ft", "inch": "in", "inches": "in", "kilogram": "kg", "kilograms": "kg",
         "kgs": "kg", "gram": "g", "grams": "g", "pound": "lb", "pounds": "lb", "lbs": "lb", "ounce": "oz",
         "ounces": "oz", "liter": "l", "liters": "l", "milliliters": "ml", "gallon": "gal", "gallons": "gal",
         "cups": "cup", "kmh": "kph", "kmph": "kph", "celsius": "c", "fahrenheit": "f", "kelvin": "k"}


def conv(v, a, b):
    a, b = ALIAS.get(a.lower(), a.lower()), ALIAS.get(b.lower(), b.lower())
    if a in "cfk" and b in "cfk" and len(a) == len(b) == 1:
        c = v if a == "c" else (v - 32) * 5 / 9 if a == "f" else v - 273.15
        return c if b == "c" else c * 9 / 5 + 32 if b == "f" else c + 273.15, a, b
    for table in (LEN, MASS, VOL, SPEED):
        if a in table and b in table:
            return v * table[a] / table[b], a, b
    raise ValueError("unknown units")


def say(v, a, b):
    r, a, b = conv(float(v), a, b)
    return f"{float(v):g} {a} is {r:,.2f} {b}."


def setup(api):
    t = api.theme
    body = api.add_card("UNITS")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.insert(0, "5 miles to km")
    entry.pack(fill="x", ipady=4)
    out = tk.Label(body, text="", anchor="w", fg=t["accent"], bg=t["panel2"], font=("Segoe UI", 10))
    out.pack(fill="x", pady=(6, 0))

    def go(_e=None):
        parts = entry.get().lower().replace(" to ", " ").split()
        try:
            num = "".join(c for c in parts[0] if c.isdigit() or c == ".")
            unit = parts[0][len(num):] or parts[1]
            target = parts[-1]
            out.config(text=say(num, unit, target))
        except Exception:
            out.config(text="Try: 5 miles to km")

    entry.bind("<Return>", go)
    api.add_tool("convert_units", "Convert between units of length, weight, volume, speed or temperature",
                 {"value": ("number", "amount"), "from_unit": ("string", "unit like miles or kg"),
                  "to_unit": ("string", "unit to convert to")},
                 lambda a: say(a["value"], a["from_unit"], a["to_unit"]))
    api.add_command(r"convert ([\d.]+)\s*([a-z]+) (?:to|into) ([a-z]+)",
                    lambda m: say(m.group(1), m.group(2), m.group(3)))
