#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate

# Check if a superuser should be created
if [[ $CREATE_SUPERUSER ]]; 
then
    python manage.py createsuperuser --no-input --email "$DJANGO_SUPERUSER_EMAIL"
fi