FROM rclone/rclone AS rclone

FROM python:3.8-alpine

RUN apk --no-cache add ca-certificates fuse tzdata git openssh supervisor && \
    echo "user_allow_other" >> /etc/fuse.conf

COPY --from=rclone /usr/local/bin/rclone /usr/local/bin/

WORKDIR /code

# update pip
RUN python -m pip install --upgrade pip

# GUNICORN - not an actual dependency
RUN pip install gunicorn

# supervisor config

COPY supervisor/supervisord.conf /etc/supervisord.conf
RUN mkdir -p /etc/supervisor.d/

COPY supervisor/crond.ini /etc/supervisor.d/
COPY supervisor/cacherefresher.ini /etc/supervisor.d/


# app install

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY sitemapgen.py .
COPY indexer.py .
COPY cacherefresher.py .
COPY sync.sh .
COPY app /code/app
COPY redirector /code/redirector

RUN echo "0 0 * * * python /code/indexer.py" | crontab -u root -

# posar el indexer i el cacherefresher com a serveis en un sol contenidor ?

EXPOSE 8000

CMD [ "/usr/local/bin/gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--keep-alive", "1" ]