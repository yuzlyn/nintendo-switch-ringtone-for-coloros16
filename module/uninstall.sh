#!/system/bin/sh
MODDIR=${0%/*}

# All mounts are per-boot, they disappear with the next reboot. The stock
# files were never modified, so there is nothing to restore.
rm -f /data/adb/ns-ringtone.log
rm -rf /data/adb/ns-ringtone
[ -d "$MODDIR/.backup" ] && rm -rf "$MODDIR/.backup"
