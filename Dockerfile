# TODO: Use rootless image
FROM python:3.13-slim

WORKDIR /app

COPY . /app/

RUN python3 -m pip install "requests==2.*"

ENTRYPOINT ["/app/entrypoint.sh"]
