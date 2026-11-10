#!/system/bin/sh

ui_print "*******************************"
ui_print " Nintendo Switch 音效"
ui_print " by yuzlyn"
ui_print "*******************************"

sdk="$(getprop ro.build.version.sdk)"
case "$sdk" in ''|*[!0-9]*) abort "! 无法读取 Android API 版本" ;; esac
[ "$sdk" -ge 26 ] || abort "! 仅支持 Android 8.0 及以上版本（API 26+）"

# 模块更新时保留用户已经调好的开关与音效选择。
OLDMOD="/data/adb/modules/ns-ringtone"
if [ -f "$OLDMOD/data/sounds.conf" ]; then
  ui_print "- 保留已有的音效选择"
  mkdir -p "$MODPATH/data"
  cp -af "$OLDMOD/data/sounds.conf" "$MODPATH/data/sounds.conf"
fi

set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm "$MODPATH/customize.sh" 0 0 0755
set_perm "$MODPATH/post-fs-data.sh" 0 0 0755
set_perm "$MODPATH/service.sh" 0 0 0755
set_perm "$MODPATH/uninstall.sh" 0 0 0755
set_perm "$MODPATH/tools/soundctl.sh" 0 0 0755
chmod 0755 "$MODPATH/webroot/cgi-bin/exec"

slots=$(grep -c '=' "$MODPATH/data/sounds.conf" 2>/dev/null)
sounds=$(ls "$MODPATH/webroot/sounds" 2>/dev/null | grep -c '\.ogg$')
ui_print "- 音效库：$sounds 个可选音效"
ui_print "- 替换槽位：$slots 项"
ui_print "- 安装完成，重启后生效"
ui_print "- 在 KernelSU 模块页面点击 WebUI 逐个开关并选择音效"
