.PHONY: all build solve test clean

all: build

build:
	@bash build.sh

solve: build
	@python3 organizer/solve.py

test: build
	@echo "[*] Testing incorrect key rejection:"
	@! printf "WRONG_KEY\n" | ./dist/soulvault >/dev/null 2>&1 && echo "[+] Successfully rejected incorrect key."
	@echo "[*] Testing correct key acceptance:"
	@printf "SV-8F4C-3B91-7E02-A6D5-C918-B472\n" | ./dist/soulvault | grep -q "OWASP{" && echo "[+] Successfully accepted valid key and printed flag."

clean:
	@rm -rf dist/soulvault
