from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Kafka
    KAFKA_BROKERS: str = "kafka:9092"
    KAFKA_CLIENT_ID: str = "log-engine"
    TOPIC_RAW: str = "logs.raw"
    TOPIC_PARSED: str = "logs.parsed"
    TOPIC_DLQ: str = "logs.dlq"
    KAFKA_GROUP_INGESTOR: str = "ingestor-group"

    # Batching / perf
    MAX_INFLIGHT: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
