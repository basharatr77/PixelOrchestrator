import requests
import time

URL = "http://127.0.0.1:8000/"

print("\n🚀 Sending test events...\n")

devices = ["Samsung A52", "Pixel 7", "Xiaomi Note 12", "iPhone XR"]

for d in devices:
    res = requests.post(URL, json={
        "type": "DEVICE_CONNECTED",
        "payload": d
    })

    print("Sent:", d, "| Response:", res.text)
    time.sleep(1)

print("\n✅ Load test complete")
