from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field

class Settings(BaseSettings):
    # Kafka
    KAFKA_BROKERS: str = "kafka:9092"
    KAFKA_CLIENT_ID: str = "log-engine"
    TOPIC_RAW: str = "logs.raw"
    TOPIC_PARSED: str = "logs.parsed"
    TOPIC_DLQ: str = "logs.dlq"

    # OpenSearch
    OS_HOST: AnyHttpUrl = Field(default="https://opensearch:9200")
    OS_USER: str = "admin"
    OS_PASSWORD: str = "admin"
    OS_INDEX_ALIAS: str = "logs-write"
    OS_INDEX_PATTERN: str = "logs-*"
    OS_TEMPLATE_NAME: str = "logs-template"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_BASIC_USER: str = "admin"
    API_BASIC_PASS: str = "admin"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
