def vehicle_score(v,o):
    if not v.available or v.capacity_kg<o.weight_kg:return -1.0
    utilization=o.weight_kg/v.capacity_kg
    normalized_efficiency=min((1/max(v.fuel_l_per_100km,.1))/.5,1.0)
    return .65*utilization+.35*normalized_efficiency

def carrier_score(c):
    if not c.verified or c.availability<=0:return -1.0
    return .35*(c.rating/5)+.25*c.availability+.20*float(c.verified)+.20*(1/(1+c.cost_per_km))
