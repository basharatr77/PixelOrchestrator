import json
from http.server import HTTPServer
from server.handler import Handler
from logger import logger

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def start_server(bus):
    Handler.bus = bus

    with open("config.json","r") as f:
        cfg = json.load(f)

    host = cfg["host"]
    port = cfg["port"]

    server = ReusableHTTPServer((host, port), Handler)

    logger.info(f"Server started on {host}:{port}")
    print(f"Server running on {host}:{port} 🚀")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        server.server_close()
