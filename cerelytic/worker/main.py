from fastapi import FastAPI
from datetime import datetime
from schemas import HealthResponse

app = FastAPI(title="Cerelytic Worker API", version="1.0.0")

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
