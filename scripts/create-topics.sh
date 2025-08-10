#!/usr/bin/env bash
set -euo pipefail

BROKER="kafka:9092"
KAFKA_TOPICS_BIN="/opt/bitnami/kafka/bin/kafka-topics.sh"

in_container() {
  docker compose exec -T kafka bash -lc "$*"
}

echo "Waiting for Kafka..."
for i in {1..60}; do
  if in_container "${KAFKA_TOPICS_BIN} --bootstrap-server ${BROKER} --list >/dev/null 2>&1"; then
    break
  fi
  sleep 2
  echo -n "."
done
echo

create_topic() {
  local name="$1" parts="$2" rf="${3:-1}"
  if in_container "${KAFKA_TOPICS_BIN} --bootstrap-server ${BROKER} --list | grep -qx '${name}'"; then
    echo "Topic '${name}' exists"
  else
    echo "Creating topic '${name}' (partitions=${parts}, rf=${rf})"
    in_container "${KAFKA_TOPICS_BIN} --create --if-not-exists --topic '${name}' --partitions ${parts} --replication-factor ${rf} --bootstrap-server ${BROKER}"
  fi
}

create_topic "logs.raw" 3 1
create_topic "logs.parsed" 3 1
create_topic "logs.dlq" 1 1

echo "Topics now:"
in_container "${KAFKA_TOPICS_BIN} --bootstrap-server ${BROKER} --list"
