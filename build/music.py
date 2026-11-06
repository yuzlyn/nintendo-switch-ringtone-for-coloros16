"""Procedural Nintendo-Switch-flavoured chiptune generator.

Everything is written from the same idiom the Switch UI uses: bright bell
plucks, tight square leads, triangle bass, pentatonic melodies and a light
shaker.  Each style is a small parameter set; transposing the whole thing
gives musically valid variants for the many ringtone slots.
"""
import numpy as np

import dsp

MAJOR = [0, 2, 4, 5, 7, 9, 11]
LYDIAN = [0, 2, 4, 6, 7, 9, 11]
MAJ_PENT = [0, 2, 4, 7, 9]
MIN_PENT = [0, 3, 5, 7, 10]
DORIAN = [0, 2, 3, 5, 7, 9, 10]

QUAL = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "sus4": [0, 5, 7],
    "add9": [0, 4, 7, 14],
}

# (key offset from C, scale, progression as [(root offset, quality)], bpm,
#  lead voice, lead octave, perc level)
STYLES = [
    ("Home", 0, MAJOR, [(0, "maj"), (7, "maj"), (9, "min"), (5, "maj")], 112, "bell", 0, 0.55),
    ("eShop", 5, MAJ_PENT, [(0, "maj"), (5, "maj"), (7, "maj"), (9, "min")], 122, "pulse", 0, 0.7),
    ("Album", 2, MAJOR, [(0, "maj7"), (9, "min7"), (5, "maj7"), (7, "dom7")], 100, "bell", 0, 0.4),
    ("News", 7, LYDIAN, [(0, "maj"), (9, "min"), (2, "min7"), (7, "maj")], 96, "bell", 1, 0.35),
    ("Odyssey", 9, MAJ_PENT, [(0, "maj"), (7, "maj"), (5, "maj"), (5, "maj")], 128, "pulse", 1, 0.8),
    ("Zelda", 3, DORIAN, [(0, "min"), (10, "maj"), (5, "min"), (7, "min")], 88, "bell", 0, 0.25),
    ("Splatoon", 4, MIN_PENT, [(0, "min"), (5, "min"), (10, "maj"), (3, "maj")], 140, "pulse", 1, 0.85),
    ("Kirby", 5, MAJOR, [(0, "maj"), (5, "maj"), (7, "dom7"), (0, "maj")], 132, "bell", 0, 0.7),
    ("Metroid", 10, MIN_PENT, [(0, "min"), (3, "maj"), (8, "maj"), (7, "min")], 104, "pulse", 0, 0.5),
    ("Mario", 0, MAJ_PENT, [(0, "maj"), (5, "maj"), (9, "min"), (7, "maj")], 124, "pulse", 1, 0.75),
    ("Animal", 2, MAJOR, [(0, "maj7"), (5, "maj7"), (9, "min7"), (7, "sus4")], 92, "bell", 0, 0.3),
    ("Arcade", 7, MAJ_PENT, [(0, "maj"), (9, "min"), (2, "min"), (7, "maj")], 150, "pulse", 1, 0.9),
]

BAR = 4.0


def _scale_note(scale, key, degree, octave=0):
    """degree can be any int (may go negative / beyond one octave)."""
    n = len(scale)
    idx = degree % n
    octs = degree // n
    return 60 + key + scale[idx] + 12 * (octave + octs)


def _chord(key, off, quality):
    return [60 + key + off + s for s in QUAL[quality]]


def _motif(style, seed):
    """A short scale-degree motif: statement, then 3 variations."""
    name = style[0]
    rng = np.random.RandomState((seed * 7919 + sum(ord(c) for c in name) * 31) % (2 ** 31 - 1))
    deg = 2 + int(rng.randint(0, 3))
    motif = [deg]
    for _ in range(5):
        motif.append(motif[-1] + int(rng.choice([-2, -1, -1, 1, 1, 2])))
    return motif


