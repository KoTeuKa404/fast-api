# FastAPI Upgraded Stack (based on your project)

## Run
```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
# run migrations if you use Alembic:
# docker compose exec web alembic revision -m "init"
# docker compose exec web alembic upgrade head
```

- API: http://localhost:9082/docs
- Nginx proxy: http://localhost:8089/
- Flower: http://localhost:5557

## Celery
Start a demo task:
```bash
curl -X POST http://localhost:9082/tasks/start?seconds=10&steps=10
```
Check status:
```bash
curl http://localhost:9082/tasks/{TASK_ID}/status
```
Cancel:
```bash
curl -X POST http://localhost:9082/tasks/{TASK_ID}/cancel
```

## Notes
- DB URL is read from `DATABASE_URL` (.env). Defaults to SQLite if not set.
- Redis/Celery URLs come from `.env`.
- Health check: `GET /healthz`.
