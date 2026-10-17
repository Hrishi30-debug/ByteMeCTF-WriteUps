#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "soul.h"

static void print_banner(void) {
    puts("╔═══════════════════════════════════════════════════════════════╗");
    puts("║                      THE ALTAR OF VORMIR                      ║");
    puts("║                    Trial of the Soul Stone                    ║");
    puts("╚═══════════════════════════════════════════════════════════════╝");
    puts("");
    puts("\"Welcome, traveler. Many have sought the Stone, but none");
    puts(" comprehend its price. An everlasting exchange is demanded:");
    puts(" A soul for a soul.");
    puts(" Name your true sacrifice and present the Astral Soul Resonance.\"");
    puts("");
}

int main(void) {
    print_banner();

    printf("Enter Sacred Offering (format: SOUL{<SACRIFICE>:<RESONANCE>}):\n> ");
    fflush(stdout);

    char input[128];
    if (!fgets(input, sizeof(input), stdin)) {
        puts("[-] Failed to read offering.");
        return 1;
    }

    // Strip trailing newlines
    size_t len = strlen(input);
    while (len > 0 && (input[len - 1] == '\n' || input[len - 1] == '\r')) {
        input[--len] = '\0';
    }

    // Check format SOUL{...}
    if (len < 10 || strncmp(input, "SOUL{", 5) != 0 || input[len - 1] != '}') {
        puts("[-] The Stonekeeper looks away: \"Your offering lacks the sacred form.\"");
        return 1;
    }

    // Extract inside SOUL{...}
    char inner[128];
    size_t inner_len = len - 6;
    memcpy(inner, input + 5, inner_len);
    inner[inner_len] = '\0';

    char *colon = strchr(inner, ':');
    if (!colon) {
        puts("[-] The Stonekeeper looks away: \"The offering is incomplete.\"");
        return 1;
    }

    *colon = '\0';
    char *sacrifice_str = inner;
    char *token_str = colon + 1;

    // 1. Verify Sacrifice Name
    if (!verify_sacrifice_name(sacrifice_str)) {
        puts("[-] The Stonekeeper shakes his head: \"That soul holds no weight in your heart.\"");
        return 1;
    }

    // 2. Parse 6-character hex token
    if (strlen(token_str) != 6) {
        puts("[-] The Stonekeeper shakes his head: \"The resonance key must be a 6-character astral seal.\"");
        return 1;
    }

    uint32_t token_val = 0;
    for (int i = 0; i < 6; i++) {
        char c = token_str[i];
        uint32_t nibble;
        if (c >= '0' && c <= '9') nibble = c - '0';
        else if (c >= 'A' && c <= 'F') nibble = c - 'A' + 10;
        else if (c >= 'a' && c <= 'f') nibble = c - 'a' + 10;
        else {
            puts("[-] The Stonekeeper sighs: \"The seal contains earthly corrupted glyphs.\"");
            return 1;
        }
        token_val = (token_val << 4) | nibble;
    }

    // 3. Verify Astral Soul Resonance (The Brute-Force Gate)
    uint32_t computed_resonance = soul_resonance(sacrifice_str, token_val);
    if (computed_resonance != TARGET_RESONANCE_TAG) {
        puts("[-] The Altar rumbles: \"The soul resonance is dissonant. The Stone remains sealed.\"");
        return 1;
    }

    // 4. Derive Cryptographic Keys
    // Master Key = SHA256(sacrifice + ":" + token_str_upper + ":" + ALTAR_SALT)
    char token_upper[7];
    for (int i = 0; i < 6; i++) {
        char c = token_str[i];
        if (c >= 'a' && c <= 'f') c = c - 'a' + 'A';
        token_upper[i] = c;
    }
    token_upper[6] = '\0';

    char kdf_buf[256];
    snprintf(kdf_buf, sizeof(kdf_buf), "%s:%s:%s", sacrifice_str, token_upper, ALTAR_SALT);

    uint8_t master_key[32];
    sha256_hash((const uint8_t *)kdf_buf, strlen(kdf_buf), master_key);

    // Derive ChaCha20 Key, Nonce, and HMAC Key
    uint8_t key_seed[64];
    memcpy(key_seed, master_key, 32);

    uint8_t chacha_key[32];
    uint8_t chacha_nonce[32];
    uint8_t hmac_key[32];

    memcpy(key_seed + 32, "::CIPHER_KEY", 12);
    sha256_hash(key_seed, 32 + 12, chacha_key);

    memcpy(key_seed + 32, "::NONCE", 7);
    sha256_hash(key_seed, 32 + 7, chacha_nonce);

    memcpy(key_seed + 32, "::HMAC_KEY", 10);
    sha256_hash(key_seed, 32 + 10, hmac_key);

    // 5. Authenticate Ciphertext with HMAC-SHA256
    uint8_t computed_mac[32];
    hmac_sha256(hmac_key, 32, ENCRYPTED_FLAG, CIPHERTEXT_LEN, computed_mac);

    if (memcmp(computed_mac, EXPECTED_HMAC, 32) != 0) {
        puts("[-] The void consumes your offering: Core cryptographic integrity check failed.");
        return 1;
    }

    // 6. Decrypt Flag
    uint8_t decrypted_flag[CIPHERTEXT_LEN + 1];
    chacha20_ctx cipher_ctx;
    chacha20_init(&cipher_ctx, chacha_key, chacha_nonce, 1);
    chacha20_crypt(&cipher_ctx, ENCRYPTED_FLAG, decrypted_flag, CIPHERTEXT_LEN);
    decrypted_flag[CIPHERTEXT_LEN] = '\0';

    // 7. Success presentation
    puts("");
    puts("[+] The clouds part above the precipice as an amber radiance engulfs the sky.");
    puts("[+] A tear falls into the abyss. The everlasting exchange is complete.");
    puts("[+] You awaken in the shallow waters, holding that which you paid dearly for.");
    printf("[+] Flag: %s\n", (char *)decrypted_flag);

    // Zeroize decrypted memory
    memset(decrypted_flag, 0, sizeof(decrypted_flag));
    memset(master_key, 0, sizeof(master_key));
    memset(chacha_key, 0, sizeof(chacha_key));
    memset(hmac_key, 0, sizeof(hmac_key));

    return 0;
}
