# Social Welfare Production Restore

These steps apply only to Social Welfare resources. Do not run them against IVS or TMS.

## Stop the service

```bash
sudo systemctl stop social-welfare.service
```

## Restore the database

1. Confirm the dump is a trusted Social Welfare backup under `/home/ivs/backups/social/`.
2. Decompress it to a temporary file outside the public application tree.
3. Restore it to the existing `social_welfare` database using the protected Social MySQL credentials:

```bash
gzip -dc /path/to/social_welfare-TIMESTAMP.sql.gz | mysql --defaults-extra-file=/home/ivs/.social-my.cnf social_welfare
```

Do not drop or recreate the database as part of routine restoration.

## Restore media

```bash
sudo tar -C /home/ivs/social_media -xzf /path/to/social-media-TIMESTAMP.tar.gz
sudo chown -R ivs:ivs /home/ivs/social_media
```

## Check and restart

```bash
cd /home/ivs/apps/social
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl start social-welfare.service
sudo systemctl status social-welfare.service --no-pager
```

Verify `/health/` and the login page through the production HTTPS URL.
