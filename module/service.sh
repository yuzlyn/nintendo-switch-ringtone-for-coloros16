#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/common.sh"

MARK="$STATE/applied_v1"
[ -f "$MARK" ] && exit 0

mkdir -p "$STATE"

# wait for the framework so SettingsProvider / MediaProvider are usable
_i=0
while [ "$_i" -lt 120 ]; do
  [ "$(getprop sys.boot_completed)" = "1" ] && break
  sleep 2
  _i=$((_i + 1))
done
sleep 5

remember ringtone
remember notification_sound
remember alarm_alert
remember oplus_customize_default_ringtone
remember oplus_customize_default_alarm
remember oplus_customize_default_sms_notification_sound

# The user may be pointing at a file on /sdcard, which we cannot replace.
# Only rewrite the selections that are not already served from the stock
# ringtone database (those have already been swapped by the bind mounts).
_rt=$(settings get system ringtone)
if is_internal "$_rt"; then
  log "ringtone already internal, keep"
else
  set_tone ringtone "ringtone_001.ogg"
  set_tone oplus_customize_default_ringtone "ringtone_001.ogg"
  set_tone oplus_customize_default_ringtone_sim2 "ringtone_001.ogg"
fi

_al=$(settings get system alarm_alert)
if is_internal "$_al"; then
  log "alarm already internal, keep"
else
  set_tone alarm_alert "ringtone_035.ogg"
  set_tone oplus_customize_default_alarm "ringtone_035.ogg"
fi

_nt=$(settings get system notification_sound)
if is_internal "$_nt"; then
  log "notification already internal, keep"
else
  set_tone notification_sound "notification_002.ogg"
  set_tone oplus_customize_default_sms_notification_sound "notification_001.ogg"
fi

touch "$MARK"
log "=== defaults applied ==="
