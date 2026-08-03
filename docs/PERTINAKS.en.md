# Perfboard build guide — a permanent, 96 kHz-ready station

> Türkçe sürüm: [PERTINAKS.md](PERTINAKS.md)

A breadboard is for prototyping, not for living on: nearly every failure that
cost weeks in this project came down to contact problems (a jumper wire broken
inside its insulation, a half-seated socket pin, swapped jack wires). The
permanent station is soldered onto perfboard and boxed.

For the schematic and component values see
[`hardware/README.md`](../hardware/README.md); for the step-by-step electrical
bring-up see [`hardware/commissioning.md`](../hardware/commissioning.md). This
guide covers only the physical build and the 96 kHz setup.

---

## 1. Materials

In addition to the circuit components:

- 5×10 cm perfboard (one board fits both channels)
- 8-pin DIP socket ×1 — **the TL072 is socketed, never soldered directly**
- Bus wire: solid bare wire (for the V+, GND and Vmid rails)
- Thin insulated wire (for connections that cross a rail)
- 3–4 cable ties (strain relief for external wires)
- Soldering iron, solder, side cutters, multimeter

Keep the clipped resistor legs — they make perfect short bridges.

## 2. Three-minute soldering school

1. Keep the tip clean and tinned (wipe on a damp sponge, feed it a little solder).
2. Touch the tip to **both the pad and the lead** at once, heat for 2 seconds.
3. Feed the solder into **the joint**, not the iron; let it flow on its own.
4. Remove the iron and hold everything still for 2–3 seconds.
5. A good joint is **shiny and cone-shaped.** Dull/ball-shaped = cold joint → reheat.
6. Every 5–6 joints, use the multimeter's continuity beeper to **check
   neighbouring pads for shorts** — solder bridges are perfboard mistake number one.
7. Clip the leads **after** soldering.

**Static:** install the JFETs last; touch a grounded metal object (a radiator)
before each handling. The TL072 goes into a socket, so it never sees soldering heat.

## 3. Layout plan

Hold the board horizontally (long edge facing you). Regions run left to right,
following the signal flow: **left = power supply · centre-left = JFET stages ·
centre = TL072 socket · right = outputs.** Channel 1 in the front half,
channel 2 in the back half.

```
   BACK EDGE  ─────────────────────────────────────────────
   [CH2: Q2 R7b R5b C5b R1b R3b C4b]      [CH2 trimpot]
   V+ rail ═════════════════════════════════════════════
   Vmid rail ═══════════════╗  ┌──────┐  ═══════════════
   GND rail ════════════════║══│SOCKET│══════════════════
                            ║  │TL072 │   [R15 C8]→ JACK-L
   [CH1: Q1 R7 R5 C5 R1 R3 C4] └──────┘  [R15b C8b]→ JACK-R
   [battery leads][C10 C11 R20 R21]       [CH1 trimpot]
   FRONT EDGE  ────────────────────────────────────────────
```

Three rules:

1. **Three bus wires** (V+, GND, Vmid) run the full length of the board; every
   part is soldered to the nearest rail point — no long zigzag connections.
   Any connection that must cross a rail uses **insulated** wire.
2. **Socket in the centre**, with the notch direction drawn on the board in
   pen — check the chip against that line on every insertion. TL072 pin map:

   | Pin | Function | | Pin | Function |
   |---|---|---|---|---|
   | 1 | OUT A (channel 1 out) | | 8 | V+ |
   | 2 | IN− A | | 7 | OUT B (channel 2 out) |
   | 3 | IN+ A | | 6 | IN− B |
   | 4 | GND | | 5 | IN+ B |

3. Every external wire (battery, jack, ANT1, ANT2) is **threaded through a
   hole** near the board edge before soldering and secured with a cable tie —
   pull forces load the board, not the solder joint.

Before soldering anything, place all parts on the board **dry** and take a
photo. There is no moving things around after soldering.

## 4. Solder order and checkpoints

If you have a working breadboard prototype, do not tear it down until the end;
move parts stage by stage so you always have a working reference. Target
values match [`commissioning.md`](../hardware/commissioning.md).

☐ **4.1** Solder the DIP socket (draw the notch direction). Leave it empty.

