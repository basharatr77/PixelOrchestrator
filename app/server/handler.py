import json
from http.server import BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    bus = None

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"status":"running"}).encode())

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        data = json.loads(self.rfile.read(length))

        Handler.bus.publish(data)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"message":"queued"}).encode())
