import threading

def start_worker(bus):
    t = threading.Thread(target=bus.run, daemon=True)
    t.start()
    return t
