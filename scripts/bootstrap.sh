#!/usr/bin/env bash
set -euo pipefail

# --- Load vars (respect env overrides) ---
if [ -f ".env" ]; then
  while IFS='=' read -r key val; do
    case "$key" in
      OS_HOST|OS_USER|OS_PASSWORD|OS_TEMPLATE_NAME|OS_INDEX_PATTERN|OS_INDEX_ALIAS)
        if [ -z "${!key:-}" ]; then export "$key"="$val"; fi
      ;;
    esac
  done < <(grep -E '^(OS_HOST|OS_USER|OS_PASSWORD|OS_TEMPLATE_NAME|OS_INDEX_PATTERN|OS_INDEX_ALIAS)=' .env || true)
fi

OS_HOST="${OS_HOST:-https://localhost:9200}"
OS_USER="${OS_USER:-admin}"
OS_PASS="${OS_PASSWORD:-admin}"
OS_TEMPLATE_NAME="${OS_TEMPLATE_NAME:-logs-template}"
OS_INDEX_PATTERN="${OS_INDEX_PATTERN:-logs-*}"
OS_ALIAS="${OS_INDEX_ALIAS:-logs-write}"
TODAY_IDX="logs-$(date +%Y.%m.%d)"

# --- Wait for OpenSearch ---
echo "Waiting for OpenSearch at ${OS_HOST} ..."
for i in {1..60}; do
  if curl -sk -u "$OS_USER:$OS_PASS" "$OS_HOST/_cluster/health" >/dev/null; then break; fi
  sleep 1
done

# --- Paths ---
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
TEMPLATES_DIR="$REPO_ROOT/services/indexer/app/templates"

TEMPLATE_JSON="$TEMPLATES_DIR/index_template.json"
POLICY_JSON="$TEMPLATES_DIR/ism_policy.json"

# --- Index template ---
echo "Applying index template '$OS_TEMPLATE_NAME'..."
curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
  -X PUT "$OS_HOST/_index_template/$OS_TEMPLATE_NAME" \
  --data-binary @"$TEMPLATE_JSON" | jq -r .

# --- Create today's index if needed ---
echo "Ensuring index $TODAY_IDX exists..."
curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
  -X PUT "$OS_HOST/$TODAY_IDX" || true

# --- Repoint alias ---
echo "Repointing alias '$OS_ALIAS' -> $TODAY_IDX ..."
for i in $(curl -sk -u "$OS_USER:$OS_PASS" "$OS_HOST/_cat/aliases/$OS_ALIAS?h=index" | tr -d '\r'); do
  curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
    -X POST "$OS_HOST/_aliases" \
    -d "{\"actions\":[{\"remove\":{\"index\":\"$i\",\"alias\":\"$OS_ALIAS\"}}]}"
done
curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
  -X POST "$OS_HOST/_aliases" \
  -d "{\"actions\":[{\"add\":{\"index\":\"$TODAY_IDX\",\"alias\":\"$OS_ALIAS\",\"is_write_index\":true}}]}"

# --- Install ISM policy ---
POLICY_ID="logs-delete-after-7d"
if [ ! -f "$POLICY_JSON" ]; then
  POLICY_JSON="/tmp/ism_policy_7d.json"
  cat > "$POLICY_JSON" <<'POL'
{
  "policy": {
    "description": "Delete logs after 7 days",
    "default_state": "hot",
    "states": [
      { "name": "hot", "actions": [], "transitions": [ { "state_name": "delete", "conditions": { "min_index_age": "7d" } } ] },
      { "name": "delete", "actions": [ { "delete": {} } ], "transitions": [] }
    ],
    "ism_template": [ { "index_patterns": ["logs-*"], "priority": 100 } ]
  }
}
POL
fi
curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
  -X PUT "$OS_HOST/_plugins/_ism/policies/$POLICY_ID" \
  --data-binary @"$POLICY_JSON" || true

# --- Attach ISM policy to all matching indices ---
echo "Attaching ISM policy to $OS_INDEX_PATTERN ..."
for i in $(curl -sk -u "$OS_USER:$OS_PASS" "$OS_HOST/_cat/indices/$OS_INDEX_PATTERN?h=index" | tr -d '\r'); do
  [ -z "$i" ] && continue
  curl -sk -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
    -X POST "$OS_HOST/_plugins/_ism/add/$i" \
    -d "{\"policy_id\":\"$POLICY_ID\"}"
done

echo "Bootstrap completed."
