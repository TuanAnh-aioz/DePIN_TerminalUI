import os

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

SERVER_URL = os.getenv("SERVER_URL")


# -----------------------------
# 2️⃣ Hàm gọi API từ node
# -----------------------------
def get_node_info():
    try:
        headers = {"x-api-key": API_KEY, "accept": "application/json"}
        r = requests.get(f"{API_URL}/node/info", headers=headers, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def get_node_balance():
    try:
        headers = {"x-api-key": API_KEY, "accept": "application/json"}
        r = requests.get(f"{API_URL}/node/balance", headers=headers, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def update_info():
    try:
        headers = {"x-api-key": API_KEY, "accept": "application/json"}
        payload = {"wallet_address": WALLET_ADDRESS, "private_key": PRIVATE_KEY}
        response = requests.put(f"{API_URL}/node/update", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None
