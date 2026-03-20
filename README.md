# Bio-AI Sequence Management System 🧬

A high-performance asynchronous backend service designed for biological sequence data management and AI-driven analysis.

## 🌟 Core Features
* **High-Performance Async Architecture**: Built with **FastAPI** and **SQLAlchemy 2.0**, fully leveraging non-blocking I/O for concurrent sequence processing.
* **Production-Grade Validation**: Utilizes **Pydantic V2** for strict data validation of genomic sequences (ATCG integrity).
* **Professional Test Suite**: Achieves 90%+ coverage using **Pytest-asyncio** with a fully isolated in-memory database testing environment.
* **Bio-Feature Extraction**: Automatic calculation of DNA base composition (A/T/C/G counts) and GC-content percentages.

## 🛠️ Tech Stack
* **Language**: Python 3.12+
* **Framework**: FastAPI, Uvicorn
* **Database**: PostgreSQL (Development: SQLite)
* **ORM**: SQLAlchemy 2.0 (Async)
* **Testing**: Pytest, HTTPX

## 🚀 Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Service**:
    ```bash
    uvicorn app.main:app --reload
    ```

3.  **Run Automated Tests**:
    ```bash
    python -m pytest
    ```

## 📈 Roadmap
- [x] Asynchronous CRUD Infrastructure
- [x] Automated Integration Test Suite
- [ ] Redis-backed Caching Layer (Week 2)
- [ ] LLM-driven Genomic Functional Annotation (Week 3)
- [ ] Distributed Task Processing with Celery (Week 3)

## 💡 Engineering Highlights
* **Dependency Injection**: Implemented robust DI patterns for seamless database session management and testing overrides.
* **Error Handling**: Centralized exception handling with clear HTTP semantics (400, 404, 500).
* **TDD Mindset**: Developed following Test-Driven Development principles to ensure system reliability.