FROM python:3.9-slim
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . .
RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt
# workers=1 keeps in-memory Socket.IO broadcasts correct without Redis.
# Under gthread, each long-lived WebSocket holds a request thread, so keep
# a high thread pool (matches prior prod capacity) for WS + GraphQL/health.
CMD gunicorn app:app -b 0.0.0.0:8000 \
    --worker-class gthread \
    --workers 1 \
    --threads 100 \
    --timeout 60 \
    --graceful-timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 200
