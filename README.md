# Bio-AI Sequence Management System 🧬

A high-performance asynchronous backend service designed for biological sequence data management and **AI-driven similarity analysis**.

## 🚀 Core Features
* **AI Vector Search**: Integrated **pgvector** to support genomic sequence similarity searches based on high-dimensional L2 distance rather than simple string matching.
* **High-Performance Async Architecture**: Built with **FastAPI** and **SQLAlchemy 2.0**, fully leveraging non-blocking I/O for concurrent sequence processing.
* **Production-Grade Containerization**: Orchestrated via **Docker Compose** with a specialized PostgreSQL 15 image (pgvector enabled) and a Redis caching layer.
* **Rigorous Test Suite**: Achieves **83% code coverage** using **Pytest-asyncio** with isolated environments, ensuring the reliability of core business logic.
* **Automated Bio-Feature Extraction**: Automatically calculates DNA mathematical features (GC-content, A-content, and normalized length) to generate 3-dimensional AI embeddings.

## 🛠️ Tech Stack
* **Language**: Python 3.12+
* **Framework**: FastAPI, Uvicorn
* **Database**: **PostgreSQL 15 (with pgvector)**
* **Cache**: Redis 7 (Mocked in tests)
* **ORM**: SQLAlchemy 2.0 (Async)
* **Infrastructure**: Docker, Docker Compose

## 📦 Quick Start

1.  **Spin up the Containerized Environment**:
    ```bash
    docker-compose up -d --build
    ```

2.  **Run Automated Tests & Coverage Report**:
    ```bash
    pytest --cov=app
    ```

## 🗺️ Roadmap
- [x] Asynchronous CRUD Infrastructure
- [x] Similarity Search Experiment with **pgvector**
- [x] Automated Integration Tests with 80%+ Coverage
- [x] Production Redis Integration
- [x] LLM-driven Genomic Functional Annotation
- [ ] Distributed Task Processing with Celery

## 🏗️ Engineering Highlights
* **Environment Isolation**: Utilizes Docker Volumes and Dependency Injection (DI) patterns for seamless switching between development, testing, and production.
* **Feature Engineering**: Translates biological logic (e.g., GC-content) into mathematical vectors, laying the groundwork for Large Language Model (LLM) integration.
* **System Robustness**: Implemented Mocking strategies for Redis to ensure test independence and reliable CI/CD pipelines.