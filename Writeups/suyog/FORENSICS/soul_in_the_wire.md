# The Soul in the Wire (Forensics, Hard)

**Author:** Suyog Jadhav  
**Category:** Forensics  
**Difficulty:** Hard  

## Challenge Description

> “The Soul Stone does not reveal itself to those who merely look. It reveals itself to those who understand what lies beneath.”  
>  
> A mysterious network capture was recovered from a compromised system. Buried beneath hundreds of megabytes of seemingly meaningless traffic lies a fragmented message.  
>  
> Several traces appear to contain possible flags, but not everything you find can be trusted. Six fragments of the truth have been scattered across different network conversations, each hiding in a different aspect of the traffic.  
>  
> The payload may deceive you. The metadata remembers.  
>  
> Follow the fragments, reconstruct the message, and uncover the Soul Stone's secret.  
>  
> **Flag Format:** `OWASP{...}`

**Attachment:** [`soul_stone.pcap`](https://drive.google.com/file/d/11M_2j3q_NjmnAh5X_gv3ig_sVqyunnSS/view?usp=sharing)

## Summary

The challenge provides a large network capture (`soul_stone.pcap`) filled with decoys and background traffic. Naive string searches on packet payloads only expose misleading fake flags. Solving the challenge requires extracting six covert communication fragments hidden across different layer 3/4 network metadata and covert channels: **Timing** (DNS query intervals), **Identity** (ICMP identifier headers), **Order** (TCP sequence ordering), **Size** (UDP packet lengths), **Direction** (reverse TCP server-to-client flows), and **Absence** (gaps in expected TCP sequence numbers). Reconstructing these fragments reveals the true hidden message: `THE SOUL IS FOUND IN THE METADATA`.

## Flag

```
OWASP{THE_SOUL_IS_FOUND_IN_THE_METADATA}
```

---

## Step 1 — Initial PCAP Reconnaissance

We begin by assessing the scope and composition of the provided packet capture:

```bash
capinfos soul_stone.pcap
```

Next, we view the overall protocol distribution across the capture:

```bash
tshark -r soul_stone.pcap -q -z io,phs
```

The capture contains a high volume of interleaved traffic across multiple protocols:
- **ARP**
- **DNS**
- **TCP**
- **UDP**
- **ICMP**

Because the file contains thousands of packets of ambient network traffic, manually inspecting streams without specific filters is impractical.

![Protocol Breakdown and Capture Overview](resources/recon_protocols.png)

---

## Step 2 — Identify Suspicious Endpoints & Filter Decoy Flags

### 1. Identifying Communicating Hosts
To isolate the core interaction, we enumerate conversation endpoints by packet volume:

```bash
tshark -r soul_stone.pcap -T fields -e ip.src -e ip.dst 2>/dev/null | sort | uniq -c | sort -nr | head -20
```

From this analysis, we identify the victim endpoint and the suspicious command-and-control (C2) server:
- **Victim IP:** `192.168.56.103`
- **Suspicious Host / C2:** `10.13.37.66`

Confirming the interaction stream:

```bash
tshark -r soul_stone.pcap -Y 'ip.addr==10.13.37.66' -T fields -e frame.number -e frame.time_relative -e ip.src -e ip.dst -e frame.protocols | head
```

This confirms an active channel between `192.168.56.103` and `10.13.37.66`.

### 2. Discarding Decoy Payload Flags
Running a generic string search for the flag format produces multiple candidates:

```bash
strings soul_stone.pcap | grep -oE 'OWASP\{[^}]+\}'
```

Output:
```
OWASP{THE_STONE_IS_WITHIN}
OWASP{NOT_THE_SOUL}
OWASP{YOU_FOUND_A_DECOY}
OWASP{THE_PACKET_LIES}
OWASP{WRONG_TIMELINE}
```

As the challenge prompt warns (*"The payload may deceive you. The metadata remembers."*), all plaintext strings placed inside packet payloads are intentional decoys. The actual data is exfiltrated through network packet metadata and covert channels.

![Host Identification and Decoy Strings](resources/suspicious_hosts_decoys.png)

---

## Step 3 — Fragment 1: DNS Query Intervals (Timing)

Looking for covert DNS tunneling or anomaly traffic associated with the challenge domain:

```bash
tshark -r soul_stone.pcap -Y 'dns.qry.name contains "soul.example.com"' -T fields -e frame.number -e frame.time_relative -e dns.qry.name
```

Output:
```
207291 500000.000000000    fragment-0.soul.example.com
207292 500000.350000000    fragment-1.soul.example.com
207293 500000.700000000    fragment-2.soul.example.com
207294 500000.820000000    fragment-3.soul.example.com
207295 500000.940000000    fragment-4.soul.example.com
```

The queried subdomains (`fragment-0`, `fragment-1`, etc.) carry no payload themselves. Instead, the covert channel is a **timing channel**: the relative time deltas between successive queries modulate the transmission.

![Fragment 1 — DNS Query Timing](resources/fragment1_dns_timing.png)

- **Fragment 1:** `THE`

---

## Step 4 — Fragment 2: ICMP Identifier Field (Identity)

Next, we inspect ICMP Echo Requests sent from the victim host `192.168.56.103` to `10.13.37.66`:

```bash
tshark -r soul_stone.pcap -Y 'icmp.type==8 && ip.src==192.168.56.103 && ip.dst==10.13.37.66' -T fields -e frame.number -e icmp.ident -e icmp.seq
```

Output:
```
207296 83 1
207297 79 2
207298 85 3
207299 76 4
```

While the ICMP data payloads contain standard padding bytes, the 16-bit ICMP Identifier (`icmp.ident`) field contains decimal ASCII values:

- `83` $\rightarrow$ `S`
- `79` $\rightarrow$ `O`
- `85` $\rightarrow$ `U`
- `76` $\rightarrow$ `L`

![Fragment 2 — ICMP Identifier Field](resources/fragment2_icmp_ident.png)

- **Fragment 2:** `SOUL`

---

## Step 5 — Fragment 3: TCP Sequence Ordering (Order)

Examining TCP traffic destined for port `9001`:

```bash
tshark -r soul_stone.pcap -Y 'tcp.port==9001' -T fields -e frame.number -e tcp.seq
```

Output:
```
207300 1
207301 2
```

The TCP conversation on port 9001 modulates information into sequence progression and ordering, yielding:

![Fragment 3 — TCP Sequence Ordering](resources/fragment3_tcp_order.png)

- **Fragment 3:** `IS`

---

## Step 6 — Fragment 4: UDP Packet Lengths (Size)

Inspecting UDP packets destined for port `7001`:

```bash
tshark -r soul_stone.pcap -Y 'udp.dstport==7001' -T fields -e udp.length
```

Output:
```
1024
1033
1039
1032
1022
```

![Fragment 4 — UDP Raw Packet Lengths](resources/fragment4_udp_raw.png)

The packet size is used as a storage channel. Each character is encoded by adding a fixed offset of $954$ bytes to its ASCII code (accounting for UDP header and generator baseline):

$$\text{ASCII} = \text{udp.length} - 954$$

- $1024 - 954 = 70 \rightarrow \mathbf{F}$
- $1033 - 954 = 79 \rightarrow \mathbf{O}$
- $1039 - 954 = 85 \rightarrow \mathbf{U}$
- $1032 - 954 = 78 \rightarrow \mathbf{N}$
- $1022 - 954 = 68 \rightarrow \mathbf{D}$

Automating the extraction in Bash:

```bash
tshark -r soul_stone.pcap -Y 'udp.dstport==7001' -T fields -e udp.length | while read x; do printf "\\$(printf '%03o' $((x - 954)))"; done; echo
```

Output:
```
FOUND
```

![Fragment 4 — UDP Packet Lengths](resources/fragment4_udp_length.png)

- **Fragment 4:** `FOUND`

---

## Step 7 — Fragment 5: Reverse TCP Direction & Timing (Direction)

Investigating inbound traffic originating from C2 port `8443` directed back to the victim host:

```bash
tshark -r soul_stone.pcap -Y 'ip.src==10.13.37.66 && ip.dst==192.168.56.103 && tcp.port==8443' -T fields -e frame.number -e tcp.seq -e frame.time_relative
```

Output:
```
207307 1 500089.560000000
207308 1 500090.860000000
```

Unlike normal egress exfiltration, this fragment utilizes reverse-direction server responses and sequence timing:

![Fragment 5 — Reverse TCP Direction](resources/fragment5_reverse_tcp.png)

- **Fragment 5:** `IN`

---

## Step 8 — Fragment 6: The Missing TCP Sequence Gap (Absence)

Finally, we inspect traffic directed to TCP port `9999`:

```bash
tshark -r soul_stone.pcap -Y 'tcp.port==9999' -T fields -e frame.number -e tcp.seq
```

Output:
```
207309 1
207310 101
207311 301
207312 401
```

Examining the sequence counter reveals an intentional gap:
- Frame `207309` has sequence `1`
- Frame `207310` has sequence `101`
- Frame `207311` jumps to `301`
- Frame `207312` has sequence `401`

Sequence number `201` is conspicuously absent. This deliberate negative space / transmission gap completes the clue chain pointing to `THE METADATA`.

![Fragment 6 — Missing TCP Sequence Gap](resources/fragment6_missing_packet.png)

---

## Step 9 — Reconstructing the Soul Stone Message

Combining the 6 recovered fragments:

| Fragment # | Channel Modality | Extracted Value |
|:---:|:---:|:---:|
| 1 | **Timing** (DNS query intervals) | `THE` |
| 2 | **Identity** (ICMP identifier headers) | `SOUL` |
| 3 | **Order** (TCP sequence ordering) | `IS` |
| 4 | **Size** (UDP packet lengths) | `FOUND` |
| 5 | **Direction** (Reverse C2 flow) | `IN` |
| 6 | **Absence** (Missing sequence gap) | `THE METADATA` |

The reconstructed message reads:

```
THE SOUL IS FOUND IN THE METADATA
```

Wrapping this string into the specified flag format:

```
OWASP{THE_SOUL_IS_FOUND_IN_THE_METADATA}
```

---

## Architecture of the Challenge

```
                         SOUL STONE PCAP
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
         Packet Payloads               Packet Metadata
        (Noise & Decoys)               (Covert Channels)
        - NOT_THE_SOUL                        │
        - THE_PACKET_LIES                     ├─ [Timing]     DNS query deltas   → THE
        - WRONG_TIMELINE                      ├─ [Identity]   ICMP ident fields  → SOUL
                                              ├─ [Order]      TCP port 9001 seq  → IS
                                              ├─ [Size]       UDP 7001 lengths   → FOUND
                                              ├─ [Direction]  TCP 8443 reverse   → IN
                                              └─ [Absence]    TCP 9999 seq drop  → THE METADATA
                                                      │
                                                      ▼
                                   THE SOUL IS FOUND IN THE METADATA
                                                      │
                                                      ▼
                                  OWASP{THE_SOUL_IS_FOUND_IN_THE_METADATA}
```

---

## Solution Summary

| Field | Value |
|---|---|
| **Challenge** | The Soul in the Wire |
| **Category** | Forensics (Network Covert Channels) |
| **Difficulty** | Hard |
| **Victim IP** | `192.168.56.103` |
| **C2 IP** | `10.13.37.66` |
| **Key Protocols** | DNS, ICMP, TCP, UDP |
| **Exfiltration Types** | Storage channels (ident, length), Timing channels, Protocol anomalies |
| **Final Flag** | `OWASP{THE_SOUL_IS_FOUND_IN_THE_METADATA}` |

---

## Forensics Methodology & Covert Channels

1. **Storage vs. Timing Channels:**  
   Covert channels in network forensics broadly split into two types:
   - **Storage Channels:** Modifying existing header fields without violating RFC standards (e.g., using `icmp.ident` to hold character ASCII codes, or modulating `udp.length` to represent numerical values).
   - **Timing Channels:** Modulating inter-arrival times between valid packets (e.g., deliberate delays in DNS lookups).
2. **Decoy Rejection & Threat Emulation:**  
   Adversaries frequently insert canary strings or fake flags to waste forensic investigators' time. String analysis (`strings` / regex) must be complemented by traffic pattern and flow analysis.
3. **Negative Information (Absence):**  
   Missing packets in TCP sessions with monotonic sequence steps indicate intentional suppression, serving as a binary or positional signal.

---

## Tools Used

- **`tshark`**: Command-line packet analysis, custom display filters, and protocol field extraction.
- **`capinfos`**: Quick metadata statistics and overview of the capture file.
- **`strings` / `grep`**: Identification and filtration of decoy payload flags.
- **`bash` (coreutils)**: Inline ASCII translation and shell automation.

---

## Timeline

| Step | Action | Result |
|:---:|---|---|
| 1 | Ran `capinfos` and `tshark -z io,phs` | Established capture scope across DNS, ICMP, TCP, and UDP |
| 2 | Enumerated communication endpoints | Pinpointed victim (`192.168.56.103`) and C2 (`10.13.37.66`) |
| 3 | Filtered payload decoys | Discarded misleading plaintext flags found via `strings` |
| 4 | Analyzed DNS queries to `soul.example.com` | Recovered Fragment 1: `THE` via timing deltas |
| 5 | Extracted ICMP echo request `icmp.ident` | Decoded ASCII codes for Fragment 2: `SOUL` |
| 6 | Inspected TCP sequence on port 9001 | Extracted Fragment 3: `IS` |
| 7 | Decoded UDP packet lengths on port 7001 | Subtracted 954-byte offset to recover Fragment 4: `FOUND` |
| 8 | Analyzed reverse TCP stream on port 8443 | Extracted Fragment 5: `IN` |
| 9 | Examined TCP port 9999 sequence progression | Detected missing sequence gap (Fragment 6 / `THE METADATA`) |
| 10 | Reconstructed fragments into complete phrase | Obtained flag: `OWASP{THE_SOUL_IS_FOUND_IN_THE_METADATA}` |
