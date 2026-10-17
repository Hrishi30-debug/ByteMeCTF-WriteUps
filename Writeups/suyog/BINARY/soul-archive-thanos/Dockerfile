FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends socat gcc make libc6-dev && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf

WORKDIR /home/ctf

COPY src/ /home/ctf/src/
COPY Makefile /home/ctf/Makefile

RUN make && \
    rm -rf /home/ctf/src /home/ctf/Makefile && \
    chmod 755 /home/ctf/challenge/soul_archive && \
    chown -R root:ctf /home/ctf

USER ctf
EXPOSE 1339

CMD ["socat", "TCP-LISTEN:1339,reuseaddr,fork", "EXEC:/home/ctf/challenge/soul_archive,pty,stderr"]
