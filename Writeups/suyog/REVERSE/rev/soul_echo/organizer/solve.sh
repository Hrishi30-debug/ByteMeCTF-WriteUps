#!/usr/bin/env bash
# Solver for Soul Echoes
TARGET="${1:-../dist/soul_echo}"

if [ ! -f "$TARGET" ]; then
    echo "[-] File $TARGET does not exist!"
    exit 1
fi

echo "[*] Extracting flag via strings..."
FLAG=$(strings "$TARGET" | grep -o 'OWASP{[^}]*}')

if [ -n "$FLAG" ]; then
    echo "[+] Found Flag: $FLAG"
    exit 0
else
    echo "[-] Flag not found!"
    exit 1
fi
