FROM python:3.8-alpine

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY sillyhttpsredirector.py .

EXPOSE 9000

#TODO: gunicorn
CMD [ "flask", "run", "-p", '9000' ] 