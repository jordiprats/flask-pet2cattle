FROM python:3.8-alpine

WORKDIR /code

# GUNICORN - not an actual dependency
RUN pip install gunicorn

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app /code/app

EXPOSE 8000

CMD [ "/usr/local/bin/gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--keep-alive", "1" ]