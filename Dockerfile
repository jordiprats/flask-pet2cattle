FROM rclone/rclone AS rclone

FROM python:3.8-alpine

RUN apk --no-cache add ca-certificates fuse tzdata git openssh && \
    echo "user_allow_other" >> /etc/fuse.conf

COPY --from=rclone /usr/local/bin/rclone /usr/local/bin/

WORKDIR /code

# GUNICORN - not an actual dependency
RUN pip install gunicorn

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app /code/app
COPY sitemapgen.py .
COPY indexer.py .
COPY sync.sh .

EXPOSE 8000

CMD [ "/usr/local/bin/gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--keep-alive", "1" ]