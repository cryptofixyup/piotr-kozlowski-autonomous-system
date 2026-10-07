def vehicle_score(vehicle, order) -> float:
    if not vehicle.available or vehicle.capacity_kg < order.weight_kg:
        return -1.0
    capacity_fit = min(order.weight_kg / vehicle.capacity_kg, 1.0)
    efficiency = 1.0 / max(vehicle.fuel_l_per_100km, 0.1)
    return 0.50 * (1.0 - capacity_fit + 0.5) + 0.50 * min(efficiency / 0.5, 1.0)

def carrier_score(carrier) -> float:
    if not carrier.verified or carrier.availability <= 0:
        return -1.0
    return (
        0.35 * (carrier.rating / 5.0)
        + 0.25 * carrier.availability
        + 0.20 * float(carrier.verified)
        + 0.20 * (1.0 / (1.0 + carrier.cost_per_km))
    )
