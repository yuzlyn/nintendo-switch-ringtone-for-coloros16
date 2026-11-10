"""Build the selectable sound library and the default slot configuration.

The module used to ship one fixed file per system slot, so nothing could be
changed from the UI.  This turns every Nintendo Switch sample in the source
pack into a named library entry, and records the slot -> entry mapping that
reproduces the old defaults.

Outputs:
  module/files/library/<id>.ogg     selectable sounds, 48k mono ogg
  module/files/library.tsv          <id>\t<display name>\t<duration ms>
  module/data/sounds.conf           <group>/<target>\t<id>|<->  default mapping
"""
import os
import sys

import numpy as np

import build as B
import dsp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Nintendo-Switch-Sounds-Effect-main", "WAV")
# The library lives inside webroot so the WebUI can stream a preview straight
# from the module without a second copy or an extra endpoint.
OUT = os.path.join(ROOT, "module", "webroot", "sounds")
TSV = os.path.join(OUT, "index.tsv")
CONF = os.path.join(ROOT, "module", "data", "sounds.conf")

# Synthesised entries keep the same ids the old table used via CUSTOM.
CUSTOM_IDS = {
    "__sleep": "custom_sleep",
    "__unlock": "custom_unlock",
    "__u_a": "custom_press",
    "__u_zl": "custom_press_zl",
    "__u_minus": "custom_press_minus",
    "__u_plus": "custom_press_plus",
    "__u_soft": "custom_press_soft",
    "__charge": "custom_charge",
}

CUSTOM_NAMES = {
    "custom_sleep": "睡眠 / 锁屏（固件原声）",
    "custom_unlock": "唤醒（固件原声）",
    "custom_press": "按键点击（唤醒 A）",
    "custom_press_zl": "确认（唤醒 ZL）",
    "custom_press_minus": "删除（唤醒 -）",
    "custom_press_plus": "空格（唤醒 +）",
    "custom_press_soft": "轻触（柔和版）",
    "custom_charge": "充电（Joy-Con 滑轨）",
}


def is_silent(x):
    return len(x) == 0 or float(np.max(np.abs(x))) < 1e-4


def build_library():
    """Encode every usable sample in the source pack."""
    os.makedirs(OUT, exist_ok=True)
    rows = []
    skipped = []

    for name in sorted(os.listdir(SRC)):
        if not name.lower().endswith(".wav"):
            continue
        stem = os.path.splitext(name)[0]
        try:
            x = dsp.load_mono(os.path.join(SRC, name))
        except Exception as exc:  # noqa: BLE001 - report and keep going
            skipped.append((name, f"read: {exc}"))
            continue
        if is_silent(x):
            skipped.append((name, "silent"))
            continue
        y = dsp.trim(x.copy(), thresh_db=-50.0, pad_ms=4)
        # 源包里的 none.wav 是 2ms 的空占位，编进库只会多一条听不见的 "none"
        # 选项。只按文件名剔除，长度过滤会误伤 StartupSleep 这类短音效。
        if stem.lower() == "none":
            skipped.append((name, "placeholder"))
            continue
        y = dsp.normalize_peak(y, ceiling_db=-1.5)
        path = os.path.join(OUT, stem + ".ogg")
        dsp.write_audio(path, y, quality=4)
        rows.append((stem, stem, int(round(len(y) * 1000 / dsp.SR))))

    for key, sid in CUSTOM_IDS.items():
        y = B.CUSTOM[key]()
        path = os.path.join(OUT, sid + ".ogg")
        dsp.write_audio(path, y, quality=4)
        rows.append((sid, CUSTOM_NAMES[sid], int(round(len(y) * 1000 / dsp.SR))))

    rows.sort(key=lambda r: r[0].lower())
    with open(TSV, "w", encoding="utf-8", newline="\n") as fh:
        for sid, label, ms in rows:
            fh.write(f"{sid}\t{label}\t{ms}\n")

    print(f"library: {len(rows)} entries, skipped {len(skipped)}")
    for name, why in skipped:
        print(f"  skip {name}: {why}")
    return {sid for sid, _, _ in rows}


def slot_source_id(source):
    """Map a build-table source token to a library id."""
    if source in CUSTOM_IDS:
        return CUSTOM_IDS[source]
    return source


def default_conf(available):
    lines = []
    missing = set()

    def emit(group, target, sid):
        if sid not in available:
            missing.add(sid)
            return
        lines.append(f"{group}/{target}={sid}")

    for target, spec in B.PRODUCT_UI.items():
        emit("product_ui", target + ".ogg", slot_source_id(spec[0]))
    for target, spec in B.MYSTOCK_UI.items():
        emit("mystock_ui", target, slot_source_id(spec[0]))
    for target, spec in B.NAMED_NOTIF.items():
        emit("notifications", target + ".ogg", slot_source_id(spec[0]))

    pool = [s for s in B.NUMBERED_POOL if s in available]
    for i in range(1, 47):
        sid = pool[(i - 1) % len(pool)] if pool else None
        if sid:
            emit("notifications", f"notification_{i:03d}.ogg", sid)

    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    body = ["# <group>/<target file>=<library id>",
            "# Write \"-\" as the id, or delete the line, to keep the stock sound."]
    body.extend(lines)
    text = "\n".join(body) + "\n"
    # The live config is what the user edits; the default is the reset target
    # and the source of the full slot list the UI renders.
    for path in (CONF, os.path.join(os.path.dirname(CONF), "sounds.default.conf")):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print(f"sounds.conf: {len(lines)} slots, missing {len(missing)}")
    for sid in sorted(missing):
        print(f"  missing source: {sid}")


def main():
    if not os.path.isdir(SRC):
        sys.exit(f"source pack not found: {SRC}")
    available = build_library()
    default_conf(available)


if __name__ == "__main__":
    main()
