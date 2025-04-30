FROM python:3.9-slim
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . .
RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt
CMD gunicorn app:app -b 0.0.0.0:8000 --workers 2 --worker-class gevent --timeout 60 --max-requests 1000 --max-requests-jitter 200
