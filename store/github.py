import threading
import tkinter as tk
import urllib.parse
import webbrowser

META = {"id": "github", "name": "GitHub Stats", "version": "1.0", "author": "Kavish",
        "description": "Shows repos, followers and stars for a GitHub user. Set your username on the card."}


def setup(api):
    t = api.theme

    def stats(user):
        u = urllib.parse.quote(user)
        info = api.http_json("https://api.github.com/users/" + u)
        repos = api.http_json(f"https://api.github.com/users/{u}/repos?per_page=100")
        stars = sum(r.get("stargazers_count", 0) for r in repos)
        return f"{info['login']}: {info['public_repos']} repos, {info['followers']} followers, {stars} stars."

    body = api.add_card("GITHUB")
    entry = tk.Entry(body, bg=t["panel"], fg=t["text"], insertbackground=t["text"], bd=0, font=("Segoe UI", 10))
    entry.insert(0, api.get("user", ""))
    entry.pack(fill="x", ipady=4)
    out = tk.Label(body, text="Type your username, press Enter", anchor="w", justify="left", wraplength=230,
                   fg=t["dim"], bg=t["panel2"], font=("Segoe UI", 9))
    out.pack(fill="x", pady=(6, 0))

    def go(_e=None):
        user = entry.get().strip()
        if not user:
            return
        api.set("user", user)

        def work():
            try:
                s = stats(user)
            except Exception:
                s = "Couldn't load that user."
            api.ui(lambda: out.config(text=s, fg=t["text"]))
        threading.Thread(target=work, daemon=True).start()

    entry.bind("<Return>", go)
    tk.Button(body, text="Open profile", bg=t["panel"], fg=t["text"], bd=0, pady=3, cursor="hand2",
              activebackground=t["accent"],
              command=lambda: entry.get().strip() and webbrowser.open("https://github.com/" + entry.get().strip())
              ).pack(fill="x", pady=(6, 0))
    api.add_tool("github_stats", "Get GitHub stats for a user (empty means the saved user)",
                 {"user": ("string", "GitHub username or empty")},
                 lambda a: stats(a.get("user") or api.get("user", "")))
    if entry.get().strip():
        go()
