FROM python:3.13-slim

WORKDIR /app

COPY . /app/

RUN pip install requests

ENTRYPOINT ["/app/entrypoint.sh"]
