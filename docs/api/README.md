# AegisAI API Endpoint Specifications

All endpoints are versioned and prefixes are grouped by service domains.

## Swagger Documentation
Once the server is running, the interactive OpenAPI documentation is accessible at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Endpoint Map

### Authentication
* **POST `/api/v1/auth/register`**: Creates a user Account.
* **POST `/api/v1/auth/login`**: Authenticates credentials, returns JWT.
* **GET `/api/v1/auth/me`**: Returns profile details for currently active user.

### System Health
* **GET `/api/v1/health`**: Returns summary of all services (Database, Redis, Celery).
* **GET `/api/v1/health/database`**: Pings PostgreSQL.
* **GET `/api/v1/health/redis`**: Pings Redis cache/broker.
* **GET `/api/v1/health/celery`**: Verifies Celery workers responding.

### Knowledge Base (Documents)
* **GET `/api/v1/documents`**: Lists uploaded knowledge base documents.
* **POST `/api/v1/documents/upload`**: Uploads file, triggers background Celery job.

### Agent Chat
* **GET `/api/v1/chat`**: Lists active chat conversations.
* **POST `/api/v1/chat`**: Initializes a new chat session.
