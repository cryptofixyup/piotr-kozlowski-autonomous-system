import pytest

from app.consolidation import (
    ConsolidationLoad, ConsolidationVehicle, screen_consolidation,
)


def load(load_id, **changes):
    data = dict(id=load_id, origin="Warsaw", destination="Berlin",
                earliest_pickup_minute=100, latest_pickup_minute=200,
                weight_kg=600)
    data.update(changes)
    return ConsolidationLoad(**data)


def vehicle(vehicle_id="V1", **changes):
    data = dict(id=vehicle_id, capacity_kg=1500, available=True)
    data.update(changes)
    return ConsolidationVehicle(**data)


def test_overlapping_windows_and_deterministic_order():
    matches = screen_consolidation(
        [load("B", earliest_pickup_minute=150),
         load("A", latest_pickup_minute=175)],
        [vehicle("V2"), vehicle("V1")],
    )
    assert [(x.load_ids, x.vehicle_id) for x in matches] == [
        (("A", "B"), "V1"), (("A", "B"), "V2")
    ]
    assert all(x.pickup_earliest_minute == 150 and
               x.pickup_latest_minute == 175 and
               x.combined_weight_kg == 1200 for x in matches)


@pytest.mark.parametrize("left,right", [
    (load("A"), load("B", origin="Warsaw suburb")),
    (load("A"), load("B", destination="Hamburg")),
    (load("A", latest_pickup_minute=120), load("B", earliest_pickup_minute=121)),
])
def test_incompatible_lanes_or_windows(left, right):
    assert screen_consolidation([left, right], [vehicle()]) == []


def test_capacity_and_availability():
    loads = [load("A"), load("B")]
    assert screen_consolidation(loads, [vehicle(capacity_kg=1199)]) == []
    assert screen_consolidation(loads, [vehicle(available=False)]) == []


@pytest.mark.parametrize("changes", [
    {"weight_kg": 0}, {"weight_kg": float("nan")},
    {"weight_kg": float("inf")}, {"origin": ""},
    {"earliest_pickup_minute": True},
    {"earliest_pickup_minute": 201}, {"id": ""},
])
def test_invalid_load_rejected(changes):
    with pytest.raises(ValueError):
        screen_consolidation([load("A", **changes), load("B")], [vehicle()])


@pytest.mark.parametrize("changes", [
    {"capacity_kg": 0}, {"capacity_kg": float("inf")},
    {"available": 1}, {"id": ""},
])
def test_invalid_vehicle_rejected(changes):
    with pytest.raises(ValueError):
        screen_consolidation([load("A"), load("B")], [vehicle(**changes)])


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):
        screen_consolidation([load("A"), load("A")], [vehicle()])
    with pytest.raises(ValueError):
        screen_consolidation([load("A"), load("B")], [vehicle(), vehicle()])


def test_empty_inputs_and_boundary_overlap():
    assert screen_consolidation([], [vehicle()]) == []
    assert screen_consolidation([load("A")], [vehicle()]) == []
    assert len(screen_consolidation(
        [load("A", latest_pickup_minute=150),
         load("B", earliest_pickup_minute=150)], [vehicle()])) == 1


def test_overflow_fails_closed():
    with pytest.raises(ValueError):
        screen_consolidation(
            [load("A", weight_kg=1e308), load("B", weight_kg=1e308)],
            [vehicle(capacity_kg=1e308)])
