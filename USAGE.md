Clone the Repository

git clone https://github.com/rishansujesh/<your-repo-name>.git
cd <your-repo-name>

KAFKA_BROKER=kafka:9092
OPENSEARCH_HOST=https://opensearch:9200

docker compose up -d

OS_HOST=https://localhost:9200 bash scripts/bootstrap.sh

##Ingest Sample Logs##

curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "@timestamp": "2025-08-10T12:00:00Z",
    "service": "api-gateway",
    "level": "error",
    "message": "Downstream timeout"
  }'

 ##Query Logs##
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "api-gateway",
    "level": "error",
    "start_time": "2025-08-10T00:00:00Z",
    "end_time": "2025-08-10T23:59:59Z"
  }'

Example Use Case
Imagine you run a multi-service SaaS platform.
When a customer reports “the app feels slow,” you can:

Ingest logs from all services via this pipeline

Search for error spikes or slow downstream calls across services

Use dashboards to pinpoint which service and when it started failing

Quickly deploy a fix

This architecture mirrors production log analytics platforms (like ELK/OpenSearch stacks at scale).
