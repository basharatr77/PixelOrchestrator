import subprocess
import time

print("🚀 CONTROL CENTER BOOTING")

# Backend
api = subprocess.Popen(["PYTHONPATH=.", "python", "main.py"], shell=True)

time.sleep(2)

# WebSocket server
ws = subprocess.Popen(["PYTHONPATH=.", "python", "dashboard/control_server.py"], shell=True)

print("✅ SYSTEM ONLINE")
print("UI: http://127.0.0.1:5500/dashboard/ui/control.html")

ws.wait()
api.wait()
