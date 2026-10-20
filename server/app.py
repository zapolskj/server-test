import os
import threading
from collections import deque

from flask import Flask, Response, render_template_string, request

app = Flask(__name__)

_queue: deque[str] = deque()
_cond = threading.Condition()

PAGE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
  <form method="post">
    <textarea name="text" rows="5">{{ text }}</textarea><br>
    <button type="submit">send</button>
  </form>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    sent = False
    text = ""
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            with _cond:
                _queue.append(text)
                _cond.notify_all()
            print(f"[-> C++] {text}", flush=True)
            sent = True
    return render_template_string(PAGE, sent=sent, text="" if sent else text)


@app.route("/api/next", methods=["GET"])
def api_next():
    with _cond:
        if not _queue:
            _cond.wait(timeout=25)
            if not _queue:
                return Response(status=204)
        message = _queue.popleft()
    return Response(
        message.encode("utf-8"),
        status=200,
        content_type="text/plain; charset=utf-8",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
