FROM python:3.9-slim
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . .
RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt
# workers=1 keeps in-memory Socket.IO broadcasts correct without Redis.
# gthread + threads give request concurrency so live scrape / slow handlers
# cannot stall every other request the way a single sync worker did.
CMD gunicorn app:app -b 0.0.0.0:8000 \
    --worker-class gthread \
    --workers 1 \
    --threads 8 \
    --timeout 60 \
    --graceful-timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 200
