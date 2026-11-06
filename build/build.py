"""Build every replacement audio asset for the NS-Ringtone module."""
import os
import shutil
import numpy as np

import dsp
import music

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Nintendo-Switch-Sounds-Effect-main", "WAV")
OUT = os.path.join(ROOT, "module", "files")

_cache = {}


def src(name):
    if name not in _cache:
        _cache[name] = dsp.load_mono(os.path.join(SRC, name + ".wav"))
    return _cache[name]


def sfx(name, max_len=None, peak_db=-2.0, lowpass=None, fade_out=18):
    """Load one Switch SE, trim the tail, optionally soften, then level it."""
    x = src(name).copy()
    x = dsp.trim(x, thresh_db=-50.0, pad_ms=6)
    if max_len and len(x) > int(dsp.SR * max_len):
        x = x[: int(dsp.SR * max_len)]
        x = dsp.fade(x, 0, fade_out)
    if lowpass:
        x = dsp.lowpass(x, lowpass)
    return dsp.normalize_peak(x, ceiling_db=peak_db)


def loud(x, target_rms=-14.5, ceiling=0.78, max_gain_db=12.0):
    """Perceived-loudness targeting for one-shot sounds (notifications)."""
    cur = dsp.rms_db(x)
    gain = min(target_rms - cur, max_gain_db)
    return dsp.soft_limit(x * (10 ** (gain / 20.0)), ceiling)


def notify_voice(spec):
    """Notification one-shot with a little room tail so a 0.1s blip still
    registers when the phone is in a pocket."""
    x = render(spec)
    x = np.pad(x, (0, int(dsp.SR * 0.18)))
    x = dsp.reverb(x, wet=0.20, size_ms=55, taps=6)
    return loud(x)


def seq(parts):
    end = max(o + len(s) / dsp.SR for o, s in parts)
    buf = np.zeros(int(dsp.SR * (end + 0.05)), dtype=np.float32)
    for o, s in parts:
        dsp.mix_into(buf, s, o)
    return buf


# --------------------------------------------------------------- ui: product
# (source, max_len, peak_db, lowpass_hz)
PRODUCT_UI = {
    "Camera_Timer":        ("SeGameIconLimit", 0.30, -6.0, 7000),
    "Camera_Timer_2sec":   ("SeGameIconLimit", 0.30, -6.0, 7000),
    "Dock":                ("__charge", 0, 0, None),
    "Effect_Tick":         ("__u_a", 0, 0, None),
    "InCallNotification":  ("SeSuccess", 0.30, -4.0, None),
    "KeypressDelete":      ("__u_minus", 0, 0, None),
    "KeypressInvalid":     ("SeKeyErrorTouch", 0.35, -6.0, 6000),
    "KeypressReturn":      ("__u_zl", 0, 0, None),
    "KeypressSpacebar":    ("__u_plus", 0, 0, None),
    "KeypressStandard":    ("__u_a", 0, 0, None),
    "Lock":                ("__screenoff", 0, 0, None),
    "LowBattery":          ("SeWarning_Dtt", 0.30, -5.0, 7000),
    "Screenshots":         ("SeCheckBtnPressFinish", 0.16, -7.0, 6000),
    "Undock":              ("SeVgcCard_Eject", 0.45, -8.0, 5000),
    "Unlock":              ("__screenon", 0, 0, None),
    "VideoRecord":         ("SeStartVgc", 0.45, -7.0, 6000),
    "camera_click":        ("SeCheckBtnPressFinish", 0.14, -7.0, 6500),
    "camera_click_start":  ("SeGameIconCardInsert", 0.14, -8.0, 6000),
    "camera_click_stop":   ("SeFooterDecideFinish", 0.18, -7.0, 6000),
    "camera_focus":        ("SeVgc_Dialog_Check", 0.20, -9.0, 5500),
    "camera_shutter":      ("SeCheckBtnPressFinish", 0.14, -7.0, 6500),
    "charging":            ("__charge", 0, 0, None),
}

