#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/common.sh"

CONF="$MODDIR/data/sounds.conf"
LIB="$MODDIR/webroot/sounds"
: > "$LOG"
log "=== ns-ringtone mount start ==="

[ -f "$CONF" ] || { log "config missing: $CONF"; exit 0; }

: > "$MODDIR/data/missing.list" 2>/dev/null

# Files copied into /data/adb/modules by hand (adb push, unzip) inherit
# u:object_r:adb_data_file:s0, which no app or system_server may read -- the
# result is a completely silent phone. Force the label the stock files use.
chcon -R u:object_r:system_file:s0 "$LIB" 2>/dev/null

# Where each group used to live. ColorOS 17 moved the UI set from my_stock to
# my_product, so every group is probed in order and the first directory that
# actually holds the target file wins.
dirs_for() {
  case "$1" in
    product_ui)    echo "/my_product/media/audio/ui /product/media/audio/ui" ;;
    mystock_ui)    echo "/my_product/media/audio/ui /my_stock/media/audio/ui /system/media/audio/ui" ;;
    notifications) echo "/data/oplus/multimedia/notifications /data/oplus/media/notifications /my_product/media/audio/notifications" ;;
    *) return 1 ;;
  esac
}

resolve_dir() {
  for _d in $(dirs_for "$1"); do
    if [ -e "$_d/$2" ]; then
      echo "$_d"
      return 0
    fi
  done
  return 1
}

bound=" "
ok=0
skip=0
fail=0
enabled=0

while IFS= read -r line; do
  case "$line" in ''|'#'*) continue ;; esac
  slot=${line%%=*}
  id=${line#*=}
  case "$slot" in */*) ;; *) continue ;; esac
  group=${slot%%/*}
  target=${slot#*/}

  case "$id" in ''|'-')
    skip=$((skip + 1))
    continue
    ;;
  esac
  enabled=$((enabled + 1))

  src="$LIB/$id.ogg"
  if [ ! -f "$src" ]; then
    skip=$((skip + 1))
    log "missing sound: $id"
    continue
  fi

  if ! dst_dir=$(resolve_dir "$group" "$target"); then
    skip=$((skip + 1))
    log "no target for: $slot"
    printf '%s\n' "$slot" >> "$MODDIR/data/missing.list"
    continue
  fi

  dst="$dst_dir/$target"
  case "$bound" in *" $dst "*) continue ;; esac
  if mount --bind "$src" "$dst" 2>/dev/null; then
    ok=$((ok + 1))
    bound="$bound$dst "
  else
    fail=$((fail + 1))
    log "bind failed: $dst"
  fi
done < "$CONF"

# the /data/oplus media dir has its own label in file_contexts
for _d in /data/oplus/multimedia/notifications /data/oplus/media/notifications; do
  [ -d "$_d" ] && restorecon -R "$_d" 2>/dev/null
done

log "enabled=$enabled ok=$ok skip=$skip fail=$fail"
_first=$(printf '%s' "$bound" | awk '{print $1}')
[ -n "$_first" ] && log "label($_first): $(ls -Z "$_first" 2>/dev/null | awk '{print $1}')"
log "=== done ==="
