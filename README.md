# Zero-config local demo
docker compose up --build

# Optional: customize config
cp .env.example .env
docker compose up --build

# Optional: include pgAdmin
docker compose --profile tools up --build

# NESO client note
The first implementation uses a synchronous HTTPX client because the ingestion workload is intentionally small and rate-limited. NESO recommends no more than two DataStore API requests per minute, so async support would be used later for clean orchestration and non-blocking behavior rather than concurrent request bursts.

An async NESO client remains a future design option if the project needs multi-resource ingestion or broader workflow coordination.