# (source, max_len, peak_db, lowpass_hz)
MYSTOCK_UI = {
    "Usb.ogg":                       ("__charge", 0, 0, None),
    "VolumePanelSound.ogg":          ("__u_a_long", 0, 0, None),
    "WheelPicker.ogg":               ("__u_a_long", 0, 0, None),
    "camera_click.wav":              ("SeCheckBtnPressFinish", 0.14, -7.0, 6500),
    "charge.mp3":                    ("__charge", 0, 0, None),
    "cover.mp3":                     ("SeFlcIconSink", 0.45, -9.0, 5200),
    "critical_lowbattery.ogg":       ("SeVgc_Error", 0.65, -4.0, 6000),
    "delete.mp3":                    ("SeFlcGroupDelete", 0.14, -9.0, 5000),
    "delete3.mp3":                   ("SeVgc_Deleted", 0.20, -8.0, 5500),
    "dew.wav":                       ("SeBatteryRateIn", 0.10, -10.0, 5000),
    "ebook_open.mp3":                ("SeDialogOpen_Accent", 0.50, -8.0, 5500),
    "ebook_open2.mp3":               ("SeFlcIconFloat", 0.40, -9.0, 5500),
    "ebook_page1.mp3":               ("SePage", 0.40, -9.0, 5500),
    "ebook_page3.mp3":               ("SeVgcCard_Leave", 0.12, -10.0, 5000),
    "error.mp3":                     ("SeKeyErrorTouch", 0.45, -6.0, 6000),
    "extended_effect_a.ogg":         ("SeNetTest_04", 0.12, -9.0, 5500),
    "extended_effect_b.ogg":         ("SeSurroundTest", 0.12, -9.0, 5500),
    "extended_effect_c.ogg":         ("SeTestTone", 0.12, -9.0, 5500),
    "extended_effect_d.ogg":         ("SeCheckboxOff", 0.10, -10.0, 5000),
    "extended_effect_e.ogg":         ("SeCheckboxOn", 0.12, -9.0, 5000),
    "full_battery.ogg":              ("SeSuccess", 0.30, -5.0, None),
    "global_delete.ogg":             ("SeVgc_Deleted", 0.20, -8.0, 5500),
    "inefficacy.mp3":                ("SeKeyErrorTouch", 0.25, -8.0, 6000),
    "lomo_click.mp3":                ("SeCheckboxOn", 0.12, -9.0, 5000),
    "lowbattery.mp3":                ("SeWarning_Dtt", 0.30, -5.0, 7000),
    "machine.mp3":                   ("SeSetStickPush", 0.14, -9.0, 5500),
    "mechanism_down.ogg":            ("SeFlcIconSink", 0.45, -9.0, 5200),
    "mechanism_up.ogg":              ("SeFlcIconFloat", 0.45, -9.0, 5200),
    "normal_lowbattery.ogg":         ("SeWarning_Dtt", 0.30, -5.0, 7000),
    "numberpicker_click.ogg":        ("__u_a", 0, 0, None),
    "powerlow.mp3":                  ("SeVgc_Error", 0.45, -6.0, 6000),
    "pure_music_down.ogg":           ("SeVgcCard_Leave", 0.12, -10.0, 5000),
    "pure_music_up.ogg":             ("SeVgcCard_Insert", 0.12, -10.0, 5000),
    "slight_feedback.ogg":           ("__u_soft", 0, 0, None),
    "technology_down.ogg":           ("SeFlcIconSink", 0.45, -9.0, 5200),
    "technology_up.ogg":             ("SeFlcIconFloat", 0.45, -9.0, 5200),
    "touch.mp3":                     ("__u_a", 0, 0, None),
    "touch2.mp3":                    ("__u_plus", 0, 0, None),
    "touch3.mp3":                    ("__u_minus", 0, 0, None),
    "uncover.mp3":                   ("SeFlcIconFloat", 0.40, -9.0, 5200),
    "warning3.mp3":                  ("SeVgc_Error", 0.45, -6.0, 6000),
    "warrning.mp3":                  ("SeWarning_Dtt", 0.30, -5.0, 7000),
}

