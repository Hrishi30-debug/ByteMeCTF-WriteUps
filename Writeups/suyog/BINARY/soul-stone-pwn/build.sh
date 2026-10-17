#!/bin/bash
set -e

mkdir -p challenge
gcc src/soul.c -o challenge/soul -fno-stack-protector -no-pie -Wno-implicit-function-declaration
chmod 755 challenge/soul

echo "[+] Built challenge/soul successfully."
