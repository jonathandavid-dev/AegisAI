# AegisAI Architecture Decision Records (ADR)

This folder documents the design decisions selected during Phase 1.

## Decisions Log

### ADR 001: Structured Logging with Structlog
* **Context**: FastAPI logs are typically standard streams, which makes indexing and alerts difficult in production.
* **Decision**: Configured `structlog` for application, request, and startup logging.
* **Consequence**: All logs are emitted as single-line JSON, allowing seamless integration with Datadog, ELK, or Google Cloud Logging.

### ADR 002: Service Layer Architecture
* **Context**: Avoid coupling controllers/routers directly with SQLAlchemy session objects and SQL queries.
* **Decision**: Adopted a clean Service Layer pattern (e.g. `AuthService`) to isolate database calls, transactions, and business calculations. Avoided the Repository Pattern to keep abstractions simple and readable.
* **Consequence**: Code is highly readable, testable, and reusable.

### ADR 003: Model Renaming (User to Account)
* **Context**: Distinguish between user permissions and underlying authentication credentials.
* **Decision**: Refactored the core login model to `Account`. Extended schema templates to define `Session`, `Document`, `Chat`, and `Message` placeholders to lay the foundation for multi-tenant and multi-session capabilities in Phase 2.
* **Consequence**: Better alignment with enterprise security frameworks.
