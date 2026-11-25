import threading
import tkinter as tk

META = {"id": "crypto", "name": "Crypto Prices", "version": "1.0", "author": "Kavish",
        "description": "Live Bitcoin, Ethereum and Solana prices. Ask: 'what is the price of bitcoin?'"}
COINS = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}
API = "https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&include_24hr_change=true&ids="


def setup(api):
    t = api.theme
    body = api.add_card("CRYPTO")
    rows = {}
    for cid, sym in COINS.items():
        r = tk.Frame(body, bg=t["panel2"])
        r.pack(fill="x")
        tk.Label(r, text=sym, width=5, anchor="w", fg=t["dim"], bg=t["panel2"],
                 font=("Consolas", 10, "bold")).pack(side="left")
        rows[cid] = tk.Label(r, text="...", anchor="e", fg=t["text"], bg=t["panel2"], font=("Consolas", 10))
        rows[cid].pack(side="right")

    def show(d):
        for cid, lab in rows.items():
            if cid in d:
                ch = d[cid].get("usd_24h_change") or 0
                lab.config(text=f"${d[cid]['usd']:,.0f}  {ch:+.1f}%", fg=t["accent"] if ch >= 0 else t["red"])

    def refresh():
        def work():
            try:
                d = api.http_json(API + ",".join(COINS))
                api.ui(lambda: show(d))
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()
        api.after(60000, refresh)

    def price(a):
        coin = str(a.get("coin", "bitcoin")).lower().strip()
        coin = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana"}.get(coin, coin)
        d = api.http_json(API + coin)
        return f"{coin} is ${d[coin]['usd']:,.2f}, {d[coin].get('usd_24h_change', 0):+.1f}% in 24 hours."

    api.add_tool("get_crypto_price", "Get the live USD price of a cryptocurrency",
                 {"coin": ("string", "coin id such as bitcoin")}, price)
    refresh()
