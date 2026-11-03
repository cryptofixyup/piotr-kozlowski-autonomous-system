"""Pure, read-only consolidation screening; never books or dispatches.

Conservative scope: exactly matching lane IDs/locations, overlapping pickup
windows, and combined load within a stated vehicle capacity. Routing, journey
duration, stops, legal hours and profitability require separate verified inputs.
"""
from dataclasses import dataclass
from itertools import combinations
from math import isfinite


@dataclass(frozen=True)
class ConsolidationLoad:
    id: str
    origin: str
    destination: str
    earliest_pickup_minute: int
    latest_pickup_minute: int
    weight_kg: float


@dataclass(frozen=True)
class ConsolidationVehicle:
    id: str
    capacity_kg: float
    available: bool = True


@dataclass(frozen=True)
class ConsolidationCandidate:
    load_ids: tuple[str, str]
    vehicle_id: str
    pickup_earliest_minute: int
    pickup_latest_minute: int
    combined_weight_kg: float


def _location(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("location must be nonempty")
    return value.strip().casefold()


def _minute(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("pickup times must be nonnegative integer minutes")
    return value


def _weight(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("weight/capacity must be numeric")
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise ValueError("weight/capacity must be finite and positive") from None
    if not isfinite(number) or number <= 0:
        raise ValueError("weight/capacity must be finite and positive")
    return number


def screen_consolidation(
    loads: list[ConsolidationLoad],
    vehicles: list[ConsolidationVehicle],
) -> list[ConsolidationCandidate]:
    """Screen feasible two-load pairs; does not reserve vehicle capacity."""
    seen_load_ids: set[str] = set()
    seen_vehicle_ids: set[str] = set()
    checked_loads = []
    checked_vehicles = []
    for load in loads:
        if not isinstance(load.id, str) or not load.id.strip() or load.id in seen_load_ids:
            raise ValueError("load IDs must be nonempty and unique")
        seen_load_ids.add(load.id)
        origin, destination = _location(load.origin), _location(load.destination)
        earliest = _minute(load.earliest_pickup_minute)
        latest = _minute(load.latest_pickup_minute)
        if earliest > latest:
            raise ValueError("pickup window is inverted")
        checked_loads.append((load.id, origin, destination, earliest, latest, _weight(load.weight_kg)))
    for vehicle in vehicles:
        if not isinstance(vehicle.id, str) or not vehicle.id.strip() or vehicle.id in seen_vehicle_ids:
            raise ValueError("vehicle IDs must be nonempty and unique")
        seen_vehicle_ids.add(vehicle.id)
        if type(vehicle.available) is not bool:
            raise ValueError("availability must be boolean")
        checked_vehicles.append((vehicle.id, _weight(vehicle.capacity_kg), vehicle.available))
    candidates = []
    for left, right in combinations(checked_loads, 2):
        if left[1:3] != right[1:3]:
            continue
        earliest = max(left[3], right[3])
        latest = min(left[4], right[4])
        if earliest > latest:
            continue
        combined = left[5] + right[5]
        if not isfinite(combined):
            raise ValueError("combined weight exceeds finite range")
        for vehicle_id, capacity, available in checked_vehicles:
            if available and combined <= capacity:
                candidates.append(ConsolidationCandidate(
                    tuple(sorted((left[0], right[0]))),
                    vehicle_id, earliest, latest, combined,
                ))
    return sorted(candidates, key=lambda c: (c.load_ids, c.vehicle_id))
