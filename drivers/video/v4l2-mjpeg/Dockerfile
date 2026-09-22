FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server.py ./

EXPOSE 8091
CMD ["python3", "server.py"]
