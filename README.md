# AegisAI – Enterprise Agentic Knowledge Platform

AegisAI is a modular, containerized software foundation demonstrating professional backend engineering, secure JWT authentication, asynchronous task execution, structured JSON logging, and container orchestration. It acts as the engineering gateway for a future Multi-Agent Cognitive Search and Retrieval-Augmented Generation (RAG) platform.

---

## Document Ingestion Pipeline (Phase 2.1)

Phase 2.1 establishes the secure ingestion pipeline for corporate document assets. The system receives files via the REST API gateway, validates file formats and sizes, maps them to database metadata, saves them securely inside the storage volume, and delegates processing jobs to background Celery queues.

### Expected Ingestion Workflow
```
Login
  ↓
Drag & Drop / Pick File (PDF, DOCX, TXT)
  ↓
Validation (Size < 25MB, Non-Empty, Allowed MIMEs/Exts)
  ↓
Write File to Disk (UUID Renamed)
  ↓
Generate SHA-256 Checksum (recorded in DB for future deduplication and integrity)
  ↓
Record Metadata to PostgreSQL (status = UPLOADED)
  ↓
Queue Celery Worker task ("process_document")
  ↓
Transition Status to QUEUED
  ↓
Worker Picks Task
  ↓
Transition Status to PROCESSING
  ↓
Success → PROCESSED
Failure → FAILED
```

### Document Lifecycles
Documents navigate through five distinct execution states:
1. **`UPLOADED`**: File has been successfully written to disk, SHA-256 generated, and metadata saved.
2. **`QUEUED`**: The Celery background task has been successfully dispatched to the Redis broker queue.
3. **`PROCESSING`**: A Celery worker has consumed the parsing task and started the analysis.
4. **`PROCESSED`**: The document extraction, chunking (Phase 2.2), and indexing steps finished successfully.
5. **`FAILED`**: Ingestion, queue operations, or schema registration encountered an exception.

### File Checksum & Integrity
Immediately after file storage, the platform computes a SHA-256 hash.
* **Why it exists**:
  1. **Integrity Validation**: Verifies files are not corrupted or tampered with in transit or on disk.
  2. **Deduplication (Future)**: Prevents redundant vector generation and storage when the same document is uploaded multiple times.

### Storage Architecture
To prevent collisions and security vectors (directory traversal, script execution):
* Original filenames are stored inside PostgreSQL metadata.
* Files are renamed to a generated UUID (e.g. `a7d2b7c6-f93e-48dd-8d7d-3d2d1fd72e2b.pdf`) upon writing.
* File uploads are persisted in `backend/app/storage/uploads/`, which is mapped to a docker volume for cross-container availability.

---

## API Specifications

All endpoints are versioned and require header JWT Authorization: `Authorization: Bearer <token>`.

### Ingestion Endpoints

#### 1. Ingest Document
* **Endpoint**: `POST /api/v1/documents/upload`
* **Format**: `multipart/form-data`
* **Parameters**: `file` (Binary payload)
* **Rules**: 
  - File extension must be `.pdf`, `.docx`, or `.txt`.
  - MIME type must match `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, or `text/plain`.
  - Max upload size: Configurable (defaults to 25MB). Reject if empty.
* **Response (201 Created)**:
  ```json
  {
    "id": 42,
    "account_id": 1,
    "original_filename": "q2_earnings.pdf",
    "stored_filename": "a7d2b7c6-f93e-48dd-8d7d-3d2d1fd72e2b.pdf",
    "file_extension": "pdf",
    "mime_type": "application/pdf",
    "file_size": 1048576,
    "storage_path": "app/storage/uploads/a7d2b7c6-f93e-48dd-8d7d-3d2d1fd72e2b.pdf",
    "status": "UPLOADED",
    "created_at": "2026-07-22T15:30:00Z",
    "updated_at": "2026-07-22T15:30:00Z"
  }
  ```

#### 2. List Documents
* **Endpoint**: `GET /api/v1/documents`
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 42,
      "original_filename": "q2_earnings.pdf",
      "file_extension": "pdf",
      "file_size": 1048576,
      "status": "PROCESSED"
    }
  ]
  ```

#### 3. Retrieve Document
* **Endpoint**: `GET /api/v1/documents/{id}`
* **Response (200 OK)**: Returns full document metadata if the document belongs to the active user.

#### 4. Delete Document
* **Endpoint**: `DELETE /api/v1/documents/{id}`
* **Behavior**: Removes file from uploads directory and drops DB metadata row.
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Document successfully deleted"
  }
  ```

---

## Technology Stack

* **Backend Engine**: Python 3.12, FastAPI, Uvicorn, Pydantic v2
* **Structured Logging**: Structlog (JSON stream delivery)
* **Storage & Relational ORM**: PostgreSQL, SQLAlchemy 2.0 (Async Engine), Alembic Migrations
* **Task Distribution**: Redis, Celery (background workers)
* **Frontend Portal**: React 18, Vite, TypeScript, TailwindCSS, Axios, Lucide Icons
* **Infrastructure**: Docker, Docker Compose, pgAdmin (automatic registration)

---

## Setup & Running with Docker

### Prerequisites
Ensure you have Docker and Docker Compose installed.

### 1. Copy Environment File
```bash
cp .env.example .env
```

### 2. Build & Launch Containers
```bash
make up
```
Or run directly:
```bash
docker compose up --build
```

On startup, the system launches:
1. **PostgreSQL** (`aegis_db`): Operational on port `5432`
2. **Redis** (`aegis_redis`): Operational on port `6379`
3. **FastAPI Gateway** (`aegis_backend`): Operational on port `8000`
4. **Celery Worker** (`aegis_celery_worker`): Executing background queues
5. **Vite Frontend** (`aegis_frontend`): Operational on port `5173`
6. **pgAdmin** (`aegis_pgadmin`): Operational on port `5050` (preconfigured to connect automatically to the DB)

---

## Database Schema Migrations

Run migrations using:
```bash
make migrate
```
Or:
```bash
docker compose run --rm backend alembic upgrade head
```

---

## Future AI & RAG Roadmap

* **Phase 1 (Completed)**: Core gateway routing, authentication session context, background workers, health metrics, and infrastructure containers.
* **Phase 2.1 (Current)**: Document Ingestion Pipeline (MIME/size validations, UUID storage renaming, metadata tracking, Celery hooks).
* **Phase 2.2 (RAG & Vector Search)**: Add `PGVector` database schemas, create text chunking rules using NLTK/SentenceTransformers, generate document embeddings, and connect local search engines.
* **Phase 3 (Agent Orchestration)**: Implement prompt decorators, structured tools execution models, and state-machine memory agents to perform planning and context-driven research.
* **Phase 4 (Cognitive Dashboard UI)**: Open WebSocket streams to animate agent reasoning steps, display document chunks citations inline, and offer custom prompt adjustments.
