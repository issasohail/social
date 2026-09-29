# Social Family Harmony update

This update adds a migration-seeded Central Regional Council hierarchy, configurable marriage-profile dropdown lists, a complete public marriage-profile form, duplicate-ID checking, multi-select prospective-match preferences, a one-page US Letter PDF profile, seven-day share defaults, WhatsApp sharing, and a Social backup script.

The six requested Central Region local councils are seeded. Because actual Jamatkhana names/codes were not supplied, four clearly identifiable placeholder Jamatkhanas are seeded under each local council using the requested `Jamatkhana_<council>_01xx` pattern. Replace them in Settings when the official names are available.

The uploaded two-page Marriage Profile Submission Form was used as the field/content baseline. Sensitive contact/ID/address information is collected internally but intentionally omitted from the share-oriented PDF where practical.

## After applying

```powershell
py manage.py migrate
py manage.py check
py manage.py collectstatic --noinput
```

For production under `/social`, set `FORCE_SCRIPT_NAME=/social` in the production environment if the reverse proxy does not already provide the script prefix.

## Backup

Run `backup_social_for_chatgpt.ps1` from the Social repository. It excludes `.env` and Git metadata, can include the full database and uploaded media, and keeps the latest three Social backup ZIPs. Full database/media backups can contain confidential personal data and should be handled as restricted files.

## Organization CRUD follow-up

Regional Council, Local Council, and Jamatkhana Settings lists now support create, read/list, inline update, and delete/deactivate behavior, with serial numbers and search/status/hierarchy filters. Seeded Central Region Jamatkhanas use clearly fake names such as `Rawalpindi Jamatkhana 01` through `04` rather than pretending to be official names.

Family Harmony profile sharing uses Django URL reversing plus `request.build_absolute_uri`, so production `/social` prefixes are retained. The recipient route itself is public/token-based and has no login decorator: the recipient does not need a Social username or password. The random token, expiry, view limit and normal share validation remain the access control.
