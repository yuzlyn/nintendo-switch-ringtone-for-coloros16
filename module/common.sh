#!/system/bin/sh
# Shared helper for the Nintendo Switch sound module.

LOG=/data/adb/ns-ringtone.log

log() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> "$LOG"; }
