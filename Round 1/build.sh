#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

python manage.py import_questions

python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mlfest.settings')
django.setup()
from django.contrib.auth.models import User
username = os.environ.get('ADMIN_USERNAME', 'teamqernels@gmail.com')
password = os.environ.get('ADMIN_PASSWORD', 'teamqernels@iQube42')
email = os.environ.get('ADMIN_EMAIL', 'teamqernels@gmail.com')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser {username} created')
else:
    print(f'Superuser {username} already exists')
"
