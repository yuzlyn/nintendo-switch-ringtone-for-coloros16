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
#
# ColorOS 17 moved the UI sound set between partitions (the same audio files
# now live under /my_product/media/audio), so each set lists every location it
# has shipped in. Directories that do not exist are skipped, and the log records
# which ones were actually used.
bound_files=" "
bound_dirs=""
total_ok=0
total_skip=0
total_fail=0

bind_dir() {
  _src="$1"
  _dst="$2"
  [ -d "$_src" ] || return 1
  [ -d "$_dst" ] || return 1
  _ok=0
  _skip=0
  _fail=0
  for _f in "$_src"/*; do
    [ -f "$_f" ] || continue
    _n=${_f##*/}
    _t="$_dst/$_n"
    case "$bound_files" in *" $_t "*) continue ;; esac
    if [ ! -e "$_t" ]; then
      _skip=$((_skip + 1))
      continue
    fi
    chmod 0644 "$_f" 2>/dev/null
    if mount --bind "$_f" "$_t" 2>/dev/null; then
      _ok=$((_ok + 1))
      bound_files="$bound_files$_t "
    else
      _fail=$((_fail + 1))
      log "bind failed: $_t"
    fi
  done
  total_ok=$((total_ok + _ok))
  total_skip=$((total_skip + _skip))
  total_fail=$((total_fail + _fail))
  bound_dirs="$bound_dirs $_dst"
  log "$_dst -> ok=$_ok skip=$_skip fail=$_fail"
  return 0
}

bind_group() {
  _src="$1"
  shift
  _used=0
  for _dst in "$@"; do
    bind_dir "$_src" "$_dst" && _used=1
  done
  [ "$_used" = "1" ] || log "no target dir for ${_src##*/}"
}

bind_group "$FILES/product_ui" \
  /my_product/media/audio/ui \
  /product/media/audio/ui

bind_group "$FILES/mystock_ui" \
  /my_product/media/audio/ui \
  /my_stock/media/audio/ui \
  /system/media/audio/ui

bind_group "$FILES/notifications" \
  /data/oplus/multimedia/notifications \
  /data/oplus/media/notifications \
  /my_product/media/audio/notifications

# the /data/oplus media dir has its own label in file_contexts
for _d in /data/oplus/multimedia/notifications /data/oplus/media/notifications; do
  [ -d "$_d" ] && restorecon -R "$_d" 2>/dev/null
done

log "dirs:$bound_dirs"
log "total: ok=$total_ok skip=$total_skip fail=$total_fail"
_first=$(printf '%s' "$bound_files" | awk '{print $1}')
[ -n "$_first" ] && log "label($_first): $(ls -Z "$_first" 2>/dev/null | awk '{print $1}')"
log "=== done ==="
