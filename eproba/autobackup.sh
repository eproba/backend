#!/bin/sh
# only run this script if the ENABLE_AUTOBACKUP environment variable is set to 'true'
if [ "$ENABLE_AUTOBACKUP" = "true" ]; then
  echo "$(date) Running automatic backup" >> /var/log/cron/backups.log 2>&1
  python /home/app/web/manage.py dbbackup --noinput --compress --clean
fi
