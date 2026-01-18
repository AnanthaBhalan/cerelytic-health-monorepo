# ---------- Builder stage ----------
FROM python:3.11.8-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt


# ---------- Runtime stage ----------
FROM python:3.11.8-slim

# Create non-root user
RUN useradd -m appuser

WORKDIR /app

# Install only runtime deps
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy source code
COPY . .

# Switch to non-root user
USER appuser

EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
