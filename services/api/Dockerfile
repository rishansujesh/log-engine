FROM python:3.11-slim-bookworm

RUN useradd -ms /bin/bash appuser
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates bash && rm -rf /var/lib/apt/lists/*

# Install deps first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the application source
COPY . /app
ENV PYTHONPATH=/app

USER appuser
EXPOSE 8080

# Default command (compose already overrides to uvicorn, but this is safe)
CMD ["uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
