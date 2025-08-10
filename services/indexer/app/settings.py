from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Kafka
    kafka_brokers: str = Field(default="kafka:9092", alias="KAFKA_BROKERS")
    kafka_client_id: str = Field(default="log-engine", alias="KAFKA_CLIENT_ID")
    topic_parsed: str = Field(default="logs.parsed", alias="TOPIC_PARSED")
    kafka_group_indexer: str = Field(default="indexer-group", alias="KAFKA_GROUP_INDEXER")
    consumer_max_records: int = 1000
    consumer_poll_ms: int = 1000

    # OpenSearch
    os_host: str = Field(default="https://opensearch:9200", alias="OS_HOST")
    os_user: str = Field(default="admin", alias="OS_USER")
    os_password: str = Field(default="admin", alias="OS_PASSWORD")
    os_index_alias: str = Field(default="logs-write", alias="OS_INDEX_ALIAS")
    os_request_timeout: int = 30
    os_max_retries: int = 5
    os_retry_backoff_base: float = 0.5

    # Bulk thresholds (docs, bytes, seconds)
    bulk_max_docs: int = 1000
    bulk_max_bytes: int = 3_000_000
    bulk_flush_interval_s: float = 1.0
