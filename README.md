# Zero-config local demo
docker compose up --build

# Optional: customize config
cp .env.example .env
docker compose up --build

# Optional: include pgAdmin
docker compose --profile tools up --build