#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/common.sh"

FILES="$MODDIR/files"
: > "$LOG"
log "=== ns-ringtone mount start ==="

# Files copied into /data/adb/modules by hand (adb push, unzip) inherit
# u:object_r:adb_data_file:s0, which no app or system_server may read -- the
# result is a completely silent phone. Force the label the stock files use.
chcon -R u:object_r:system_file:s0 "$FILES" 2>/dev/null

# Bind every replacement file over its original. The originals stay untouched
# underneath, so removing the module fully restores the stock sounds.
bind_dir() {
  _src="$1"
  _dst="$2"
  [ -d "$_src" ] || { log "src missing: $_src"; return; }
  [ -d "$_dst" ] || { log "dst missing: $_dst"; return; }
  _ok=0
  _skip=0
  _fail=0
  for _f in "$_src"/*; do
    [ -f "$_f" ] || continue
    _n=${_f##*/}
    _t="$_dst/$_n"
    if [ ! -e "$_t" ]; then
      _skip=$((_skip + 1))
      continue
    fi
    chmod 0644 "$_f" 2>/dev/null
    if mount --bind "$_f" "$_t" 2>/dev/null; then
      _ok=$((_ok + 1))
    else
      _fail=$((_fail + 1))
      log "bind failed: $_t"
    fi
  done
  log "$_dst -> ok=$_ok skip=$_skip fail=$_fail"
}

bind_dir "$FILES/product_ui"    /product/media/audio/ui
bind_dir "$FILES/mystock_ui"    /my_stock/media/audio/ui
bind_dir "$FILES/notifications" /data/oplus/multimedia/notifications

# the /data/oplus media dir has its own label in file_contexts
restorecon -R /data/oplus/multimedia/notifications 2>/dev/null

log "labels: $(ls -Z /product/media/audio/ui/KeypressStandard.ogg 2>/dev/null | awk '{print $1}')"
log "=== done ==="
