# Bio-AI Sequence Management System 🧬

A high-performance asynchronous backend service designed for biological sequence data management and **AI-driven similarity analysis**.

## 🚀 Core Features
* **AI Vector Search**: Integrated **pgvector** to support genomic sequence similarity searches based on high-dimensional L2 distance rather than simple string matching.
* **High-Performance Async Architecture**: Built with **FastAPI** and **SQLAlchemy 2.0**, fully leveraging non-blocking I/O for concurrent sequence processing.
* **Production-Grade Containerization**: Orchestrated via **Docker Compose** with a specialized PostgreSQL 15 image (pgvector enabled) and a Redis caching layer.
* **Rigorous Test Suite**: Achieves **83% code coverage** using **Pytest-asyncio** with isolated environments, ensuring the reliability of core business logic.
* **Automated Bio-Feature Extraction**: Automatically calculates DNA mathematical features (GC-content, A-content, and normalized length) to generate 3-dimensional AI embeddings.
* **Infrastructure**: Docker, Docker Compose, **Google Cloud Platform (Cloud Run, Cloud SQL, Cloud Memorystore)**
* **CI/CD**: **GitHub Actions** with Automated GCP Deployment

## 🛠️ Tech Stack
* **Language**: Python 3.12+
* **Framework**: FastAPI, Uvicorn
* **Database**: **PostgreSQL 15 (with pgvector)**
* **Cache**: Redis 7 (Mocked in tests)
* **ORM**: SQLAlchemy 2.0 (Async)
* **Infrastructure**: Docker, Docker Compose
* **Monitoring**: Prometheus, Grafana

## 📦 Quick Start

1.  **Spin up the Containerized Environment**:
    ```bash
    docker-compose up -d --build
    ```

2.  **Run Automated Tests & Coverage Report**:
    ```bash
    pytest --cov=app
    ```
2.  **Monitoring Access**:
    ```
    Prometheus: http://localhost:9090
    Grafana: http://localhost:3000 (Default: admin/admin)
    ```


## 🗺️ Roadmap
- [x] Asynchronous CRUD Infrastructure
- [x] Similarity Search Experiment with **pgvector**
- [x] Automated Integration Tests with 80%+ Coverage
- [x] Production Redis Integration
- [x] LLM-driven Genomic Functional Annotation
- [x] Real-time Observability Stack (Prometheus/Grafana)
- [x] API Rate Limiting & Security
- [x] **Automated CI/CD Pipeline (GitHub Actions to Google Cloud Run)**

## 🏗️ Engineering Highlights
* **Environment Isolation**: Utilizes Docker Volumes and Dependency Injection (DI) patterns for seamless switching between development, testing, and production.
* **Feature Engineering**: Translates biological logic (e.g., GC-content) into mathematical vectors, laying the groundwork for Large Language Model (LLM) integration.
* **System Robustness**: Implemented Mocking strategies for Redis to ensure test independence and reliable CI/CD pipelines.
* **Real-time Observability Stack**: Integrated Prometheus and Grafana to monitor system health and track p95 latency, specifically for long-running AI inference tasks.
* **Defensive Rate Limiting**: Implemented global, IP-based request throttling via SlowAPI to protect Gemini API quotas and ensure service availability under high load.

## ☁️ Cloud Architecture & DevOps

The system is architected for cloud-native scalability on **Google Cloud Platform**:
* **Serverless Execution**: The FastAPI application is containerized and deployed via **Cloud Run**, ensuring auto-scaling based on incoming DNA analysis requests.
* **Managed Persistence**: Utilizes **Cloud SQL (PostgreSQL 15)** with the `pgvector` extension for secure and scalable genomic data storage.
* **Secure Networking**: Integrated **Serverless VPC Access** to enable private communication between Cloud Run and **Cloud Memorystore (Redis)**.
* **Continuous Deployment**: A fully automated CI/CD pipeline built with **GitHub Actions** that handles:
    1.  Secure authentication via Google Service Accounts.
    2.  Automated image building and pushing to **Artifact Registry**.
    3.  Atomic deployments to Cloud Run with automatic traffic routing.