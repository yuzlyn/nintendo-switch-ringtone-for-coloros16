#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/common.sh"

# give the stock ringtone selections back
if [ -d "$STATE" ]; then
  for _f in "$STATE"/orig_*; do
    [ -f "$_f" ] || continue
    _key=${_f##*/orig_}
    _val=$(cat "$_f")
    if [ -n "$_val" ] && [ "$_val" != "null" ]; then
      settings_put_media "$_key" "$_val" 2>/dev/null
    fi
  done
  rm -rf "$STATE"
fi

# any fallback copies made when a bind mount was impossible
[ -d "$MODDIR/.backup" ] && rm -rf "$MODDIR/.backup"

# mounts are per-boot, they disappear with the next reboot
rm -f "$LOG"
