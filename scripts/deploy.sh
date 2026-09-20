#!/usr/bin/env bash
set -euo pipefail

cd /home/ivs/apps/social

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Production worktree contains local changes. Deployment stopped." >&2
    git status --short >&2
    exit 1
fi

source .venv/bin/activate
git fetch origin
git pull --ff-only origin main
python -m pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check
python manage.py test
sudo systemctl restart social-welfare.service
sudo systemctl status social-welfare.service --no-pager
