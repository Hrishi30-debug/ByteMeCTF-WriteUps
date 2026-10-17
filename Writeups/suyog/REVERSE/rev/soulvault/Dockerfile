FROM golang:1.22-bullseye AS builder

WORKDIR /app
COPY src/ ./src/
COPY build.sh Makefile ./

RUN mkdir -p dist && \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
        -trimpath \
        -ldflags="-s -w" \
        -o dist/soulvault \
        ./src

# Verification step inside docker
RUN strings dist/soulvault | grep -i "OWASP{" && exit 1 || echo "Security check passed: No plaintext flag found."

FROM alpine:latest
WORKDIR /vault
COPY --from=builder /app/dist/soulvault /vault/soulvault
RUN chmod +x /vault/soulvault

ENTRYPOINT ["/vault/soulvault"]
