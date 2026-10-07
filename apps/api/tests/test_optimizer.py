from app.optimizer import optimize_order
from app.schemas import OptimizeRequest

def test_optimizer_selects_feasible_resources():
    req = OptimizeRequest(
        order={"id":"O1","origin":"Warsaw","destination":"Berlin","weight_kg":2000,"revenue_pln":3500},
        route={"distance_km":575,"toll_cost_pln":150},
        vehicles=[
            {"id":"V1","capacity_kg":3500,"fuel_l_per_100km":10,"available":True},
            {"id":"V2","capacity_kg":12000,"fuel_l_per_100km":20,"available":True},
        ],
        carriers=[
            {"id":"C1","rating":5,"cost_per_km":2.5,"availability":1,"verified":True},
            {"id":"C2","rating":4,"cost_per_km":2.0,"availability":0.8,"verified":True},
        ],
        fuel_price_pln_per_litre=6.5,
        target_margin_pct=20,
    )
    result = optimize_order(req)
    assert result["vehicle_id"] == "V1"
    assert result["margin_pln"] > 0
