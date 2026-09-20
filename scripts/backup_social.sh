#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=/home/ivs/backups/social
MEDIA_DIR=/home/ivs/social_media
MYSQL_CONFIG=/home/ivs/.social-my.cnf
LOCK_FILE=/home/ivs/apps/social/logs/backup-social.lock
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE=/home/ivs/apps/social/logs/backup-social.log

mkdir -p "$BACKUP_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || { printf '%s backup already running\n' "$(date --iso-8601=seconds)" >> "$LOG_FILE"; exit 1; }
exec >>"$LOG_FILE" 2>&1
printf '%s backup started\n' "$(date --iso-8601=seconds)"

mysqldump --defaults-extra-file="$MYSQL_CONFIG" --single-transaction --quick --routines --triggers social_welfare | gzip -9 > "$BACKUP_DIR/social_welfare-$TIMESTAMP.sql.gz"
tar -C "$MEDIA_DIR" -czf "$BACKUP_DIR/social-media-$TIMESTAMP.tar.gz" .

find "$BACKUP_DIR" -type f -mtime +30 -delete
printf '%s backup completed\n' "$(date --iso-8601=seconds)"
