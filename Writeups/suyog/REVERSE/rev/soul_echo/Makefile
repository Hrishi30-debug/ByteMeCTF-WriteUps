.PHONY: all build solve test clean

all: build

build:
	@bash build.sh

solve: build
	@bash organizer/solve.sh dist/soul_echo

test: build
	@printf "3\n" | ./dist/soul_echo | grep -q "OWASP{" && echo "[+] Test Passed: Story revealed flag."

clean:
	@rm -rf dist/soul_echo
