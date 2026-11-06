"""Build the replacement audio assets for the NS-Ringtone module.

Every output is a single, unmodified Nintendo Switch firmware sample: the
source is only trimmed of silence and gain-matched.  Nothing is synthesised,
concatenated or layered.
"""
import os
import shutil
import numpy as np

import dsp

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


def raw(source, peak_db=-7.0):
    """Just the original sample: trim silence, set the level. Nothing else."""
    x = dsp.trim(src(source).copy(), thresh_db=-50.0, pad_ms=4)
    return dsp.normalize_peak(x, ceiling_db=peak_db)


def unlock_press(source="SeUnlock", peak_db=-7.5, tail=0.03, lp=5000):
    """Wake-screen button press shape: the sample, softened a little."""
    x = dsp.trim(src(source).copy(), thresh_db=-50.0, pad_ms=4)
    x = dsp.lowpass(x, lp)
    if tail:
        x = np.pad(x, (0, int(dsp.SR * tail)))
        x = dsp.reverb(x, wet=0.14, size_ms=40, taps=4)
    x = dsp.fade(x, 0, 12)
    return dsp.normalize_peak(x, ceiling_db=peak_db)


def joycon_charge():
    """Soft mechanical 'clack' plus a warm two note lift: the Joy-Con rail."""
    buf = np.zeros(int(dsp.SR * 0.95), dtype=np.float32)
    dsp.mix_into(buf, dsp.voice_noise(0.045, amp=0.16, decay=150, cut=3800), 0.005)
    dsp.mix_into(buf, dsp.voice_tri(45, 0.10, amp=0.22, a=0.001, r=0.05), 0.005)
    for k, m in enumerate([76, 83]):
        sig = dsp.voice_bell(m, 0.75, amp=0.22, decay=4.6)
        sig = dsp.reverb(sig, wet=0.14, size_ms=60, taps=6)
        dsp.mix_into(buf, sig, 0.10 + k * 0.115)
    return dsp.normalize_peak(buf, ceiling_db=-8.0)


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
    "Lock":                ("__sleep", 0, 0, None),
    "LowBattery":          ("SeWarning_Dtt", 0.30, -5.0, 7000),
    "Screenshots":         ("SeCheckBtnPressFinish", 0.16, -7.0, 6000),
    "Undock":              ("SeVgcCard_Eject", 0.45, -8.0, 5000),
    "Unlock":              ("__unlock", 0, 0, None),
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
    "VolumePanelSound.ogg":          ("SeVgcCard_Move", 0.16, -5.0, 5200),
    "WheelPicker.ogg":               ("SeVgcCard_Move", 0.16, -6.0, 5200),
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
    "Alert":            ("SeNewsBad", 0.60, -1.0, None),
    "Anticipate":       ("SeUnlockKeyL", 0.55, -1.0, None),
    "Bell":             ("SeVgcBtnCard_Decide", 0.60, -1.0, None),
    "Bloom":            ("SeSelectCheck", 0.60, -1.0, None),
    "Calypso":          ("SeBtnFocus", 0.55, -1.0, None),
    "Chime":            ("SeDialogPtclRating", 0.70, -1.0, None),
    "Choo Choo":        ("SeVgc_Paring_Guide", 0.80, -1.0, None),
    "ct-error":         ("SeVgc_Error", 0.80, -1.0, None),
    "Descent":          ("SeSelectUncheck", 0.60, -1.0, None),
    "Ding":             ("SeSuccess", 0.30, -0.5, None),
    "Electronic":       ("SeGameIconEffect", 0.25, -1.0, None),
    "Fanfare":          ("SeDialogParentalControllOn", 0.75, -1.0, None),
    "Glass":            ("SeNewsNice", 0.22, -1.0, None),
    "Horn":             ("SeVgcCard_Eject_Start", 0.60, -1.0, None),
    "Ladder":           ("SeBatteryRateIn", 0.22, -1.0, None),
    "Minuet":           ("StartupNews", 0.85, -0.5, None),
    "News Flash":       ("SeNewsChannelRegister", 0.25, -1.0, None),
    "Noir":             ("SeKeyErrorTouch", 0.60, -1.0, None),
    "Sherwood Forest":  ("SeDeviceFound_Dtt", 0.75, -1.0, None),
    "Spell":            ("SeVgc_Paring_Fix", 0.75, -1.0, None),
    "Suspense":         ("SeVgcCard_Appear_01", 0.22, -1.0, None),
    "Swish":            ("SeFlcIconLoadedInner", 0.22, -1.0, None),
    "Swoosh":           ("SeVgcCard_Overlap_Short", 0.25, -1.0, None),
    "Telegraph":        ("SeMeterKeyDecide", 0.60, -1.0, None),
    "Tiptoes":          ("SeNewsBookmark", 0.22, -1.0, None),
    "Tri-Tone":         ("StartupAlbum", 0.85, -0.5, None),
    "Tweet":            ("SeSelectFocus", 0.25, -1.0, None),
    "Typewriters":      ("SeKeyRecieved", 0.60, -1.0, None),
    "Update":           ("StartupVgc", 0.25, -1.0, None),
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

CUSTOM = {
    # 固件原样输出
    "__sleep": lambda: raw("StartupSleep", -7.0),
    "__unlock": lambda: raw("SeUnlock", -7.0),
    # 唤醒画面按键音（点击）
    "__u_a": lambda: unlock_press("SeUnlock", -7.5, 0.03, 5000),
    "__u_zl": lambda: unlock_press("SeUnlockKeyZL", -7.5, 0.03, 5000),
    "__u_minus": lambda: unlock_press("SeUnlockMinus", -8.5, 0.03, 5000),
    "__u_plus": lambda: unlock_press("SeUnlockPlus", -8.5, 0.03, 5000),
    "__u_soft": lambda: unlock_press("SeUnlock", -10.0, 0.03, 4500),
    # 充电音：按用户要求保持不变
    "__charge": joycon_charge,
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
    return n


def build_notifications():
    for target, spec in NAMED_NOTIF.items():
        dsp.write_audio(os.path.join(OUT, "notifications", target + ".ogg"),
                        render(spec))
    for i in range(1, 47):
        source = NUMBERED_POOL[(i - 1) % len(NUMBERED_POOL)]
        dsp.write_audio(
            os.path.join(OUT, "notifications", f"notification_{i:03d}.ogg"),
            sfx(source, 0.80, -1.0, None),
        )
    return len(NAMED_NOTIF) + 46


def main():
    import sys

    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only == "all" and os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for sub in ("product_ui", "mystock_ui", "notifications"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    if only in ("all", "ui"):
        print(f"ui sounds: {build_ui()}", flush=True)
    if only in ("all", "notif"):
        print(f"notifications: {build_notifications()}", flush=True)


if __name__ == "__main__":
    main()
