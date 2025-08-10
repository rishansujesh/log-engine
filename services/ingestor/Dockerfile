
FROM python:3.11-slim-bookworm

RUN useradd -ms /bin/bash appuser
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app
ENV PYTHONPATH=/app

USER appuser
CMD ["python", "-m", "app.main"]
