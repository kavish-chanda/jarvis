import html
import random
import tkinter as tk

META = {"id": "trivia", "name": "Trivia", "version": "1.0", "author": "Kavish",
        "description": "Trivia game. Say: 'quiz me'. Jarvis asks, then reveals the answer."}


def setup(api):
    t = api.theme
    body = api.add_card("TRIVIA")
    q_label = tk.Label(body, text="Say 'quiz me' or press New", anchor="w", justify="left", wraplength=230,
                       fg=t["text"], bg=t["panel2"], font=("Segoe UI", 9))
    q_label.pack(fill="x")
    st = {"answer": ""}

    def fetch():
        r = api.http_json("https://opentdb.com/api.php?amount=1&type=multiple")["results"][0]
        right = html.unescape(r["correct_answer"])
        opts = [html.unescape(x) for x in r["incorrect_answers"]] + [right]
        random.shuffle(opts)
        return html.unescape(r["question"]), opts, right

    def ask(_m=None):
        q, opts, right = fetch()
        st["answer"] = right
        text = q + "\n" + "\n".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(opts))
        api.ui(lambda: (q_label.config(text=text), api.after(10000, lambda: api.speak("The answer is " + right))))
        return "Here is your question. " + q + " Is it " + ", ".join(opts[:-1]) + ", or " + opts[-1] + "?"

    def new():
        import threading
        threading.Thread(target=ask, daemon=True).start()

    row = tk.Frame(body, bg=t["panel2"])
    row.pack(fill="x", pady=(6, 0))
    tk.Button(row, text="New", command=new, bg=t["panel"], fg=t["text"], bd=0, padx=10, pady=3,
              activebackground=t["accent"], cursor="hand2").pack(side="left", padx=(0, 6))
    tk.Button(row, text="Reveal", command=lambda: q_label.config(text="Answer: " + (st["answer"] or "-")),
              bg=t["panel"], fg=t["text"], bd=0, padx=10, pady=3, activebackground=t["accent"],
              cursor="hand2").pack(side="left")
    api.add_tool("trivia_question", "Ask the user a trivia question", {}, ask)
    api.add_command(r"\b(trivia|quiz me)\b", ask)
