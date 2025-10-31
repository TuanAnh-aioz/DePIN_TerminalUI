import requests

API_KEY = "0B9396b4beA3F542B0B86519077d82ed0013c498a586435268bF11866D42eCc2"
API_URL = "http://localhost:1111"

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
        payload = {
            "wallet_address": "0x04423d591ef814beD75608876BAD5Dea4F643113",
            "private_key": "MBkDV27rczxTRf+Qw9ApNCAUyqaB0hUSH+u9fgl3RaE="
        }
        response = requests.put(f"{API_URL}/node/update", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None