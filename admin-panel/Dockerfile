FROM python:3.12.4-slim

WORKDIR /opt/app

# Preventing creation of .pyc files and running in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE 'config.settings'

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir

RUN apt-get update && \
    apt-get install netcat-traditional \
    -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN chmod +x start.sh

EXPOSE 8000

ENTRYPOINT [ "sh", "-c", "./start.sh" ]