# ----------------------------------------------------------- ui: notifications
# (source, max_len, peak_db, lowpass_hz)
NAMED_NOTIF = {
    "Alert":            ("SeNewsBad", 0.60, -2.0, None),
    "Anticipate":       ("SeUnlockKeyL", 0.55, -2.0, None),
    "Bell":             ("SeVgcBtnCard_Decide", 0.60, -2.0, None),
    "Bloom":            ("SeSelectCheck", 0.60, -2.0, None),
    "Calypso":          ("SeBtnFocus", 0.55, -2.0, None),
    "Chime":            ("SeDialogPtclRating", 0.70, -2.0, None),
    "Choo Choo":        ("SeVgc_Paring_Guide", 0.80, -2.0, None),
    "ct-error":         ("SeVgc_Error", 0.80, -2.0, None),
    "Descent":          ("SeSelectUncheck", 0.60, -2.0, None),
    "Ding":             ("SeSuccess", 0.30, -1.0, None),
    "Electronic":       ("SeGameIconEffect", 0.25, -2.0, None),
    "Fanfare":          ("SeDialogParentalControllOn", 0.75, -2.0, None),
    "Glass":            ("SeNewsNice", 0.22, -2.0, None),
    "Horn":             ("SeVgcCard_Eject_Start", 0.60, -2.0, None),
    "Ladder":           ("SeBatteryRateIn", 0.22, -2.0, None),
    "Minuet":           ("StartupNews", 0.85, -1.5, None),
    "News Flash":       ("SeNewsChannelRegister", 0.25, -2.0, None),
    "Noir":             ("SeKeyErrorTouch", 0.60, -2.0, None),
    "Sherwood Forest":  ("SeDeviceFound_Dtt", 0.75, -2.0, None),
    "Spell":            ("SeVgc_Paring_Fix", 0.75, -2.0, None),
    "Suspense":         ("SeVgcCard_Appear_01", 0.22, -2.0, None),
    "Swish":            ("SeFlcIconLoadedInner", 0.22, -2.0, None),
    "Swoosh":           ("SeVgcCard_Overlap_Short", 0.25, -2.0, None),
    "Telegraph":        ("SeMeterKeyDecide", 0.60, -2.0, None),
    "Tiptoes":          ("SeNewsBookmark", 0.22, -2.0, None),
    "Tri-Tone":         ("StartupAlbum", 0.85, -1.5, None),
    "Tweet":            ("SeSelectFocus", 0.25, -2.0, None),
    "Typewriters":      ("SeKeyRecieved", 0.60, -2.0, None),
    "Update":           ("StartupVgc", 0.25, -2.0, None),
}

NUMBERED_POOL = [
    "SeVgcCard_Status_Insert", "SeVgcCard_Status_Eject", "SeGameIconFocus",
    "SeGameIconLimit", "SeGameIconAdd", "SeGameIconDecideSupend",
    "SeHelpBtnFocus", "SeFlcIconSink", "SeFlcIconFloat", "SeSurroundTestSw",
    "SeUnlockStickL", "SeUnlockStickR", "SeUnlockMinus", "SeUnlockPlus",
    "SeRadioBtnFocus", "SeSaveBackupChecked", "SeSetNaviFocus",
    "SeFullLancherBtnFocus", "SeVgcBtnCard_Reserved_Select",
    "SeVgcCard_Status_FamilyLend", "SeVgcCard_Status_FamilyReturn",
    "SeVgc_FamilyReturn", "SeVgc_Info_OperateOthers", "SeVgc_Connect_Recieve",
    "SeFooterDecideBack", "SeEntLaunchEffectHome",
    "SeEntSpeacialNewsBalloonAppear", "SeCheckboxFocus", "StartupShop",
    "StartupSet", "StartupSleep", "StartupFlc", "StartupSplay", "EntAlbum",
    "EntFlc", "EntNso", "EntSplay", "EntVgc", "SeVgcCard_Insert_Start_Others",
    "SeVgcCard_Move_Insert_2", "SeWaiting", "SeVgcCard_Leave_Short",
    "SeVgcCard_Status_Visible", "SeVgcCard_Insert_Others",
    "SeVgcCard_Insert", "SeAppletBtnFocus",
]

WEATHER_LEN = {
    "weather_alarm_cloud.ogg": 21.0, "weather_alarm_cloud2.ogg": 20.8,
    "weather_alarm_cloud3.ogg": 19.7, "weather_alarm_cloud4.ogg": 21.3,
    "weather_alarm_default.ogg": 30.3, "weather_alarm_haze.ogg": 16.8,
    "weather_alarm_haze2.ogg": 17.3, "weather_alarm_rain.ogg": 16.5,
    "weather_alarm_rain2.ogg": 15.0, "weather_alarm_snow.ogg": 18.2,
    "weather_alarm_snow2.ogg": 43.2, "weather_alarm_sun.ogg": 21.4,
    "weather_alarm_sun2.ogg": 20.9, "weather_alarm_sun3.ogg": 40.5,
    "weather_alarm_sun4.ogg": 20.9, "weather_alarm_thunderstorm.ogg": 16.0,
    "weather_alarm_thunderstorm2.ogg": 28.7, "weather_alarm_thunderstorm3.ogg": 14.9,
    "weather_alarm_wind.ogg": 19.2, "weather_alarm_wind2.ogg": 21.0,
}


# ------------------------------------------------------------- custom designs

def screen_chime(up=True):
    """Multi-stage screen on/off chime, Switch-ish three step figure."""
    notes = [84, 88, 91] if up else [91, 88, 84]
    parts = []
    for k, m in enumerate(notes):
        sig = dsp.voice_bell(m, 0.55, amp=0.30, decay=7.5)
        parts.append((k * 0.075, sig))
    x = seq(parts)
    x = dsp.fade(x, 2, 120)
    return dsp.normalize_peak(x, ceiling_db=-7.0)


