"""Minimal DSP helpers: load / normalize / render chiptune voices / write ogg."""
import os
import numpy as np
import soundfile as sf

SR = 48000


def midi_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def load_mono(path, sr=SR):
    """Load any supported file as mono float32 at sr."""
    x, f = sf.read(path, dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if f != sr:
        x = resample(x, f, sr)
    return x


def resample(x, src, dst):
    if src == dst:
        return x
    n = int(round(len(x) * dst / src))
    xi = np.arange(n) * (src / dst)
    i0 = np.floor(xi).astype(np.int64)
    i1 = np.clip(i0 + 1, 0, len(x) - 1)
    i0 = np.clip(i0, 0, len(x) - 1)
    t = (xi - i0).astype(np.float32)
    return (x[i0] * (1 - t) + x[i1] * t).astype(np.float32)


def db(x):
    return 20.0 * np.log10(max(float(x), 1e-9))


def rms_db(x):
    return db(np.sqrt(np.mean(np.square(x)) + 1e-18))


def peak_db(x):
    return db(np.max(np.abs(x)) + 1e-18)


def trim(x, thresh_db=-55.0, pad_ms=8):
    """Trim leading/trailing near-silence."""
    if len(x) == 0:
        return x
    win = max(1, int(SR * 0.005))
    env = np.convolve(np.abs(x), np.ones(win) / win, mode="same")
    thr = 10 ** (thresh_db / 20.0)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    s = max(0, idx[0] - int(SR * pad_ms / 1000))
    e = min(len(x), idx[-1] + int(SR * pad_ms / 1000))
    return x[s:e]


def soft_limit(x, ceiling=0.891):
    """Tanh-ish soft knee limiter, keeps peak under ceiling."""
    x = np.asarray(x, dtype=np.float32)
    p = np.max(np.abs(x)) + 1e-9
    if p <= ceiling:
        return x
    # drive the excess into tanh then renormalise
    drive = p / ceiling
    y = np.tanh(x * drive * 0.9) / np.tanh(drive * 0.9) * ceiling
    y = np.clip(y, -ceiling, ceiling)
    return y.astype(np.float32)


def normalize(x, target_rms_db=-18.0, ceiling=0.891, keep_peak=False):
    x = np.asarray(x, dtype=np.float32)
    if len(x) == 0:
        return x
    cur = rms_db(x)
    gain = 10 ** ((target_rms_db - cur) / 20.0)
    y = x * gain
    return soft_limit(y, ceiling)


def normalize_peak(x, ceiling_db=-2.0):
    x = np.asarray(x, dtype=np.float32)
    if len(x) == 0:
        return x
    ceiling = 10 ** (ceiling_db / 20.0)
    p = float(np.max(np.abs(x)))
    if p < 1e-9:
        return x
    return (x * (ceiling / p)).astype(np.float32)


def fade(x, fade_in_ms=0, fade_out_ms=0):
    x = np.asarray(x, dtype=np.float32).copy()
    if fade_in_ms > 0:
        n = min(len(x), int(SR * fade_in_ms / 1000))
        x[:n] *= np.linspace(0, 1, n, dtype=np.float32)
    if fade_out_ms > 0:
        n = min(len(x), int(SR * fade_out_ms / 1000))
        x[-n:] *= np.linspace(1, 0, n, dtype=np.float32)
    return x


def pad_to(x, dur_s):
    n = int(SR * dur_s)
    if len(x) >= n:
        return x[:n]
    return np.pad(x, (0, n - len(x)))


_FFMPEG = None


def ffmpeg_exe():
    global _FFMPEG
    if _FFMPEG is None:
        os.environ.setdefault("IMAGEIO_FFMPEG_LOGLEVEL", "error")
        import imageio_ffmpeg

        _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    return _FFMPEG


def write_audio(path, x, quality=4, clip_guard=True):
    """Encode through ffmpeg (libsndfile's vorbis encoder blows the stack on
    long buffers under Windows).  Keeps the container implied by the name.

    Lossy encoders overshoot on transients, so the decoded peak is measured
    and the source is trimmed once if it went over.  Android decoders clip
    just as happily as any other.
    """
    import subprocess
    import tempfile

    x = np.clip(np.asarray(x, dtype=np.float32), -1.0, 1.0)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        sf.write(path, x, SR, subtype="PCM_16")
        return
    tmp = tempfile.mktemp(suffix=".wav")
    sf.write(tmp, x, SR, subtype="PCM_16")
    try:
        if ext == ".mp3":
            args = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", tmp,
                    "-c:a", "libmp3lame", "-q:a", str(quality), path]
        else:
            args = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", tmp,
                    "-c:a", "libvorbis", "-q:a", str(quality), path]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    if clip_guard:
        d, _ = sf.read(path, dtype="float32")
        p = float(np.max(np.abs(d))) if len(d) else 0.0
        if p > 0.93:
            write_audio(path, x * (0.93 / p), quality, clip_guard=False)


