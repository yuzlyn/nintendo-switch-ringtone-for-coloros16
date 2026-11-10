#!/system/bin/sh
# soundctl.sh - Nintendo Switch 音效模块控制脚本
# 用法:
#   soundctl status                  输出 key=value 状态（供 WebUI 读取）
#   soundctl slots                   输出全部槽位的当前映射：<group>/<file>=<id|->
#   soundctl set <slot> <id|->       设置某个槽位使用哪个音效，"-" 表示保持原声
#   soundctl reset                   恢复默认映射
#   soundctl library                 输出音效库清单：<id>=<时长ms>

MODDIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$MODDIR/data"
CONF="$DATA/sounds.conf"
DEFAULT_CONF="$DATA/sounds.default.conf"
LIB="$MODDIR/webroot/sounds"
PENDING="$DATA/pending_reboot"

valid_slot() {
  case "$1" in
    product_ui/*|mystock_ui/*|notifications/*) ;;
    *) return 1 ;;
  esac
  case "$1" in
    */*/*|*/../*|*/.. ) return 1 ;;
  esac
  [ -n "$1" ]
}

valid_id() {
  [ "$1" = "-" ] && return 0
  case "$1" in
    ''|*/*|*[!A-Za-z0-9._-]*) return 1 ;;
  esac
  return 0
}

write_slot() {
  slot="$1"
  id="$2"
  tmp="$DATA/.sounds.conf.new"
  found=0
  : > "$tmp" || exit 1
  if [ -f "$CONF" ]; then
    while IFS= read -r line; do
      case "$line" in
        ''|'#'*)
          printf '%s\n' "$line" >> "$tmp"
          continue
          ;;
      esac
      case "$line" in
        "$slot="*)
          printf '%s=%s\n' "$slot" "$id" >> "$tmp"
          found=1
          ;;
        *) printf '%s\n' "$line" >> "$tmp" ;;
      esac
    done < "$CONF"
  fi
  [ "$found" = "1" ] || printf '%s=%s\n' "$slot" "$id" >> "$tmp"
  mv -f "$tmp" "$CONF" || exit 1
  chmod 0644 "$CONF"
}

cmd_status() {
  total=0
  enabled=0
  if [ -f "$CONF" ]; then
    while IFS= read -r line; do
      case "$line" in ''|'#'*) continue ;; esac
      case "$line" in *=*) ;; *) continue ;; esac
      total=$((total + 1))
      case "${line#*=}" in ''|'-') ;; *) enabled=$((enabled + 1)) ;; esac
    done < "$CONF"
  fi
  library=0
  [ -f "$LIB/index.tsv" ] && library=$(grep -c . "$LIB/index.tsv" 2>/dev/null)
  [ -z "$library" ] && library=0

  missing=0
  [ -f "$DATA/missing.list" ] && missing=$(grep -c . "$DATA/missing.list" 2>/dev/null)
  [ -z "$missing" ] && missing=0

  echo "total=$total"
  echo "enabled=$enabled"
  echo "library=$library"
  echo "missing=$missing"
  echo "pending_reboot=$([ -f "$PENDING" ] && echo 1 || echo 0)"
  echo "converter=bind_mount"
}

cmd_missing() {
  [ -f "$DATA/missing.list" ] && cat "$DATA/missing.list" 2>/dev/null
}

# One round trip for the WebUI: every CGI call costs a shell fork, and four of
# them in sequence is what made the page feel stuck on first load.
cmd_snapshot() {
  echo "#status"
  cmd_status
  echo "#slots"
  cmd_slots
  echo "#missing"
  cmd_missing
  echo "#library"
  [ -f "$LIB/index.tsv" ] && cat "$LIB/index.tsv"
  return 0
}

cmd_slots() {
  [ -f "$CONF" ] || return 0
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    case "$line" in *=*) printf '%s\n' "$line" ;; esac
  done < "$CONF"
}

cmd_library() {
  [ -f "$LIB/index.tsv" ] || return 0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    ms=$(printf '%s' "$line" | cut -f3)
    id=$(printf '%s' "$line" | cut -f1)
    [ -n "$id" ] && echo "$id=${ms:-0}"
  done < "$LIB/index.tsv"
}

cmd_set() {
  slot="$1"
  id="$2"
  valid_slot "$slot" || { echo "ERROR invalid_slot"; exit 1; }
  valid_id "$id" || { echo "ERROR invalid_id"; exit 1; }
  if [ "$id" != "-" ] && [ ! -f "$LIB/$id.ogg" ]; then
    echo "ERROR sound_not_found"
    exit 1
  fi
  write_slot "$slot" "$id" || { echo "ERROR write_failed"; exit 1; }
  touch "$PENDING"
  sync
  echo "ok=set"
}

cmd_reset() {
  [ -f "$DEFAULT_CONF" ] || { echo "ERROR default_missing"; exit 1; }
  cp -f "$DEFAULT_CONF" "$CONF" || { echo "ERROR write_failed"; exit 1; }
  chmod 0644 "$CONF"
  touch "$PENDING"
  sync
  echo "ok=reset"
}

case "$1" in
  status) cmd_status ;;
  slots) cmd_slots ;;
  missing) cmd_missing ;;
  library) cmd_library ;;
  snapshot) cmd_snapshot ;;
  set) cmd_set "$2" "$3" ;;
  reset) cmd_reset ;;
  *)
    echo "usage: soundctl status|slots|library|set|reset"
    exit 2
    ;;
esac
exit 0
