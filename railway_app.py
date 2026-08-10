#!/usr/bin/env python
"""
Runs migrations, collects static files, then starts Django under gunicorn.
"""
import os
import subprocess
import sys

DJANGO_PORT = int(os.environ.get('PORT', 8080))


def run_migrations():
    print("Running migrations...")
    result = subprocess.run(['python', 'manage.py', 'migrate', '--noinput'])
    if result.returncode != 0:
        sys.exit(1)


def collect_static():
    print("Collecting static files...")
    result = subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'])
    if result.returncode != 0:
        sys.exit(1)


def run_django():
    print(f"Starting Django on port {DJANGO_PORT}")
    cmd = [
        'gunicorn', 'crwn.wsgi:application',
        '--bind', f'0.0.0.0:{DJANGO_PORT}',
        '--workers', '1',
        '--threads', '1',
        '--timeout', '120',
        '--access-logfile', '-',
        '--error-logfile', '-',
    ]
    os.execvp('gunicorn', cmd)


if __name__ == '__main__':
    run_migrations()
    collect_static()
    run_django()
