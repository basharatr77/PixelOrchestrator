def filter_headers(path, request_headers):
    # block non-websocket clients
    if "upgrade" not in request_headers.get("Connection", "").lower():
        return 403, [], b"WebSocket only"
