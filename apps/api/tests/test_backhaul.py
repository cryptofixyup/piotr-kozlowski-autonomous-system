import pytest

from app.backhaul import AvailableVehicle, BackhaulLeg, screen_backhauls


def leg(**changes):
    data = dict(id="L1", origin="Berlin", destination="Warsaw",
                ready_minute=100, deadline_minute=200,
                weight_kg=1000, revenue_pln=2500)
    data.update(changes)
    return BackhaulLeg(**data)


def vehicle(**changes):
    data = dict(id="V1", at_location=" berlin ", available_minute=95,
                capacity_kg=1500)
    data.update(changes)
    return AvailableVehicle(**data)


def test_exact_match_and_deterministic_order():
    result = screen_backhauls([leg()], [vehicle(id="V2"), vehicle(id="V1")])
    assert [item.vehicle_id for item in result] == ["V1", "V2"]
    assert all(item.surplus_capacity_kg == 500 for item in result)


@pytest.mark.parametrize("override", [
    {"at_location": "Berlin suburb"},
    {"available_minute": 101},
    {"capacity_kg": 999},
])
def test_infeasible_vehicle_excluded(override):
    assert screen_backhauls([leg()], [vehicle(**override)]) == []


@pytest.mark.parametrize("override", [
    {"origin": ""}, {"weight_kg": 0}, {"weight_kg": float("nan")},
    {"revenue_pln": float("inf")}, {"ready_minute": 2.5},
    {"deadline_minute": 99}, {"id": ""},
])
def test_invalid_leg_fail_closed(override):
    with pytest.raises(ValueError):
        screen_backhauls([leg(**override)], [vehicle()])


@pytest.mark.parametrize("override", [
    {"at_location": ""}, {"capacity_kg": -1},
    {"capacity_kg": float("inf")}, {"available_minute": True},
])
def test_invalid_vehicle_fail_closed(override):
    with pytest.raises(ValueError):
        screen_backhauls([leg()], [vehicle(**override)])


def test_duplicate_ids_fail_closed():
    with pytest.raises(ValueError):
        screen_backhauls([leg(), leg()], [vehicle()])
    with pytest.raises(ValueError):
        screen_backhauls([leg()], [vehicle(), vehicle()])


def test_empty_inputs_and_no_execution_side_effects():
    assert screen_backhauls([], []) == []
    assert screen_backhauls([leg()], []) == []
    assert screen_backhauls([], [vehicle()]) == []
