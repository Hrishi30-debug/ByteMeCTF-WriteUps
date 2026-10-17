CC = gcc
CFLAGS = -O0 -fstack-protector-strong -fPIE -pie -Wl,-z,relro,-z,now -z noexecstack -D_FORTIFY_SOURCE=2
SRC = src/soul_vault.c
BIN = challenge/soul_vault

all: $(BIN)

$(BIN): $(SRC)
	mkdir -p challenge
	$(CC) $(CFLAGS) $(SRC) -o $(BIN)
	chmod 755 $(BIN)

clean:
	rm -rf challenge/soul_vault

.PHONY: all clean
