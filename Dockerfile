FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/uniqoremote src/uniqoremote

RUN pip install --no-cache-dir cryptography msgpack numpy structlog

EXPOSE 21116/udp
EXPOSE 21117/udp

CMD ["python", "-m", "uniqoremote.server"]
