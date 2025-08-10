#!/usr/bin/env bash
set -euo pipefail

API_USER=${API_BASIC_USER:-admin}
API_PASS=${API_BASIC_PASS:-admin}
OS_USER=${OS_USER:-admin}
OS_PASS=${OS_PASSWORD:-admin}

echo "== Healthchecks =="
curl -s "http://localhost:8080/" | jq .
curl -s -u "$API_USER:$API_PASS" "http://localhost:8080/healthz" | jq .
curl -sk -u "$OS_USER:$OS_PASS" "https://localhost:9200/_cluster/health" | jq .

echo "== Ingest NDJSON =="
cat > /tmp/sample.ndjson <<'NDJ'
{"@timestamp":"2025-01-01T10:00:00Z","level":"info","service":"checkout","env":"dev","host":"local","message":"cart opened","labels":{"session":"s1"}}
{"@timestamp":"2025-01-01T10:00:02Z","level":"warn","service":"checkout","env":"dev","host":"local","message":"slow payment","fields":{"latency_ms":900}}
{"@timestamp":"2025-01-01T10:00:04Z","level":"error","service":"payments","env":"dev","host":"local","message":"stripe boom","labels":{"provider":"stripe"}}
NDJ
curl -s -u "$API_USER:$API_PASS" -H 'Content-Type: application/x-ndjson' --data-binary @/tmp/sample.ndjson "http://localhost:8080/ingest/logs" | jq .

echo "== Ingest JSON array =="
cat > /tmp/sample.json <<'JSON'
[
  {"@timestamp":"2025-01-01T10:01:00Z","level":"debug","service":"auth","env":"dev","host":"local","message":"cache warm"},
  {"@timestamp":"2025-01-01T10:01:02Z","level":"info","service":"orders","env":"dev","host":"local","message":"order placed","labels":{"order_id":"X42"}}
]
JSON
curl -s -u "$API_USER:$API_PASS" -H 'Content-Type: application/json' --data @/tmp/sample.json "http://localhost:8080/ingest/logs" | jq .

sleep 2

echo "== Query: match_all (last 5) =="
curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
  -X GET "https://localhost:9200/logs-*/_search?size=5&sort=@timestamp:desc" \
  -d '{"query":{"match_all":{}}}' | jq '.hits.total,.hits.hits[]._source'

echo "== Query via API: level=error =="
curl -s -u "$API_USER:$API_PASS" "http://localhost:8080/query?level=error&size=5" | jq .

echo "== Query via API: service=checkout (since 2025-01-01T09:59:00Z) =="
curl -s -u "$API_USER:$API_PASS" "http://localhost:8080/query?service=checkout&from=2025-01-01T09:59:00Z&size=5" | jq .

echo "== Query via API: full-text 'stripe' =="
curl -s -u "$API_USER:$API_PASS" "http://localhost:8080/query?q=stripe&size=5" | jq .
