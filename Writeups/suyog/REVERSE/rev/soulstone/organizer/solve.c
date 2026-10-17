#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define TARGET_RESONANCE_TAG 0xE7F841B8U

static inline uint32_t soul_resonance_fast(uint32_t h, uint32_t token) {
    uint32_t state = (h ^ token);
    for (int i = 0; i < 4; i++) {
        state = (state ^ (state >> 15)) * 0x85EBCA6BU;
        state = (state ^ (state >> 13)) * 0xC2B2AE35U;
        state = (state ^ (state >> 16));
        state = (state + token);
    }
    return state;
}

int main(void) {
    printf("============================================================\n");
    printf("        SOULSTONE REVERSE ENGINEERING BRUTE-FORCE SOLVER\n");
    printf("============================================================\n\n");

    // 1. Recover Sacrifice Name by unmasking
    const uint8_t mask[6] = {0x47 ^ 0x5A, 0x41 ^ 0x6B, 0x4D ^ 0x7C, 0x4F ^ 0x8D, 0x52 ^ 0x9E, 0x41 ^ 0xAF};
    const uint8_t keys[6] = {0x5A, 0x6B, 0x7C, 0x8D, 0x9E, 0xAF};
    char sacrifice[7];
    for (int i = 0; i < 6; i++) {
        sacrifice[i] = (char)(mask[i] ^ keys[i]);
    }
    sacrifice[6] = '\0';
    printf("[*] Recovered Sacrifice Name: %s\n", sacrifice);

    // Precompute prefix hash
    uint32_t h = 0x5A17F00DU;
    for (const char *p = sacrifice; *p; p++) {
        h = ((h * 31U + (uint8_t)*p) ^ 0x9E3779B9U);
    }
    printf("[*] Precomputed Prefix Hash:  0x%08X\n", h);

    // 2. High-speed 24-bit Brute Force search
    printf("[*] Brute-forcing 24-bit resonance token (0x000000 to 0xFFFFFF)...\n");
    clock_t t0 = clock();

    uint32_t found_token = 0;
    int found = 0;

    for (uint32_t token = 0; token <= 0xFFFFFFU; token++) {
        if (soul_resonance_fast(h, token) == TARGET_RESONANCE_TAG) {
            found_token = token;
            found = 1;
            break;
        }
    }

    clock_t t1 = clock();
    double elapsed = (double)(t1 - t0) / CLOCKS_PER_SEC;

    if (!found) {
        printf("[-] Failed to find matching token!\n");
        return 1;
    }

    printf("[+] Found matching token in %.4f seconds!\n", elapsed);
    printf("[+] Recovered Resonance Token: 0x%06X\n", found_token);
    printf("\n[+] Sacred Offering String: SOUL{%s:%06X}\n", sacrifice, found_token);

    return 0;
}
