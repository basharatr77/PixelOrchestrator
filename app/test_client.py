import requests
import time

url = "http://127.0.0.1:8000/"

print("TEST 1: Sending device event...")

res = requests.post(url, json={
    "type": "DEVICE_CONNECTED",
    "payload": "Samsung A52"
})

print("Response:", res.text)

time.sleep(1)

print("TEST 2: Checking server status...")

res2 = requests.get(url)

print("GET Response:", res2.text)

print("TEST COMPLETE ✔")
