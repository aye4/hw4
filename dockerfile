FROM python:3.10-alpine

WORKDIR /usr/test

COPY . /usr/test

EXPOSE 3000

cmd ["python", "main.py"]
