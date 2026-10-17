import hashlib
import struct
import time
import requests

BASE_URL = "https://byteme-soulvault-api.onrender.com"

def derive_client_label(seed_bytes):
    value = 0x811C9DC5
    for b in seed_bytes:
        value = ((value ^ b) * 0x01000193) & 0xFFFFFFFF
        value ^= (value >> 13)
        value = ((value << 7) | (value >> 25)) & 0xFFFFFFFF
    
    value ^= (len(seed_bytes) * 0x9E3779B9) & 0xFFFFFFFF
    
    value ^= (value >> 16)
    value = (value * 0x7FEB352D) & 0xFFFFFFFF
    value ^= (value >> 15)
    value = (value * 0x846CA68B) & 0xFFFFFFFF
    value ^= (value >> 16)
    
    return f"g3-{value:08x}"

def solve_pow(prefix, difficulty=20, rounds=3):
    print(f"[*] Searching for {difficulty}-bit proof-of-work (3 echo rounds)...")
    t0 = time.time()
    counter = 0
    full_zero_bytes, remaining_bits = divmod(difficulty, 8)
    
    while counter <= 0xFFFFFFFF:
        le_counter = struct.pack("<I", counter)
        d = hashlib.sha256(prefix + le_counter).digest()
        for r in range(rounds):
            d = hashlib.sha256(d + prefix + bytes([r])).digest()
            
        if d[:full_zero_bytes] == b"\x00" * full_zero_bytes:
            if not remaining_bits or (d[full_zero_bytes] >> (8 - remaining_bits) == 0):
                elapsed = time.time() - t0
                print(f"[+] Found counter: {counter} in {elapsed:.2f}s!")
                return counter
        counter += 1
    raise RuntimeError("Counter search exhausted")

def run():
    seed = "Google:Pixel 7:34"
    seed_bytes = seed.encode("utf-8")
    device_hash = hashlib.sha256(seed_bytes).hexdigest()
    client_label = derive_client_label(seed_bytes)
    route = "/v1/soul/echo/fragment"

    print(f"[*] Device Hash:  {device_hash}")
    print(f"[*] Client Label: {client_label}")
    print(f"[*] Route:        {route}")

    challenge_url = f"{BASE_URL}{route}"
    params = {"device": device_hash, "client": client_label}
    print(f"[*] Requesting challenge from {challenge_url}...")
    
    resp = requests.get(challenge_url, params=params, timeout=10)
    assert resp.status_code == 200, f"Challenge request failed: {resp.text}"
    chal = resp.json()
    
    ticket = chal["ticket"]
    nonce = chal["nonce"]
    difficulty = chal.get("difficulty", 20)
    print(f"[+] Received ticket: {ticket}, nonce: {nonce}, difficulty: {difficulty}")

    prefix = f"{client_label}:{ticket}:{nonce}:{device_hash}".encode("ascii")
    counter = solve_pow(prefix, difficulty=difficulty, rounds=3)

    payload = {
        "ticket": ticket,
        "device": device_hash,
        "client": client_label,
        "counter": counter
    }
    print("[*] Submitting proof of work...")
    sol_resp = requests.post(challenge_url, json=payload, timeout=10)
    print(f"[!] Server response ({sol_resp.status_code}): {sol_resp.text}")
    
    data = sol_resp.json()
    if data.get("status") == "awakened":
        print(f"\n[+] FLAG: {data.get('message')}\n")

if __name__ == "__main__":
    run()
