#!/system/bin/sh
# Shared helpers for the Nintendo Switch sound module.

STATE=/data/adb/ns-ringtone
LOG=/data/adb/ns-ringtone.log

log() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# SettingsProvider validates media URIs against the calling app; uid 0 has no
# package and gets silently rejected, the shell (uid 2000) passes.
run_as_shell() {
  if su 2000 -c "true" >/dev/null 2>&1; then
    su 2000 -c "$1"
  else
    sh -c "$1"
  fi
}

settings_put_media() {
  _k=$1
  _v=$2
  run_as_shell "settings put system $_k '$_v'"
}

# Return the MediaStore internal audio id for a display name, or empty.
media_id() {
  content query --uri content://media/internal/audio/media \
    --projection _id:_display_name \
    --where "_display_name='$1'" 2>/dev/null \
    | sed -n 's/.*_id=\([0-9][0-9]*\).*/\1/p' | head -n 1
}

is_internal() {
  case "$1" in
    *media/internal/audio/media/*) return 0 ;;
    *) return 1 ;;
  esac
}

# set_tone <settings-key> <display-name>
set_tone() {
  _key=$1
  _name=$2
  _id=$(media_id "$_name")
  if [ -z "$_id" ]; then
    log "media id not found for $_name"
    return 1
  fi
  _uri="content://media/internal/audio/media/${_id}?title=${_name%.*}&canonical=1"
  settings_put_media "$_key" "$_uri"
  _now=$(settings get system "$_key")
  if [ "$_now" = "$_uri" ]; then
    log "set $_key = $_uri"
  else
    log "FAILED $_key (now: $_now)"
  fi
}

# Remember a setting the first time we touch it so uninstall can restore it.
remember() {
  _key=$1
  [ -f "$STATE/orig_$_key" ] && return 0
  settings get system "$_key" > "$STATE/orig_$_key" 2>/dev/null
}
