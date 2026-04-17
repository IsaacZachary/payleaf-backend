# PayLeaf Backend — Payment Service

PayLeaf is a secure, high-performance payment infrastructure designed for modern fintech applications. It handles both traditional card payments and cryptocurrency charges with an emphasis on transparency, security, and developer experience.

## Tech Stack
*   **Python 3.12** / **Django 5.0** / **DRF 3.15**
*   **PostgreSQL 16** (Atomic transactions, JSONB audit logs)
*   **Redis 7** (In-memory store for sessions, rate limits, and idempotency)
*   **Celery 5** (Distributed task queue for webhooks, KYC, and crypto polling)
*   **Docker** (Containerized orchestration for web, worker, and beat)

## Security Architecture
*   **Auditing**: Every mutating API request is logged in an append-only table. Each row is cryptographically linked to the previous one via SHA256 (Hash Chain), ensuring tampering detection.
*   **Authentication**: Argon2id password hashing for dashboards. API Key access uses SHA256 hashed keys (stored secrets are never retrievable).
*   **Data Integrity**: Redis-backed Idempotency middleware prevents double-charging by caching results for 24h.
*   **PCI Scope**: Zero PAN exposure. We utilize processor-side tokenization (SAQ-A) via Stripe.
*   **Webhook Verification**: Outbound webhooks are signed using HMAC-SHA256 secrets.

## Getting Started

### Local Setup
1.  **Clone the Repo**: 
    ```bash
    git clone https://github.com/payleaf/backend.git
    cd backend
    ```
2.  **Environment Variables**: Copy `.env.example` to `.env` and fill in the secrets.
3.  **Launch Ecosystem**:
    ```bash
    make up
    ```
4.  **Bootstrap DB**:
    ```bash
    make migrate
    ```
5.  **Verify**:
    ```bash
    make test
    ```

### Makefile Reference
*   `make up`: Start all services (web, postgres, redis, celery, beat, worker).
*   `make migrate`: Run Django migrations.
*   `make test`: Execute pytest suite with coverage.
*   `make lint`: Run Ruff and Black for code quality.

## Deployment
PayLeaf is designed to be cloud-agnostic:
*   **Railway/Fly.io**: Automatically detects `Dockerfile` and `docker-compose.yml`. Set env vars in the dashboard.
*   **AWS ECS**: Use the provided `Dockerfile`. Use RDS for Postgres and ElastiCache for Redis.
*   **GCP Cloud Run**: Fully compatible. Mount secrets from Secret Manager to env vars.

## API Documentation
The authoritative API contract is located in [docs/BACKEND_API.md](docs/BACKEND_API.md).
Interactive test requests live in [docs/api_tests.http](docs/api_tests.http).

## Env Var List (Partial)
| Variable | Description | Default |
| :--- | :--- | :--- |
| `DEBUG` | Toggle debug mode | `False` |
| `SECRET_KEY` | Django project key | (required) |
| `DATABASE_URL` | Postgres URI | (required) |
| `STRIPE_SECRET_KEY` | Stripe SDK Key | (required) |
| `COINBASE_API_KEY` | Coinbase Commerce Key | (required) |
| `PAYMENT_PROCESSOR` | Stripe / NowPayments | `stripe` |
| `CORS_ALLOWED_ORIGINS` | React App domain | `http://localhost:5173` |
