#  Real-Time Log Processing Pipeline

![Kafka](https://img.shields.io/badge/Kafka-Event%20Streaming-black?logo=apachekafka)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-blue?logo=fastapi)
![OpenSearch](https://img.shields.io/badge/OpenSearch-Search%20&%20Analytics-4285F4?logo=opensearch)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Python](https://img.shields.io/badge/Python-Backend-green?logo=python)

A **containerized, event-driven log processing pipeline** built with **FastAPI**, **Kafka**, and **OpenSearch**, designed for **real-time ingestion, normalization, indexing, and querying** of application logs.  
This project simulates a production-grade architecture for high-velocity log analytics, search, and dashboarding — entirely runnable locally via **Docker Compose**.

---

##  Features

- ** API ingestion**: Receive raw JSON/NDJSON logs via a REST API (`FastAPI`).
- ** Real-time pipeline**: Kafka topics buffer logs between microservices.
- ** Log normalization**: Enrich & standardize incoming logs before indexing.
- ** Bulk indexing**: High-throughput writes into OpenSearch with daily indices.
- ** Data lifecycle management**: ISM policy automatically deletes logs older than 7 days.
- ** Query API**: Filter logs by fields (e.g., service, log level, time range).
- ** OpenSearch Dashboards**: Visualize logs and search interactively.
- ** Fully containerized**: Easy local spin-up using Docker Compose.
- ** Tested**: Unit tests for ingestion, normalization, and indexing components.

---

##  Architecture

            ┌──────────────┐       ┌──────────────┐
  API  ---> │   Kafka      │ --->  │   Ingestor    │ --->  Kafka (parsed logs)
 (FastAPI)  │   logs.raw   │       └──────────────┘
            └──────────────┘
                                        |
                                        v
                               ┌──────────────┐
                               │   Indexer    │ ---> OpenSearch (logs-yyyy.MM.dd)
                               └──────────────┘
                                        |
                                        v
                               ┌────────────────┐
                               │ Query API      │ ---> API / Dashboards
                               └────────────────┘

| Component       | Purpose                                           | Key Tools / Libraries |
|-----------------|---------------------------------------------------|-----------------------|
| **API Service** | Accept logs from external clients                 | FastAPI, Pydantic     |
| **Kafka**       | Event streaming & decoupling between services     | Apache Kafka          |
| **Ingestor**    | Normalizes & enriches logs                        | Python, Kafka Consumer|
| **Indexer**     | Bulk writes to OpenSearch                         | OpenSearch Python Client, ISM |
| **Storage**     | Search & analytics engine                         | OpenSearch            |
| **Orchestration**| Local multi-service environment                  | Docker Compose        |
| **Testing**     | Unit tests for core logic                         | Pytest                |


