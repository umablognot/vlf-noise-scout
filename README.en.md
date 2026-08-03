# VLF Noise Scout

> **📡 Live broadcast window:** the station streams continuously from
> **3 to 10 August 2026** and will go **offline on 10 August 2026**. The code
> and documentation are permanent; you can build your own station any time.

**A homemade dual-channel VLF natural-radio receiving station with a live web stream.**
Built in a flat in Ankara, Türkiye, using a metal mop handle as the main antenna
and roughly €20 of components.

> Türkçe sürüm: [README.md](README.md)

---

## What it does

The radio pulses of lightning (*sferics*), their night-time ionospheric echoes
(*tweeks*) and the rare *whistlers* all live between 250 Hz and 12 kHz — inside
the **audio band**. No conventional radio is needed: the antenna signal is
sampled directly by a PC sound card.

This station provides:

- **Two independent channels:** a metal pole (main antenna) and a 10 cm reference probe
- **Adaptive noise cancellation:** interference heard by the reference probe is
  subtracted from the main channel (frequency-domain NLMS)
- **Live web stream:** seamless raw/clean comparison
- **Event-mode waterfall:** the steady noise floor is learned and subtracted,
  leaving only new impulses on screen
- **Look-back recording:** the last 60 seconds are continuously buffered
- **Live lightning map:** an embedded map showing where the sferics come from
  (data: the [Blitzortung.org](https://www.blitzortung.org/) volunteer network)
- **Distant-transmitter scan:** SNR measurement of known VLF stations at 96 kHz
  sampling — proves the chain works without waiting for luck

### Measured result

3 August 2026, daytime, Ankara — 60-second scan:

| Station | Frequency | SNR | Verdict |
|---|---:|---:|---|
| Alpha F1 🇷🇺 | 11.90 kHz | 12.3 dB | **DETECTED** |
| Alpha F2 🇷🇺 | 12.65 kHz | 11.7 dB | **DETECTED** |
| Alpha F3 🇷🇺 | 14.88 kHz | 8.6 dB | faint trace |
| HWU 🇫🇷 | 21.75 kHz | 8.0 dB | faint trace |
| GBZ 🇬🇧 | 19.58 kHz | 6.9 dB | faint trace |
| DHO38 🇩🇪 | 23.40 kHz | 6.6 dB | faint trace |
| TBB 🇹🇷 | 26.70 kHz | 6.6 dB | faint trace |
| NAA 🇺🇸 | 24.00 kHz | 5.8 dB | faint trace |
| ICV 🇮🇹 | 20.27 kHz | 5.1 dB | faint trace |

Alpha (RSDN-20) is a Russian navigation system; the others are naval submarine
communication transmitters. All are above human hearing — they are measured, not heard.

---

## Hardware

### Bill of materials

| Part | Qty | Note |
|---|---:|---|
| 2N5457 JFET (TO-92) | 4 | J201 substitute; 2 channels + spares |
| TL072 (DIP-8) | 2 | dual op-amp, 1 spare |
| 8-pin DIP socket | 2 | chips are socketed, never soldered directly |
| Resistor assortment (1/4W) | 1 | 20k, 510Ω, 100k, 1k, 1M, 10M used |
| 10 MΩ resistor | 4 | gate bias (2 in series = 20 MΩ) |
| 100k multi-turn trimpot (3006) | 2 | gain adjustment |
| 1 µF film capacitor | 6 | coupling / source bypass |
| 470 nF film | 2 | feedback |
| 100 nF MLCC | 2 | supply decoupling |
| 4.7 nF film | 2 | inter-stage coupling |
| 100 µF electrolytic | 4 | supply + Vmid filtering |
| 8×AA battery holder + cells | 1 | **12 V, batteries only** |
| Perfboard 5×10 cm | 2 | one for this project |
| 3.5 mm stereo plug (solder type) | 1 | to PC line input |
| Metal pole (mop handle) | 1 | main antenna |
| Thin wire ~10–40 cm | 1 | reference probe |
| Multimeter | 1 | **mandatory** |

### Circuit (per channel, built twice)

```
STAGE 1 — JFET preamp                    STAGE 2 — TL072 gain stage
                V+ (12V)                      from C4 ──┬──[+ TL072]──┬── 1k ── 1µF ──► Line In
                 │                                      │            │
               20k (R7)                              100k (R12)      ├── 100k trimpot ──┐
                 │                                      │            │                  │
                 ├──── 4.7nF (C4) ──► STAGE 2         Vmid       [− input] ─────────────┘
               Drain                                                 │
             ┌───┴───┐                                               └── 1k ── 470nF ── Vmid
Antenna ─1M──│ 2N5457│                    COMMON SUPPLY
        │    └───┬───┘                       V+ ──┬─ 10k ─┬─ 10k ─ GND     Vmid = V+/2
      20M      Source                             │       │
    (2x10M)      ├── 510Ω ── GND               100µF     Vmid ── 100µF ── GND
        │        └── 1µF  ── GND                  │
       GND                                       GND      V+ ── 100nF ── GND (close to TL072)
```

**Gain budget:** JFET stage ≈ +23 dB, TL072 stage ≈ +40 dB (trimmed) →
total ≈ **+63 dB**, and ≈ 0 dB at 50 Hz — mains is suppressed ~60 dB relative
to the band of interest.

**Bias rule:** drain voltage must sit at 40–70 % of V+ (4.8–8.4 V on a 12 V rail).
Too low → increase the source resistor; stuck at V+ → decrease it and re-check
the JFET pinout.

### Build order

1. Supply + Vmid → **measure** (V+ ≈ 12–13 V, Vmid ≈ half)
2. Channel 1 stage 1 → **measure drain voltage**
3. Channel 1 stage 2 → output DC ≈ Vmid
4. Jack + antenna → live test with `probe_check.py`
5. **Do not start channel 2 until channel 1 works**
6. Channel 2 → stereo verification (correlation must NOT be +1.000)

Step-by-step build guide: [`docs/PERTINAKS.en.md`](docs/PERTINAKS.en.md)
(Türkçe: [`docs/PERTINAKS.md`](docs/PERTINAKS.md)).

### Safety

- This is a **receiver**, not a transmitter; listening requires no licence
- Antennas stay **indoors** — never on a roof or hanging off a balcony
- Never connect to mains live/neutral/earth, radiators or water pipes
- **Battery power only** — a mains adapter injects switching noise straight into the band
- Do not touch the circuit during a thunderstorm
- This is **not** a lightning detection or protection system

---

## Software

```
server/vlf_stream/     capture, DSP, MP3 streaming, FastAPI server
server/tools/          probe_check.py · verici_avi.py (transmitter hunt) · canli_seviye.py (live level meter)
web/               station UI (TR/EN)
hardware/          BOM, commissioning checklist
docs/              build guides, experiment protocol
```

### Setup

```bash
cd server
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# ffmpeg required:  apt install ffmpeg   |   winget install Gyan.FFmpeg
```

### Run

On Windows the easiest path is double-clicking **`start-server.bat`** in the
repo root: on first run it creates the virtual environment, lists audio
devices, asks for the device number and starts the server.

Manual start:

```bash
export VLF_DEVICE=1              # Windows: $env:VLF_DEVICE = "1"
uvicorn vlf_stream.server:app --host 0.0.0.0 --port 8000
```

Find the device index with `python -c "import sounddevice; print(sounddevice.query_devices())"`.
On Windows these indices **change** whenever devices are enabled/disabled — check every time.

Try it without hardware: `VLF_MOCK_MODE=1`

### Diagnostic tools

```bash
python tools/probe_check.py --device 1 --seconds 20 --out capture.wav
python tools/canli_seviye.py --device 1          # live level / clipping meter
python tools/verici_avi.py --device 1 --seconds 60 --json ../data/son_tarama.json
```

The `--json` output feeds the transmitter table in the web UI. Scanning requires
the Windows input to be set to **96 kHz** (at 48 kHz the ceiling is 24 kHz and
the upper transmitters fall outside the range).

---

## Build log: what actually happened

Written so that others don't lose the same time. Total: **two weeks**, most of it
spent not on circuit design but on **contact failures**.

### 1. A gain error in the original design (caught before building)

The first schematic fed a single JFET straight into the sound card. The gain
budget totalled ≈ **0 dB**: antenna/gate capacitive divider −6 dB, JFET stage
+15 dB, drain-to-line-input divider −6…−10 dB. Classic natural-radio receivers
run at 60–80 dB. Built as drawn, it would have heard nothing. Replaced with a
two-stage front end (+63 dB).

### 2. The metric was lying

The web UI's "noise reduction" figure credited the band filter's work to the
adaptive filter: it showed 46.1 dB of "cancellation" even with the reference
probe **completely silent**. Now *adaptive cancellation* and *band filter* are
reported separately; the same test reads 0.0 dB.

### 3. Why not a Raspberry Pi?

The project was originally planned around a Raspberry Pi, but the C-Media
(CM108) USB sound card bought for it turned out to be **mono**:
`arecord -D plughw:...` reported "Stereo" — the `plug` layer duplicates mono
into two channels. The truth is in `cat /proc/asound/cardX/stream0`. This
project cannot work without two independent channels, so when the USB card
fell short, everything **moved to the PC's built-in stereo line input (the
blue jack)** and the whole system now runs on the PC. This is the only place
in the repo where the Pi appears — it is a historical note.

### 4. Getting Windows to open the input

The line input initially produced no data at all: `-200.0 dBFS`, i.e. exact
zeros. The chain of causes: with no plug physically inserted, Realtek jack
detection leaves the device "not plugged in" and Windows never opens it;
then `mmsys.cpl` → Recording → show disabled devices → Enable → Levels to 100.
If a device appears only under WDM-KS, it is not fully enabled yet.

### 5. Breadboard hell (the real time sink)

The system died and came back many times. Faults found, in order:

- **A jumper wire broken inside its insulation** — visually perfect, occasionally
  even passing a continuity test
- **A half-seated DIP socket pin** — DC measurements all normal while AC never passes
- **A capacitor leg left floating** — circuit "works" but decoupling is absent
- **Swapped jack wires** — left and right had been exchanged; days of "dead channel"
  were actually measurements taken on an unconnected end
- **One half of the TL072 dying** — normal DC, no AC gain

Two diagnostic tricks proved invaluable: the **fingernail test** (scratch a node
while recording and look for a jump at the output — the human body is a weak
signal source) and the **green level bar in the Windows Recording tab** (answers
"is this node alive?" in seconds without running Python).

**Conclusion:** a breadboard is for prototyping, not for living in. After moving
to soldered perfboard in an enclosure, the contact failures stopped.

### 6. The clipping trap

Raising the gain let the mains signal saturate the ADC, generating **false
harmonics** that buried the weak distant transmitters. Three scans compared:

| Setting | Left RMS | Clipping | Alpha F2 |
|---|---:|---:|---:|
| High gain | −11.6 dBFS | 0.85 % | 13.9 dB |
| Low gain | −27.5 dBFS | 0.00 % | 5.5 dB |
| **Medium, clip-free** | **−25.8 dBFS** | **0.00 %** | **11.7 dB + 8 stations** |

So neither "more gain" nor "less gain" is right — the answer is **just below the
clipping threshold**. `canli_seviye.py` was written to find exactly that point:
it shows live RMS and clipping while you turn the trimmer.

### 7. Day/night reality

During the day, indoors, in a city, sferics are hard to hear — one or two clicks
per minute is normal. Tweeks form **only at night**, so hunting for the "J" hook
in daylight is futile. That is precisely why `verici_avi.py` exists: even when
the sky is quiet, the 24/7 transmitters let you measure the health of the chain.

---

## Sources and an honesty note

**This project is not a first.** VLF natural-radio receivers have been built for
decades, and dual-channel adaptive noise cancellation with a reference probe is a
known technique (standard in active noise control, and applied in VLF work too).
The contribution here is not a new method but a **cheap, reproducible,
step-by-step documented and measurement-verified** implementation.

What this build drew on:

- **Natural-radio receiver architecture:** the classic E-field probe + high-impedance
  JFET buffer + op-amp gain stage arrangement (Stephen P. McGreevy's VLF receiver
  work and the general "mini whip" active-antenna literature)
- **Adaptive noise cancellation:** the Widrow–Hoff LMS/NLMS family; here a
  frequency-domain, transient-protected variant is used (adaptation freezes
  during impulses so the filter never learns the sferic itself)
- **Lightning location data:** the Blitzortung.org volunteer network (free for
  non-commercial use); embedded as a map in the UI
- **VLF transmitter lists:** public frequency records of Alpha/RSDN-20 and MSK
  naval communication transmitters
- **AI assistance:** the initial codebase was generated with a language model.
  It was then reviewed from scratch with a second model (Claude); the gain error
  and the false metric above were found in that review. The circuit revision, the
  diagnostic tools (`probe_check.py`, `canli_seviye.py`, `verici_avi.py`), the web
  UI and this document were produced in the same collaborative process. All
  measurements, soldering and fault-hunting were done by hand on real hardware.

Because the code was written with AI assistance, **do not trust it blindly**: the
DSP is covered by unit tests (`server/tests/`), and the hardware side was verified by
measurement. Apply the same scepticism yourself.

## Licence

MIT — see [LICENSE](LICENSE).
