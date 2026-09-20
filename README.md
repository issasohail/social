# Social Welfare Center Database

Local Django application for the Social Welfare Center, with an independent database and modular organization, people, boards, case management, Family Harmony, sharing, and audit domains.

## Windows local setup

```powershell
cd E:\social
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_social_demo --confirm
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The default configuration uses SQLite so the project can be verified immediately. For local MySQL, set `DB_ENGINE=django.db.backends.mysql`, `DB_NAME=social_welfare`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `.env`. Do not reuse TMS or IVS credentials/databases.

## Checks and tests

```powershell
python manage.py check
python manage.py test
python manage.py seed_social_demo --confirm --jks-per-local 2 --profiles-per-jk 5
python manage.py remove_social_demo --dry-run
```

The demo command creates fictional records only. Never commit `.env`, media, database files, or passwords.

## Architecture

`config` owns settings/routes. `organization`, `people`, `boards`, `cases`, `family_harmony`, `sharing`, and `audit` are separate Django apps. Board and jurisdiction fields are persisted with sensitive records so server-side filtering can be extended without relying on menu visibility.

Production deployment will require a configured MySQL account, secret environment variables, HTTPS, a reverse proxy, static/media storage, and a process manager. Those deployment concerns are intentionally not configured in this local project.