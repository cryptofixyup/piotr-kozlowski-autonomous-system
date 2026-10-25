from pydantic import BaseModel, Field, FiniteFloat

class Vehicle(BaseModel):
    id: str
    capacity_kg: FiniteFloat = Field(gt=0)
    fuel_l_per_100km: FiniteFloat = Field(gt=0)
    available: bool = True

class Carrier(BaseModel):
    id: str
    rating: FiniteFloat = Field(ge=0, le=5)
    cost_per_km: FiniteFloat = Field(ge=0)
    availability: FiniteFloat = Field(ge=0, le=1)
    verified: bool = True

class Order(BaseModel):
    id: str
    origin: str
    destination: str
    weight_kg: FiniteFloat = Field(gt=0)
    revenue_pln: FiniteFloat = Field(ge=0)

class Route(BaseModel):
    distance_km: FiniteFloat = Field(gt=0)
    toll_cost_pln: FiniteFloat = Field(ge=0)

class OptimizeRequest(BaseModel):
    order: Order
    route: Route
    vehicles: list[Vehicle]
    carriers: list[Carrier]
    fuel_price_pln_per_litre: FiniteFloat = Field(gt=0)
    target_margin_pct: FiniteFloat = Field(ge=0, le=100)
