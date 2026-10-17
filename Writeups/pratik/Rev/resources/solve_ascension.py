kDelta = 0x9E3779B9

def rotl32(v, c):
    return ((v << c) | (v >> (32 - c))) & 0xFFFFFFFF

def derive_key(transcript):
    key = [0xC3A5C85C, 0xB492B66F, 0x9AE16A3B, 0x7F4A7C15]
    for i, byte in enumerate(transcript.encode('utf-8')):
        slot = i & 3
        next_val = key[(slot + 1) & 3]
        key[slot] ^= (byte + kDelta + (next_val << 6) + (next_val >> 2)) & 0xFFFFFFFF
        key[slot] = rotl32(key[slot], (i % 23) + 5)
        key[slot] = (key[slot] + i * 0x045D9F3B) & 0xFFFFFFFF
    return key

def decrypt_xtea_block(block, key):
    left = block[0] | (block[1] << 8) | (block[2] << 16) | (block[3] << 24)
    right = block[4] | (block[5] << 8) | (block[6] << 16) | (block[7] << 24)
    sum_val = (kDelta * 32) & 0xFFFFFFFF
    
    for _ in range(32):
        t_r = ((((left << 4) ^ (left >> 5)) + left) ^ (sum_val + key[(sum_val >> 11) & 3])) & 0xFFFFFFFF
        right = (right - t_r) & 0xFFFFFFFF
        sum_val = (sum_val - kDelta) & 0xFFFFFFFF
        t_l = ((((right << 4) ^ (right >> 5)) + right) ^ (sum_val + key[sum_val & 3])) & 0xFFFFFFFF
        left = (left - t_l) & 0xFFFFFFFF
        
    res = bytearray(8)
    for i in range(4):
        res[i] = (left >> (i * 8)) & 0xFF
        res[i + 4] = (right >> (i * 8)) & 0xFF
    return res

def solve():
    transcript = "A9yromem:B4moon:C2tpvm:D82620"
    print(f"[*] Transcript: {transcript}")
    
    key = derive_key(transcript)
    print(f"[*] Derived XTEA Key: {[hex(k) for k in key]}")
    
    ciphertext = bytes([
        31, 158, 20, 122, 141, 137, 168, 45, 240, 106, 95, 245, 69, 77,
        84, 118, 196, 207, 161, 254, 153, 120, 188, 149, 5, 239, 219, 28,
        41, 153, 245, 94, 96, 9, 107, 183, 189, 3, 93, 45
    ])
    iv = bytes([83, 65, 124, 25, 45, 136, 196, 6])
    
    prev = bytearray(iv)
    plaintext = bytearray()
    for offset in range(0, len(ciphertext), 8):
        chunk = ciphertext[offset:offset+8]
        dec = decrypt_xtea_block(chunk, key)
        plain_chunk = bytearray(dec[i] ^ prev[i] for i in range(8))
        plaintext.extend(plain_chunk)
        prev = bytearray(chunk)
        
    padding = plaintext[-1]
    unpadded = plaintext[:-padding]
    flag = unpadded.decode('utf-8')
    print(f"\n[+] Plaintext Flag: {flag}\n")
    return flag

if __name__ == "__main__":
    solve()