def joycon_charge():
    """Soft mechanical 'clack' plus a warm two note lift: the Joy-Con rail."""
    buf = np.zeros(int(dsp.SR * 0.95), dtype=np.float32)
    # rail click
    dsp.mix_into(buf, dsp.voice_noise(0.045, amp=0.16, decay=150, cut=3800), 0.005)
    dsp.mix_into(buf, dsp.voice_tri(45, 0.10, amp=0.22, a=0.001, r=0.05), 0.005)
    # warm confirmation
    for k, m in enumerate([76, 83]):
        sig = dsp.voice_bell(m, 0.75, amp=0.22, decay=4.6)
        sig = dsp.reverb(sig, wet=0.14, size_ms=60, taps=6)
        dsp.mix_into(buf, sig, 0.10 + k * 0.115)
    return dsp.normalize_peak(buf, ceiling_db=-8.0)


def soft_tick():
    """Volume slider / picker tick: short, rounded, no harsh top end."""
    sig = dsp.voice_bell(88, 0.16, amp=0.30, decay=24.0)
    sig = dsp.lowpass(sig, 4200)
    sig = dsp.fade(sig, 1, 30)
    return dsp.normalize_peak(sig, ceiling_db=-5.0)


def unlock_press(source="SeUnlock", peak_db=-7.5, tail=0.03, lp=5000):
    """The Switch wake-screen button press: a soft, rounded 'tok'.

    tail pads the sample so a very short press still leaves a little room
    behind it instead of stopping dead.
    """
    x = dsp.trim(src(source).copy(), thresh_db=-50.0, pad_ms=4)
    x = dsp.lowpass(x, lp)
    if tail:
        x = np.pad(x, (0, int(dsp.SR * tail)))
        x = dsp.reverb(x, wet=0.14, size_ms=40, taps=4)
    x = dsp.fade(x, 0, 12)
    return dsp.normalize_peak(x, ceiling_db=peak_db)


def boot_sound():
    total = 5.8
    buf = np.zeros(int(dsp.SR * total), dtype=np.float32)
    dsp.mix_into(buf, dsp.voice_kick(0.22, amp=0.55), 0.02)
    dsp.mix_into(buf, dsp.voice_noise(0.09, amp=0.10, decay=45, cut=5200), 0.02)
    for k, m in enumerate([72, 76, 79, 84]):
        sig = dsp.voice_bell(m, 2.6, amp=0.30 - k * 0.02, decay=1.9)
        sig = dsp.reverb(sig, wet=0.30, size_ms=90, taps=10)
        dsp.mix_into(buf, sig, 0.16 + k * 0.135)
    for m in [48, 55, 64]:
        dsp.mix_into(buf, dsp.voice_tri(m, 3.4, amp=0.13, a=0.25, r=1.6), 0.10)
    for k, m in enumerate([96, 100, 103]):
        dsp.mix_into(buf, dsp.voice_bell(m, 2.0, amp=0.05, decay=2.2), 0.75 + k * 0.18)
    buf = dsp.normalize(buf, target_rms_db=-19.5, ceiling=0.88)
    return dsp.fade(buf, 3, 900)


def shutdown_sound():
    total = 5.8
    buf = np.zeros(int(dsp.SR * total), dtype=np.float32)
    for k, m in enumerate([84, 79, 74, 67]):
        sig = dsp.voice_bell(m, 2.2, amp=0.26 - k * 0.03, decay=1.6)
        sig = dsp.reverb(sig, wet=0.28, size_ms=85, taps=9)
        dsp.mix_into(buf, sig, 0.05 + k * 0.22)
    dsp.mix_into(buf, dsp.voice_tri(48, 2.8, amp=0.12, a=0.15, r=1.5), 0.10)
    dsp.mix_into(buf, dsp.voice_noise(0.35, amp=0.06, decay=9, cut=2600), 1.55)
    buf = dsp.normalize(buf, target_rms_db=-21.0, ceiling=0.85)
    return dsp.fade(buf, 5, 1400)


def countdown(seconds):
    buf = np.zeros(int(dsp.SR * (seconds + 0.6)), dtype=np.float32)
    for i in range(seconds):
        m = 84 if i == seconds - 1 else 76
        dsp.mix_into(buf, dsp.voice_bell(m, 0.5, amp=0.30, decay=12.0), i)
    return dsp.normalize_peak(buf, ceiling_db=-2.0)