def write_ogg(path, x, quality=4):
    write_audio(path, x, quality)


def write_wav(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.clip(x, -1, 1), SR, subtype="PCM_16")


# ---------------------------------------------------------------- synthesis

def _phase(freq, n):
    return 2 * np.pi * np.cumsum(np.full(n, freq, dtype=np.float64)) / SR


def env_adsr(n, a=0.005, d=0.08, s=0.6, r=0.12):
    a_n = max(1, int(a * SR))
    d_n = max(1, int(d * SR))
    r_n = max(1, int(r * SR))
    s_n = max(0, n - a_n - d_n - r_n)
    e = np.concatenate(
        [
            np.linspace(0, 1, a_n, dtype=np.float32),
            np.linspace(1, s, d_n, dtype=np.float32),
            np.full(s_n, s, dtype=np.float32),
            np.linspace(s, 0, r_n, dtype=np.float32),
        ]
    )
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def lowpass(x, cutoff):
    """Simple one-pole low pass, cheap but effective for taming squares."""
    if cutoff >= SR / 2:
        return x
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y.astype(np.float32)


def voice_pulse(m, dur, duty=0.5, amp=0.3, a=0.004, d=0.06, s=0.65, r=0.10, cut=6000):
    n = int(SR * dur)
    ph = _phase(midi_freq(m), n) % (2 * np.pi)
    w = np.where(ph < duty * 2 * np.pi, 1.0, -1.0).astype(np.float32)
    w = lowpass(w, cut)
    return w * env_adsr(n, a, d, s, r) * amp


def voice_bell(m, dur, amp=0.3, decay=4.0, cut=9000):
    """Bright sine + soft odd harmonic, exponential decay: the Switch 'pop'."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi_freq(m)
    w = (
        np.sin(2 * np.pi * f * t)
        + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)
        + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9)
    ).astype(np.float32)
    e = np.exp(-t * decay)
    e *= np.minimum(1.0, t / 0.004)
    return w * e * amp


def voice_tri(m, dur, amp=0.25, a=0.006, r=0.08):
    n = int(SR * dur)
    ph = _phase(midi_freq(m), n) % (2 * np.pi)
    w = (2 / np.pi) * np.arcsin(np.sin(ph))
    return (w.astype(np.float32)) * env_adsr(n, a, 0.05, 0.8, r) * amp


def voice_noise(dur, amp=0.08, decay=40.0, cut=8000):
    n = int(SR * dur)
    t = np.arange(n) / SR
    w = np.random.RandomState(int(dur * 1000) % 9973).randn(n).astype(np.float32)
    w = lowpass(w, cut)
    return w * np.exp(-t * decay) * amp


def voice_kick(dur=0.12, amp=0.35):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 150 * np.exp(-t * 30) + 55
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 22) * amp).astype(np.float32)


def mix_into(buf, sig, at_s):
    i = int(SR * at_s)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i : i + n] += sig[:n]


def reverb(x, wet=0.22, size_ms=70, taps=9, decay=0.72):
    """Vectorised multi-tap diffuse tail. Cheap but musical enough for chiptune."""
    x = np.asarray(x, dtype=np.float32)
    n = len(x)
    out = np.zeros(n + int(SR * 0.6), dtype=np.float32)
    out[:n] = x
    acc = x.copy()
    for k in range(1, taps + 1):
        d = int(SR * size_ms * k * 1.17 / 1000)
        if d >= n:
            break
        g = decay ** k * 0.55
        acc[d:] += x[: n - d] * g
    delay = np.zeros_like(acc)
    delay[: len(acc)] = acc
    out2 = np.zeros(n, dtype=np.float32)
    out2[: min(n, len(delay))] = delay[:n]
    return (x * (1 - wet) + out2 * wet).astype(np.float32)
