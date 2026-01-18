dev-stack:
	docker compose -f infra/docker-compose.yml up --build

dev-api:
	uvicorn manager-api.main:app --reload

dev-worker:
	python worker/worker.py

test-api:
	pytest
