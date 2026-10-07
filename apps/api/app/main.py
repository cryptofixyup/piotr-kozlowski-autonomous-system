from fastapi import FastAPI, HTTPException
from app.optimizer import optimize_order
from app.schemas import OptimizeRequest, TransitionRequest
from services.order_state_machine.service import OrderState, transition
from services.order_state_machine.validator import InvalidOrderTransition
app=FastAPI(title="Autonomous Operations API",version="0.2.0")
@app.get("/health")
def health()->dict[str,str]: return {"status":"ok"}
@app.post("/v1/optimize")
def optimize(request:OptimizeRequest): return optimize_order(request)
@app.post("/v1/orders/transition")
def transition_order(request:TransitionRequest):
    try:return {"status":transition(OrderState(request.current),request.target).status.value}
    except InvalidOrderTransition as exc:raise HTTPException(status_code=409,detail=str(exc)) from exc
