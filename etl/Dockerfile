FROM python:3.12.5-slim

WORKDIR /opt/app

# Preventing creation of .pyc files and running in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN apt-get update && \
    apt-get install netcat-traditional \
    -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir

COPY . .
RUN chmod +x start.sh

ENTRYPOINT [ "sh", "-c", "./start.sh" ]
