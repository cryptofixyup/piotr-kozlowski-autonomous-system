from .schemas import OptimizeRequest
from services.assignment_engine.engine import assign
def optimize_order(request:OptimizeRequest):
    decision=assign(request.order,request.vehicles,request.carriers)
    if decision is None:return {"decision":"reject","reason":"no_feasible_assignment"}
    vehicle=next(v for v in request.vehicles if v.id==decision.vehicle_id); carrier=next(c for c in request.carriers if c.id==decision.carrier_id)
    fuel=request.route.distance_km/100*vehicle.fuel_l_per_100km*request.fuel_price_pln_per_litre; carrier_cost=request.route.distance_km*carrier.cost_per_km
    total=fuel+carrier_cost+request.route.toll_cost_pln; margin=request.order.revenue_pln-total; pct=100*margin/request.order.revenue_pln if request.order.revenue_pln else 0
    return {"decision":"approve" if pct>=request.target_margin_pct else "review","vehicle_id":vehicle.id,"carrier_id":carrier.id,"confidence":decision.confidence,"cost_pln":round(total,2),"margin_pln":round(margin,2),"margin_pct":round(pct,2)}
