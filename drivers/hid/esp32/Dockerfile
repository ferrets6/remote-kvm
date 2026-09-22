FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY keymap.py server.py .

EXPOSE 8096
CMD ["python", "server.py"]
