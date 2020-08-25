#!/bin/bash

if [[ "$1" != "test" ]]; then
	echo "starting nginx ssl"
	suffix="_ssl"
else
	echo "starting nginx without ssl"
fi

ln -s "/etc/nginx/sites-available/nginx$suffix.conf" "/etc/nginx/sites-enabled/flask"

echo Starting Gunicorn.
exec gunicorn wsgi \
	 --chdir src \
     --bind=unix:/app/sock.sock \
	 --log-level debug \
     --workers 1 \
	 --access-logfile /app/gunicorn.log \
	 --log-level debug &

echo Starting nginx
exec service nginx start

echo Starting cron
cron

echo "Done."
