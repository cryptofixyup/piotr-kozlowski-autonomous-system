from pydantic import BaseModel, Field

class Vehicle(BaseModel):
    id: str
    capacity_kg: float = Field(gt=0)
    fuel_l_per_100km: float = Field(gt=0)
    available: bool = True

class Carrier(BaseModel):
    id: str
    rating: float = Field(ge=0, le=5)
    cost_per_km: float = Field(ge=0)
    availability: float = Field(ge=0, le=1)
    verified: bool = True

class Order(BaseModel):
    id: str
    origin: str
    destination: str
    weight_kg: float = Field(gt=0)
    revenue_pln: float = Field(ge=0)

class Route(BaseModel):
    distance_km: float = Field(gt=0)
    toll_cost_pln: float = Field(ge=0)

class OptimizeRequest(BaseModel):
    order: Order
    route: Route
    vehicles: list[Vehicle]
    carriers: list[Carrier]
    fuel_price_pln_per_litre: float = Field(gt=0)
    target_margin_pct: float = Field(ge=0, le=100)
