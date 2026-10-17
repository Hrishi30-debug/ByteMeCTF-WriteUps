#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
SRC_DIR="${SCRIPT_DIR}/src"

echo "=== Building Soul Echoes CTF Challenge ==="

mkdir -p "${DIST_DIR}"

if ! command -v gcc >/dev/null 2>&1; then
    echo "[-] Error: GCC not found." >&2
    exit 1
fi

echo "[*] Compiling binary..."
gcc -O2 -Wall -Wextra \
    -o "${DIST_DIR}/soul_echo" \
    "${SRC_DIR}/main.c"

chmod +x "${DIST_DIR}/soul_echo"

echo "[+] Binary built successfully: ${DIST_DIR}/soul_echo"
file "${DIST_DIR}/soul_echo"

echo "[*] Testing strings extraction..."
strings "${DIST_DIR}/soul_echo" | grep -i "OWASP{"

echo "=== Build Complete ==="
