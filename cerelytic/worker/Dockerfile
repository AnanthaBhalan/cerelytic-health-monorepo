# ---------- Builder stage ----------
FROM python:3.11.8-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt


# ---------- Runtime stage ----------
FROM python:3.11.8-slim

RUN useradd -m appuser

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY . .

USER appuser

# ❌ No EXPOSE
# ❌ No uvicorn

CMD ["python", "worker.py"]
