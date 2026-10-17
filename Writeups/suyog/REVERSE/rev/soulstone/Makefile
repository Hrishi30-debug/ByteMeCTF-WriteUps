.PHONY: all build solve test clean

all: build

build:
	@bash build.sh

solve: build
	@python3 organizer/solve.py

test: build
	@echo "[*] Testing incorrect sacrifice rejection:"
	@! printf "SOUL{THANOS:123456}\n" | ./dist/soulstone >/dev/null 2>&1 && echo "[+] Successfully rejected incorrect sacrifice."
	@echo "[*] Testing incorrect resonance token rejection:"
	@! printf "SOUL{GAMORA:000000}\n" | ./dist/soulstone >/dev/null 2>&1 && echo "[+] Successfully rejected incorrect token."
	@echo "[*] Testing correct sacred offering acceptance:"
	@printf "SOUL{GAMORA:A73D91}\n" | ./dist/soulstone | grep -q "OWASP{" && echo "[+] Successfully accepted offering and unlocked the Soul Stone!"

clean:
	@rm -rf dist/soulstone organizer/solve_c
