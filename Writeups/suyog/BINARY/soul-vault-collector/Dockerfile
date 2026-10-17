FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends socat gcc make libc6-dev && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf

WORKDIR /home/ctf

# Copy source and Makefile to build within exact container libc environment
COPY src/ /home/ctf/src/
COPY Makefile /home/ctf/Makefile

RUN make && \
    rm -rf /home/ctf/src /home/ctf/Makefile && \
    echo "OWASP{S0ul_St0ne_C0ll3ct0r_UAF_Aw4k3n3d}" > /home/ctf/flag.txt && \
    chmod 444 /home/ctf/flag.txt && \
    chmod 755 /home/ctf/challenge/soul_vault && \
    chown -R root:ctf /home/ctf

USER ctf
EXPOSE 1338

CMD ["socat", "TCP-LISTEN:1338,reuseaddr,fork", "EXEC:/home/ctf/challenge/soul_vault,pty,stderr"]