def _melody_line(style, bars, seed):
    """Motif + sequenced variations, snapped to chord tones on strong beats."""
    name, key, scale, prog, bpm, lead, oct_adj, perc = style
    rng = np.random.RandomState((seed * 104729 + 17) % (2 ** 31 - 1))
    motif = _motif(style, seed)
    notes = []
    beat = 0.0
    rhythms = [
        [1.0, 0.5, 0.5, 1.0, 1.0, 0.0],   # statement
        [0.5, 0.5, 1.0, 1.0, 1.0, 0.0],   # answer
        [1.0, 0.5, 0.5, 0.5, 0.5, 1.0],   # busier
        [1.5, 0.5, 0.5, 1.5, 0.0, 0.0],   # cadence, leaves air
    ]

    for bar in range(bars):
        root_off, quality = prog[bar % len(prog)]
        phr = bar % 4
        degs = list(motif)
        if phr == 1:
            degs[-1] = degs[-1] - 1
            degs[-2] = degs[-2] + 1
        elif phr == 2:
            degs = [d + 2 for d in degs]
        elif phr == 3:
            degs = [degs[0], degs[1] - 1, degs[2] - 2, 0, 0, 0]

        rhythm = rhythms[phr]
        t = 0.0
        for i, dur in enumerate(rhythm):
            if dur <= 0 or t >= BAR:
                break
            strong = (t % 4.0) < 0.01 or abs((t % 4.0) - 2.0) < 0.01
            deg = degs[i % len(degs)]
            cur = _scale_note(scale, key, deg, oct_adj)
            if strong:
                targets = [60 + key + root_off + ct + 12 * oct_adj
                           for ct in QUAL[quality]]
                m = min(targets, key=lambda x: abs(x - cur))
            else:
                m = cur
            vel = 0.95 if strong else 0.70 + 0.22 * rng.rand()
            notes.append((beat + t, min(dur, BAR - t) * 0.9, m, vel))
            t += dur
        beat += BAR
    return notes


def compose(style, bars=8, seed=1, transpose=0, bpm_scale=1.0, tag=""):
    name, key, scale, prog, bpm, lead, oct_adj, perc = style
    bpm = bpm * bpm_scale
    spb = 60.0 / bpm
    total_beats = bars * BAR
    total = total_beats * spb
    n = int(dsp.SR * (total + 1.2))
    buf = np.zeros(n, dtype=np.float32)

    key = key + transpose
    rng = np.random.RandomState(seed)

    # ---- pad / arpeggio bed
    for bar in range(bars):
        root_off, quality = prog[bar % len(prog)]
        chord = _chord(key, root_off, quality)
        t0 = bar * BAR * spb
        # bass: root on 1 and 3
        for b in (0.0, 2.0):
            m = chord[0] - 24
            dsp.mix_into(buf, dsp.voice_tri(m, spb * 1.6, amp=0.30, r=0.12), t0 + b * spb)
        # soft chord stab on off-beat 2.5
        for m in chord[:3]:
            dsp.mix_into(
                buf,
                dsp.voice_pulse(m, spb * 0.55, duty=0.35, amp=0.045, cut=3200,
                                a=0.01, d=0.05, s=0.5, r=0.15),
                t0 + 1.5 * spb,
            )

    # ---- arpeggio 8ths
    arp_amp = 0.10 if lead == "bell" else 0.075
    step = 0.5
    k = 0
    for i in range(int(total_beats / step)):
        tb = i * step
        bar = int(tb // BAR)
        root_off, quality = prog[bar % len(prog)]
        chord = _chord(key, root_off, quality)
        seq = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 12]
        m = seq[k % 4]
        k += 1
        dsp.mix_into(
            buf,
            dsp.voice_bell(m, spb * 0.5, amp=arp_amp, decay=16.0),
            tb * spb,
        )

    # ---- lead melody
    for (t, dur, m, vel) in _melody_line(style, bars, seed):
        d = dur * spb
        if lead == "bell":
            sig = dsp.voice_bell(m, d + 0.35, amp=0.30 * vel, decay=6.5)
            dsp.mix_into(buf, dsp.reverb(sig, wet=0.16, size_ms=55), t * spb)
        else:
            sig = dsp.voice_pulse(m, d, duty=0.25, amp=0.20 * vel,
                                  a=0.005, d=0.07, s=0.62, r=min(0.12, d * 0.4), cut=7000)
            dsp.mix_into(buf, dsp.reverb(sig, wet=0.10, size_ms=45), t * spb)

    # ---- percussion
    if perc > 0:
        for i in range(int(total_beats)):
            tb = i
            if i % 4 in (0, 2):
                dsp.mix_into(buf, dsp.voice_kick(0.10, amp=0.22 * perc), tb * spb)
            if i % 2 == 1:
                dsp.mix_into(buf, dsp.voice_noise(0.05, amp=0.05 * perc, decay=70, cut=9000),
                             tb * spb)
            else:
                dsp.mix_into(buf, dsp.voice_noise(0.03, amp=0.025 * perc, decay=110, cut=11000),
                             (tb + 0.5) * spb)

    x = buf[: int(dsp.SR * total)]
    x = dsp.normalize(x, target_rms_db=-16.0, ceiling=0.89)
    x = dsp.fade(x, 4, 90)
    return x


