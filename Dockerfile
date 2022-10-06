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

COPY supervisor/indexer.ini /etc/supervisor.d/
COPY supervisor/cacherefresher.ini /etc/supervisor.d/


# app install

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY sitemapgen.py .
COPY indexer.py .
COPY indexer.sh .
COPY cacherefresher.py .
COPY sync.sh .
COPY app /code/app
COPY redirector /code/redirector

# posar el indexer i el cacherefresher com a serveis en un sol contenidor ?

# user

RUN addgroup -g 1000 pet2cattle
RUN adduser -u 1000 -G pet2cattle -D -h /home/pet2cattle pet2cattle

RUN chown pet2cattle:pet2cattle /var/spool/cron/crontabs/pet2cattle

RUN mkdir -p /home/pet2cattle
RUN chown -R 1000:1000 /home/pet2cattle

ENV HOME /home/pet2cattle

# runtime

USER pet2cattle:pet2cattle

EXPOSE 8000

CMD [ "/usr/local/bin/gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--keep-alive", "1" ]