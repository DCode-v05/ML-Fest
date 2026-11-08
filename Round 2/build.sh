#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

python manage.py setup_challenges

python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mlfest.settings')
django.setup()
from django.contrib.auth.models import User
username = os.environ.get('ADMIN_USERNAME', 'admin')
password = os.environ.get('ADMIN_PASSWORD', 'admin123')
email = os.environ.get('ADMIN_EMAIL', 'admin@mlfest.com')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser {username} created')
else:
    print(f'Superuser {username} already exists')
"
