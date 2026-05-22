"""
Hardware ID verification – Windows 11 safe, with signature.
"""
import subprocess
import hashlib
import platform
import os
import json

def get_hwid():
    """Generate unique hardware ID using PowerShell (Windows 11 compatible)."""
    system = platform.system()
    if system == "Windows":
        try:
            mb = subprocess.check_output(
                ["powershell", "-Command", "(Get-CimInstance Win32_BaseBoard).SerialNumber"],
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()
            cpu = subprocess.check_output(
                ["powershell", "-Command", "(Get-CimInstance Win32_Processor).ProcessorId"],
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()
            combined = f"PIXEL-{mb}-{cpu}-ORCHESTRATOR"
            return hashlib.sha256(combined.encode()).hexdigest()
        except Exception:
            return "fallback-hwid-local-error"
    return hashlib.sha256(platform.platform().encode()).hexdigest()

def verify_hwid(license_file="license.dat"):
    if not os.path.exists(license_file):
        return False
    try:
        with open(license_file, "r") as f:
            stored_data = json.load(f)
        expected_sign = hashlib.md5(stored_data["hwid"].encode()).hexdigest()
        return stored_data.get("signature") == expected_sign and stored_data.get("hwid") == get_hwid()
    except Exception:
        return False

def register_hwid(license_file="license.dat"):
    current_hwid = get_hwid()
    signature = hashlib.md5(current_hwid.encode()).hexdigest()
    data = {"hwid": current_hwid, "signature": signature}
    with open(license_file, "w") as f:
        json.dump(data, f, indent=4)
    return True
