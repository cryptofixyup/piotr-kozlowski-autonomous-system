"""Deterministic, read-only backhaul feasibility screening.

Locations use exact normalized identifiers, not inferred geographic proximity.
Time values are integer minutes on a shared timeline; distances/costs must be
supplied by trusted upstream systems. This module performs no I/O or dispatch.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class BackhaulLeg:
    id: str
    origin: str
    destination: str
    ready_minute: int
    deadline_minute: int
    weight_kg: float
    revenue_pln: float


@dataclass(frozen=True)
class AvailableVehicle:
    id: str
    at_location: str
    available_minute: int
    capacity_kg: float


@dataclass(frozen=True)
class BackhaulCandidate:
    leg_id: str
    vehicle_id: str
    surplus_capacity_kg: float
    revenue_pln: float


def _location(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("location must be nonempty")
    return value.strip().casefold()


def _minute(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("timestamps must be nonnegative integer minutes")
    return value


def _positive_finite(value: float, name: str, *, zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    number = float(value)
    if not isfinite(number) or (number < 0 if zero else number <= 0):
        raise ValueError(f"{name} must be finite and nonnegative" if zero else f"{name} must be finite and positive")
    return number


def screen_backhauls(
    legs: list[BackhaulLeg], vehicles: list[AvailableVehicle]
) -> list[BackhaulCandidate]:
    """Return individually feasible matches; no vehicle is allocated or reserved.

    Requires exact origin-location agreement, verified availability before ready
    time, and sufficient capacity. No unverified travel time is invented.
    """
    seen_legs: set[str] = set()
    seen_vehicles: set[str] = set()
    checked_legs = []
    checked_vehicles = []
    for leg in legs:
        if not isinstance(leg.id, str) or not leg.id.strip() or leg.id in seen_legs:
            raise ValueError("leg IDs must be nonempty and unique")
        seen_legs.add(leg.id)
        origin, destination = _location(leg.origin), _location(leg.destination)
        ready, deadline = _minute(leg.ready_minute), _minute(leg.deadline_minute)
        if deadline < ready:
            raise ValueError("deadline precedes ready time")
        weight = _positive_finite(leg.weight_kg, "weight_kg")
        revenue = _positive_finite(leg.revenue_pln, "revenue_pln", zero=True)
        checked_legs.append((leg.id, origin, destination, ready, weight, revenue))
    for vehicle in vehicles:
        if not isinstance(vehicle.id, str) or not vehicle.id.strip() or vehicle.id in seen_vehicles:
            raise ValueError("vehicle IDs must be nonempty and unique")
        seen_vehicles.add(vehicle.id)
        location = _location(vehicle.at_location)
        available = _minute(vehicle.available_minute)
        capacity = _positive_finite(vehicle.capacity_kg, "capacity_kg")
        checked_vehicles.append((vehicle.id, location, available, capacity))
    matches = [
        BackhaulCandidate(leg_id, vehicle_id, capacity - weight, revenue)
        for leg_id, origin, _destination, ready, weight, revenue in checked_legs
        for vehicle_id, location, available, capacity in checked_vehicles
        if location == origin and available <= ready and capacity >= weight
    ]
    return sorted(matches, key=lambda item: (item.leg_id, -item.revenue_pln, item.vehicle_id))
