from services.assignment_engine.engine import assign

def test_assignment_prefers_utilized_feasible_vehicle():
    order=type("O",(),{"weight_kg":2000})()
    v1=type("V",(),{"id":"V1","capacity_kg":3500,"fuel_l_per_100km":10,"available":True})()
    v2=type("V",(),{"id":"V2","capacity_kg":12000,"fuel_l_per_100km":20,"available":True})()
    c=type("C",(),{"id":"C1","rating":5,"cost_per_km":2.5,"availability":1,"verified":True})()
    d=assign(order,[v1,v2],[c])
    assert d and d.vehicle_id=="V1" and d.carrier_id=="C1"
