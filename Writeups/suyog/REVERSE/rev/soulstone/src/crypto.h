#ifndef SOUL_CRYPTO_H
#define SOUL_CRYPTO_H

#include <stdint.h>
#include <stddef.h>

/* SHA-256 Context */
typedef struct {
    uint32_t state[8];
    uint64_t count;
    uint8_t buffer[64];
} sha256_ctx;

void sha256_init(sha256_ctx *ctx);
void sha256_update(sha256_ctx *ctx, const uint8_t *data, size_t len);
void sha256_final(sha256_ctx *ctx, uint8_t hash[32]);
void sha256_hash(const uint8_t *data, size_t len, uint8_t hash[32]);

/* HMAC-SHA256 */
void hmac_sha256(const uint8_t *key, size_t key_len,
                 const uint8_t *data, size_t data_len,
                 uint8_t out[32]);

/* ChaCha20 Stream Cipher */
typedef struct {
    uint32_t state[16];
} chacha20_ctx;

void chacha20_init(chacha20_ctx *ctx, const uint8_t key[32], const uint8_t nonce[12], uint32_t counter);
void chacha20_crypt(chacha20_ctx *ctx, const uint8_t *in, uint8_t *out, size_t len);

#endif /* SOUL_CRYPTO_H */
