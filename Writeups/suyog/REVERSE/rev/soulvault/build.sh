#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
SRC_DIR="${SCRIPT_DIR}/src"

echo "=== Building SoulVault CTF Challenge ==="

mkdir -p "${DIST_DIR}"

GO_BIN="$(command -v go || echo "/usr/local/go/bin/go")"
if ! command -v "${GO_BIN}" >/dev/null 2>&1; then
    echo "[-] Error: Go compiler not found." >&2
    exit 1
fi

echo "[*] Using Go compiler: $("${GO_BIN}" version)"
echo "[*] Compiling stripped release binary..."

(
    cd "${SRC_DIR}"
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 "${GO_BIN}" build \
        -trimpath \
        -ldflags="-s -w" \
        -o "${DIST_DIR}/soulvault" \
        .
)

chmod +x "${DIST_DIR}/soulvault"

echo "[+] Binary built successfully: ${DIST_DIR}/soulvault"
file "${DIST_DIR}/soulvault"

echo "[*] Auditing binary for leaked plaintext flags..."
if strings "${DIST_DIR}/soulvault" | grep -iE 'OWASP\{' ; then
    echo "[-] SECURITY AUDIT FAILED: Plaintext flag detected in strings!" >&2
    exit 1
fi
echo "[+] Security audit passed: No plaintext flags found."
echo "=== Build Complete ==="
