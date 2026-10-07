from fastapi import FastAPI
from app.optimizer import optimize_order
from app.schemas import OptimizeRequest

app = FastAPI(title="Autonomous Operations API", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/v1/optimize")
def optimize(request: OptimizeRequest):
    return optimize_order(request)
