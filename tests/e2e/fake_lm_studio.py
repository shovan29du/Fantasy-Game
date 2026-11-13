"""Minimal stand-in for LM Studio's OpenAI-compatible server, for browser tests.

Usage: python fake_lm_studio.py <port>
POST /__fail {"fail": true|false} makes chat completions return HTTP 500.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NARRATION = 'Worldweaver: **The rooftop wind carries the smell of rain.** Captain Hayate: "You are late." He hands you a sealed scroll.'
QUEST = {"title": "The Sealed Scroll", "description": "Carry the sealed scroll to the northern watchtower before dawn.", "hint": "Take the rooftops."}
STATE = {"fail": False}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._json(200, {"data": [{"id": "fake-model", "object": "model"}]})

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/__fail":
            STATE["fail"] = bool(request.get("fail"))
            return self._json(200, STATE)
        if STATE["fail"]:
            self.send_response(500)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        text = " ".join(str(m.get("content", "")) for m in request.get("messages", []))
        if "json" in text.lower():
            reply = json.dumps(QUEST if "quest" in text.lower() else {"name": "Mock", "description": "mock", "items": []})
        else:
            reply = NARRATION
        if request.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for word in reply.split(" "):
                chunk = {"choices": [{"delta": {"content": word + " "}}]}
                self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        else:
            self._json(200, {"choices": [{"message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}]})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
