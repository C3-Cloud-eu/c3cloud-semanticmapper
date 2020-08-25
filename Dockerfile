FROM python:3.7.3

# RUN mkdir -p /etc/nginx/sites-available/flask/

RUN echo 'deb http://deb.debian.org/debian stretch-backports main' >> /etc/apt/sources.list

RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -yq nginx nano cron 
# 	apt-get install -yq certbot python-certbot-nginx -t stretch-backports
	# DEBIAN_FRONTEND=noninteractive apt-get -yq install sqlite3 && \
	# rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN wget https://dl.eff.org/certbot-auto && \
	mv certbot-auto /usr/local/bin/certbot-auto && \
	chmod 0755 /usr/local/bin/certbot-auto

RUN echo '0 0 * * 1 /usr/local/bin/certbot-auto renew --nginx ' > /etc/cron.d/croncertbot && \
	chmod 0644 /etc/cron.d/croncertbot && \
	crontab /etc/cron.d/croncertbot && \
    cron





USER root

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# add the csv file describing the FHIR equivalence types
RUN mkdir -p /app/src/data
COPY ./data/conceptMapEquivalences.csv /app/src/data/conceptMapEquivalences.csv


#EXPOSE 5000
#EXPOSE 443
#EXPOSE 80

# error_log stderr;
RUN echo "daemon off;" >> /etc/nginx/nginx.conf


COPY ./resources/start_script.sh .
# COPY resources/nginx.conf /etc/nginx/sites-available/flask
COPY resources/nginx.conf /etc/nginx/sites-available/
COPY resources/nginx_ssl.conf /etc/nginx/sites-available/
# RUN ln -s /etc/nginx/sites-available/flask /etc/nginx/sites-enabled/flask
RUN rm -f /etc/nginx/sites-enabled/default
COPY ./src /app/src

RUN chmod +x ./start_script.sh
ENTRYPOINT ["./start_script.sh"]
# ENTRYPOINT ["bash"]

# ENTRYPOINT ["python"]
# CMD ["src/c3_cloud.py"]
