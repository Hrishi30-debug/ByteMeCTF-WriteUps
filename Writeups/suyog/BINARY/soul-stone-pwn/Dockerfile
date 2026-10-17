FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends socat gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf

WORKDIR /home/ctf

COPY src/soul.c /tmp/soul.c
RUN gcc /tmp/soul.c -o /home/ctf/soul -fno-stack-protector -no-pie -Wno-implicit-function-declaration && \
    rm /tmp/soul.c && \
    chmod 755 /home/ctf/soul && \
    chown -R root:ctf /home/ctf

USER ctf
EXPOSE 1337

CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:/home/ctf/soul,pty,stderr"]
