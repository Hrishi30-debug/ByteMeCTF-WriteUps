#include "soul.h"
#include <string.h>

/*
 * soul_resonance computes the Astral Soul Resonance value.
 * Combines the sacrifice name with the 24-bit resonance token
 * through a non-linear cryptographic permutation.
 */
uint32_t soul_resonance(const char *sacrifice, uint32_t token) {
    uint32_t h = 0x5A17F00DU;
    for (const char *p = sacrifice; *p; p++) {
        h = ((h * 31U + (uint8_t)*p) ^ 0x9E3779B9U);
    }

    uint32_t state = (h ^ token);
    for (int i = 0; i < 4; i++) {
        state = (state ^ (state >> 15)) * 0x85EBCA6BU;
        state = (state ^ (state >> 13)) * 0xC2B2AE35U;
        state = (state ^ (state >> 16));
        state = (state + token);
    }
    return state;
}

/*
 * verify_sacrifice_name checks if the offering matches the expected sacrifice.
 * Compares against obfuscated masked bytes so "GAMORA" is not exposed in plaintext.
 */
int verify_sacrifice_name(const char *name) {
    if (!name || strlen(name) != 6) {
        return 0;
    }
    static const uint8_t xor_keys[6] = {0x5A, 0x6B, 0x7C, 0x8D, 0x9E, 0xAF};
    for (int i = 0; i < 6; i++) {
        uint8_t unmasked = (uint8_t)name[i] ^ xor_keys[i];
        if (unmasked != SACRIFICE_HASH_MASK[i]) {
            return 0;
        }
    }
    return 1;
}