☐ **4.2** Power: battery leads (through a strain-relief hole) → V+ and GND
rails. C11, R20, R21, C10.
**✔ CP1:** insert batteries, switch on: V+ ≈ 12–13 V, Vmid ≈ half of it.
Switch off.

☐ **4.3** Channel 1 stage 1: Q1 (verify D-S-G from the datasheet), R7, R5,
C5, C4, R1, R3 (2×10M in series). Thread the ANT1 wire through a hole and
solder it to R1.
**✔ CP2:** switch on: drain = 40–70 % of V+ (4.8–8.4 V at 12 V).

☐ **4.4** Channel 1 stage 2: socket pin 8 → V+ and pin 4 → GND bridges,
C3 100nF close to the socket (pin 8 pad to GND), C4 → pin 3, R12
(pin 3 → Vmid), trimpot 1 (wiper + one end → pin 1, other end → pin 2),
R13 + C7 (pin 2 → Vmid), R15 + C8 → JACK-L wire (through a hole). Jack ground
wire → GND rail. Insert the TL072 (notch on the line).
**✔ CP3:** pin 1 DC ≈ Vmid.
**✔ CP4:** trimpot at minimum, jack plugged into the PC: scratch the pin 3
pad with a fingernail → the LEFT channel must jump in `probe_check.py`. Then,
with the antenna connected, trim the LEFT level to −30…−20 dBFS.

☐ **4.5** Channel 2: a copy of 4.3–4.4 using socket pins 5-6-7. JACK-R wire
through a hole. Reference probe → ANT2.
**✔ CP5:** both channels live, channel correlation ≠ +1.000, RIGHT level
trimmed to −40…−30 dBFS.

☐ **4.6** Box it: board at the bottom, cables exit through a single hole,
battery holder beside it. Re-verify CP4 and CP5 before closing the lid.

## 5. Moving to 96 kHz — for the transmitter hunt

At 48 kHz sampling the ceiling is 24 kHz and most MSK transmitters are out of
range. 96 kHz raises the ceiling to 48 kHz and brings the whole catalogue,
including TBB (26.7 kHz), into range. **No hardware change is needed:** the
JFET stage passes hundreds of kHz, and the TL072's 3 MHz gain-bandwidth
product gives ~30 kHz of bandwidth at 40 dB gain. One rule: do not max out the
trimpot during a transmitter scan (keep it around 30–35 dB), or the bandwidth
shrinks.

☐ **5.1** Set the Windows input to 96 kHz: `mmsys.cpl` → Recording → Line In →
Properties → Advanced → **"2 channel, 16 bit, 96000 Hz"** → Apply.

☐ **5.2** Verify:

```powershell
python server/tools/probe_check.py --device 1 --rate 96000 --seconds 10
```

The header must say 96000 Hz and the spectrum must extend to 48 kHz.

☐ **5.3** Start the server at 96 kHz (or put these in `server/.env`):

```powershell
$env:VLF_DEVICE = "1"
$env:VLF_SAMPLE_RATE = "96000"
$env:VLF_HIGH_CUT_HZ = "20000"
uvicorn vlf_stream.server:app --host 0.0.0.0 --port 8000
```

☐ **5.4** Transmitter hunt:

```powershell
python server/tools/verici_avi.py --device 1 --seconds 60 --json ../data/son_tarama.json
```

The `--json` output feeds the transmitter table in the web interface.

**Honest limit:** the web interface is fed by the MP3 stream, and MP3 stays at
48 kHz — the web waterfall ceiling is 24 kHz. Transmitters above 24 kHz show
up in the `verici_avi.py` output, not on the web. These transmitters are above
human hearing anyway: they are not heard, they are measured.

## 6. Common perfboard mistakes

| Symptom | Cause |
|---|---|
| Unwanted zero ohms between two points | Solder bridge — inspect with a magnifier, sweep with the iron |
| Works, cuts out, works again | Cold joint (dull/ball look) — reheat |
| Nonsense DC readings with the chip in | Socket/chip notch not matching the drawn line |
| One node completely dead | Lead clipped before soldering or lifted pad → bridge from a neighbouring hole |
| probe_check fails at 96k | Windows Advanced tab still at 48000 |
| No stream audio but tests pass | Environment variables missing in that terminal (apply block 5.3 fully) |
