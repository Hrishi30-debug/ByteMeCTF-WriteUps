#include "crypto.h"
#include <string.h>

/* ========================================================================= */
/* SHA-256 Implementation (FIPS 180-4)                                       */
/* ========================================================================= */

#define ROTR32(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define CH(x, y, z)  (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define EP0(x)       (ROTR32(x, 2) ^ ROTR32(x, 13) ^ ROTR32(x, 22))
#define EP1(x)       (ROTR32(x, 6) ^ ROTR32(x, 11) ^ ROTR32(x, 25))
#define SIG0(x)      (ROTR32(x, 7) ^ ROTR32(x, 18) ^ ((x) >> 3))
#define SIG1(x)      (ROTR32(x, 17) ^ ROTR32(x, 19) ^ ((x) >> 10))

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static void sha256_transform(sha256_ctx *ctx, const uint8_t data[64]) {
    uint32_t a, b, c, d, e, f, g, h, t1, t2, m[64];
    for (int i = 0, j = 0; i < 16; ++i, j += 4)
        m[i] = ((uint32_t)data[j] << 24) | ((uint32_t)data[j + 1] << 16) |
               ((uint32_t)data[j + 2] << 8) | ((uint32_t)data[j + 3]);
    for (int i = 16; i < 64; ++i)
        m[i] = SIG1(m[i - 2]) + m[i - 7] + SIG0(m[i - 15]) + m[i - 16];

    a = ctx->state[0];
    b = ctx->state[1];
    c = ctx->state[2];
    d = ctx->state[3];
    e = ctx->state[4];
    f = ctx->state[5];
    g = ctx->state[6];
    h = ctx->state[7];

    for (int i = 0; i < 64; ++i) {
        t1 = h + EP1(e) + CH(e, f, g) + K[i] + m[i];
        t2 = EP0(a) + MAJ(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }

    ctx->state[0] += a;
    ctx->state[1] += b;
    ctx->state[2] += c;
    ctx->state[3] += d;
    ctx->state[4] += e;
    ctx->state[5] += f;
    ctx->state[6] += g;
    ctx->state[7] += h;
}

void sha256_init(sha256_ctx *ctx) {
    ctx->state[0] = 0x6a09e667;
    ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372;
    ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f;
    ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab;
    ctx->state[7] = 0x5be0cd19;
    ctx->count = 0;
}

void sha256_update(sha256_ctx *ctx, const uint8_t *data, size_t len) {
    size_t buffer_len = ctx->count % 64;
    ctx->count += len;

    if (buffer_len > 0) {
        size_t copy_len = 64 - buffer_len;
        if (len < copy_len) {
            memcpy(ctx->buffer + buffer_len, data, len);
            return;
        }
        memcpy(ctx->buffer + buffer_len, data, copy_len);
        sha256_transform(ctx, ctx->buffer);
        data += copy_len;
        len -= copy_len;
    }

    while (len >= 64) {
        sha256_transform(ctx, data);
        data += 64;
        len -= 64;
    }

    if (len > 0) {
        memcpy(ctx->buffer, data, len);
    }
}

void sha256_final(sha256_ctx *ctx, uint8_t hash[32]) {
    uint8_t pad[64] = {0x80};
    size_t buffer_len = ctx->count % 64;
    size_t pad_len = (buffer_len < 56) ? (56 - buffer_len) : (120 - buffer_len);
    uint64_t bits_count = ctx->count * 8;

    uint8_t bits_be[8];
    for (int i = 0; i < 8; i++) {
        bits_be[7 - i] = (uint8_t)(bits_count >> (i * 8));
    }

    sha256_update(ctx, pad, pad_len);
    sha256_update(ctx, bits_be, 8);

    for (int i = 0; i < 8; i++) {
        hash[i * 4]     = (uint8_t)(ctx->state[i] >> 24);
        hash[i * 4 + 1] = (uint8_t)(ctx->state[i] >> 16);
        hash[i * 4 + 2] = (uint8_t)(ctx->state[i] >> 8);
        hash[i * 4 + 3] = (uint8_t)(ctx->state[i]);
    }
}

void sha256_hash(const uint8_t *data, size_t len, uint8_t hash[32]) {
    sha256_ctx ctx;
    sha256_init(&ctx);
    sha256_update(&ctx, data, len);
    sha256_final(&ctx, hash);
}

/* ========================================================================= */
/* HMAC-SHA256 Implementation (RFC 2104)                                     */
/* ========================================================================= */

void hmac_sha256(const uint8_t *key, size_t key_len,
                 const uint8_t *data, size_t data_len,
                 uint8_t out[32]) {
    uint8_t k[64];
    memset(k, 0, sizeof(k));

    if (key_len > 64) {
        sha256_hash(key, key_len, k);
    } else {
        memcpy(k, key, key_len);
    }

    uint8_t ipad[64];
    uint8_t opad[64];
    for (int i = 0; i < 64; i++) {
        ipad[i] = k[i] ^ 0x36;
        opad[i] = k[i] ^ 0x5C;
    }

    sha256_ctx inner;
    sha256_init(&inner);
    sha256_update(&inner, ipad, 64);
    sha256_update(&inner, data, data_len);
    uint8_t inner_hash[32];
    sha256_final(&inner, inner_hash);

    sha256_ctx outer;
    sha256_init(&outer);
    sha256_update(&outer, opad, 64);
    sha256_update(&outer, inner_hash, 32);
    sha256_final(&outer, out);
}

/* ========================================================================= */
/* ChaCha20 Implementation (RFC 7539 / 8439)                                 */
/* ========================================================================= */

#define ROTL32(v, n) (((v) << (n)) | ((v) >> (32 - (n))))
#define CHACHA_QR(a, b, c, d) \
    a += b; d ^= a; d = ROTL32(d, 16); \
    c += d; b ^= c; b = ROTL32(b, 12); \
    a += b; d ^= a; d = ROTL32(d, 8);  \
    c += d; b ^= c; b = ROTL32(b, 7);

static uint32_t load32_le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static void store32_le(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

void chacha20_init(chacha20_ctx *ctx, const uint8_t key[32], const uint8_t nonce[12], uint32_t counter) {
    ctx->state[0] = 0x61707865;
    ctx->state[1] = 0x3320646e;
    ctx->state[2] = 0x79622d32;
    ctx->state[3] = 0x6b206574;

    for (int i = 0; i < 8; i++) {
        ctx->state[4 + i] = load32_le(key + i * 4);
    }

    ctx->state[12] = counter;
    for (int i = 0; i < 3; i++) {
        ctx->state[13 + i] = load32_le(nonce + i * 4);
    }
}

static void chacha20_block(const uint32_t in_state[16], uint8_t out[64]) {
    uint32_t s[16];
    memcpy(s, in_state, sizeof(s));

    for (int i = 0; i < 10; i++) {
        CHACHA_QR(s[0], s[4], s[8],  s[12]);
        CHACHA_QR(s[1], s[5], s[9],  s[13]);
        CHACHA_QR(s[2], s[6], s[10], s[14]);
        CHACHA_QR(s[3], s[7], s[11], s[15]);

        CHACHA_QR(s[0], s[5], s[10], s[15]);
        CHACHA_QR(s[1], s[6], s[11], s[12]);
        CHACHA_QR(s[2], s[7], s[8],  s[13]);
        CHACHA_QR(s[3], s[4], s[9],  s[14]);
    }

    for (int i = 0; i < 16; i++) {
        store32_le(out + i * 4, s[i] + in_state[i]);
    }
}

void chacha20_crypt(chacha20_ctx *ctx, const uint8_t *in, uint8_t *out, size_t len) {
    uint8_t block[64];
    while (len > 0) {
        chacha20_block(ctx->state, block);
        ctx->state[12]++; /* Increment block counter */

        size_t chunk = (len < 64) ? len : 64;
        for (size_t i = 0; i < chunk; i++) {
            out[i] = in[i] ^ block[i];
        }

        in += chunk;
        out += chunk;
        len -= chunk;
    }
}
