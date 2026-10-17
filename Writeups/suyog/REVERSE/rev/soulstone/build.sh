#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
SRC_DIR="${SCRIPT_DIR}/src"

echo "=== Building SoulStone CTF Challenge ==="

mkdir -p "${DIST_DIR}"

if ! command -v gcc >/dev/null 2>&1; then
    echo "[-] Error: GCC compiler not found." >&2
    exit 1
fi

echo "[*] Compiling stripped release binary with GCC..."
gcc -O2 -Wall -Wextra -s -fno-ident \
    -o "${DIST_DIR}/soulstone" \
    "${SRC_DIR}/main.c" \
    "${SRC_DIR}/resonance.c" \
    "${SRC_DIR}/crypto.c"

chmod +x "${DIST_DIR}/soulstone"

echo "[+] Binary built successfully: ${DIST_DIR}/soulstone"
file "${DIST_DIR}/soulstone"

echo "[*] Auditing binary for leaked plaintext flags and secrets..."
if strings "${DIST_DIR}/soulstone" | grep -iE 'OWASP\{|GAMORA|A73D91'; then
    echo "[-] SECURITY AUDIT FAILED: Plaintext secret detected in binary!" >&2
    exit 1
fi

echo "[+] Security audit passed: No plaintext secrets found."
echo "=== Build Complete ==="
