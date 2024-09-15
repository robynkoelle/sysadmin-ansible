#!/bin/bash

# Backup directory
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="{{ postgresql.backup_directory }}"
LOG_FILE="{{ postgresql.backup_directory }}/backup_log_$DATE.log"

# Backup file name
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Create a dump of all databases and log output
{
    echo "[$DATE] Starting backup..."

    sudo -u postgres /usr/bin/pg_dumpall > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo "[$DATE] Backup successfully created: $BACKUP_FILE"
    else
        echo "[$DATE] Error creating backup"
        exit 1
    fi

} >> "$LOG_FILE" 2>&1
