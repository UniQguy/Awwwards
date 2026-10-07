web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 60
release: python manage.py migrate --no-input && python manage.py collectstatic --no-input
worker: python manage.py cleanup_expired_reservations