CUSTOM = {
    "__screenoff": lambda: screen_chime(up=False),
    "__screenon": lambda: screen_chime(up=True),
    "__charge": joycon_charge,
    "__tick": soft_tick,
    # wake-screen button presses (A family)
    "__u_a": lambda: unlock_press("SeUnlock", -7.5, 0.03, 5000),
    "__u_a_long": lambda: unlock_press("SeUnlock", -5.0, 0.11, 5200),
    "__u_zl": lambda: unlock_press("SeUnlockKeyZL", -7.5, 0.03, 5000),
    "__u_minus": lambda: unlock_press("SeUnlockMinus", -8.5, 0.03, 5000),
    "__u_plus": lambda: unlock_press("SeUnlockPlus", -8.5, 0.03, 5000),
    "__u_soft": lambda: unlock_press("SeUnlock", -10.0, 0.03, 4500),
}


def render(spec):
    source, max_len, peak_db, lowpass = spec
    if source in CUSTOM:
        return CUSTOM[source]()
    return sfx(source, max_len, peak_db, lowpass)


def build_ui():
    n = 0
    for target, spec in PRODUCT_UI.items():
        dsp.write_audio(os.path.join(OUT, "product_ui", target + ".ogg"), render(spec))
        n += 1
    for target, spec in MYSTOCK_UI.items():
        dsp.write_audio(os.path.join(OUT, "mystock_ui", target), render(spec))
        n += 1

    dsp.write_audio(os.path.join(OUT, "mystock_ui", "poweron.mp3"), boot_sound())
    dsp.write_audio(os.path.join(OUT, "mystock_ui", "poweroff.mp3"), shutdown_sound())
    dsp.write_audio(os.path.join(OUT, "mystock_ui", "sound_10s.mp3"), countdown(10))
    dsp.write_audio(os.path.join(OUT, "mystock_ui", "sound_5s.mp3"), countdown(5))
    n += 4

    for i, (name, dur) in enumerate(sorted(WEATHER_LEN.items())):
        style = music.STYLES[(i * 5) % len(music.STYLES)]
        bars = max(4, int(round(dur / (4 * 60.0 / (style[4] * 0.62)))))
        x = music.compose_ambient(style, bars=bars, seed=100 + i, transpose=(i % 5) - 2)
        x = dsp.fade(dsp.pad_to(x, dur), 400, 900)
        dsp.write_audio(os.path.join(OUT, "mystock_ui", name), x)
        dsp.write_audio(os.path.join(OUT, "oplus_ui", name), x)
        n += 2
    return n


def build_notifications():
    for target, spec in NAMED_NOTIF.items():
        dsp.write_audio(os.path.join(OUT, "notifications", target + ".ogg"),
                        notify_voice(spec))
    for i in range(1, 47):
        source = NUMBERED_POOL[(i - 1) % len(NUMBERED_POOL)]
        dsp.write_audio(
            os.path.join(OUT, "notifications", f"notification_{i:03d}.ogg"),
            notify_voice((source, 0.80, -2.0, None)),
        )
    return len(NAMED_NOTIF) + 46


def build_ringtones(names):
    for i, name in enumerate(sorted(names)):
        style = music.STYLES[i % len(music.STYLES)]
        transpose = (i // len(music.STYLES)) % 12 - 5
        bars = 8 if i % 3 == 0 else 10
        x = music.compose(style, bars=bars, seed=1000 + i, transpose=transpose,
                          bpm_scale=1.0 + ((i % 4) - 1.5) * 0.02)
        target = name if name.endswith(".ogg") else name + ".ogg"
        dsp.write_audio(os.path.join(OUT, "ringtones", target), x)
    return len(names)


def build_alarms():
    for name, style_i, trans, dur in [
        ("Rise.ogg", 2, 0, 26.0),
        ("Dynamic_Weather.ogg", 8, -3, 30.0),
    ]:
        x = music.compose_alarm(music.STYLES[style_i], seed=77 + style_i,
                                transpose=trans, total_s=dur)
        dsp.write_audio(os.path.join(OUT, "alarms", name), x)


def collect_ringtones():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "ringtones.txt"), encoding="utf-8-sig") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def main():
    import sys

    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only == "all" and os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for sub in ("product_ui", "mystock_ui", "oplus_ui", "ringtones",
                "notifications", "alarms"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    if only in ("all", "ui"):
        print(f"ui sounds: {build_ui()}", flush=True)
    if only in ("all", "notif"):
        print(f"notifications: {build_notifications()}", flush=True)
    if only in ("all", "tones"):
        print(f"ringtones: {build_ringtones(collect_ringtones())}", flush=True)
        build_alarms()
        print("alarms: 2", flush=True)


if __name__ == "__main__":
    main()