def compose_ambient(style, bars=8, seed=3, transpose=0, bpm_scale=1.0):
    """Soft pad bed used for the weather alarm slots."""
    name, key, scale, prog, bpm, lead, oct_adj, perc = style
    bpm = bpm * 0.62 * bpm_scale
    spb = 60.0 / bpm
    total = bars * BAR * spb
    n = int(dsp.SR * total)
    buf = np.zeros(n, dtype=np.float32)
    key = key + transpose
    for bar in range(bars):
        root_off, quality = prog[bar % len(prog)]
        chord = _chord(key, root_off, quality)
        t0 = bar * BAR * spb
        for j, m in enumerate(chord[:3]):
            sig = dsp.voice_tri(m, spb * 3.6, amp=0.16, a=0.35, r=1.2)
            dsp.mix_into(buf, dsp.reverb(sig, wet=0.35, size_ms=110, taps=12), t0 + j * 0.03)
        # slow shimmer
        for j in range(4):
            m = chord[j % len(chord)] + 12
            dsp.mix_into(
                buf,
                dsp.voice_bell(m, spb * 1.2, amp=0.055, decay=3.0),
                t0 + (j * 1.0) * spb,
            )
    x = dsp.normalize(buf, target_rms_db=-21.0, ceiling=0.84)
    x = dsp.fade(x, 700, 1400)
    return x


def compose_alarm(style, seed=7, transpose=0, total_s=26.0):
    """Repeating bell figure with a rising urgency - alarm material."""
    name, key, scale, prog, bpm, lead, oct_adj, perc = style
    bpm = 108.0
    spb = 60.0 / bpm
    n = int(dsp.SR * total_s)
    buf = np.zeros(n, dtype=np.float32)
    key = key + transpose
    pattern = [0, 12, 7, 12, 0, 12, 5, 12]
    t = 0.0
    i = 0
    while t < total_s - 2.0:
        bar = int(t // (BAR * spb))
        root_off, quality = prog[bar % len(prog)]
        chord = _chord(key, root_off, quality)
        for k, off in enumerate(pattern):
            m = chord[0] + 12 + off
            dsp.mix_into(buf, dsp.voice_bell(m, spb * 0.55, amp=0.22, decay=9.0),
                         t + k * spb * 0.5)
        for b in (0.0, 2.0):
            dsp.mix_into(buf, dsp.voice_tri(chord[0] - 24, spb * 1.5, amp=0.26), t + b * spb)
        t += BAR * spb
        i += 1
    x = dsp.normalize(buf, target_rms_db=-16.0, ceiling=0.89)
    x = dsp.fade(x, 8, 400)
    return x
