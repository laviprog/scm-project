from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class OperationSpec:
    operation_id: int
    resource_id: int
    performance: float
    yield_: float


@dataclass(frozen=True)
class SalesOrder:
    sales_order_id: int
    product_id: int
    target_weight: float
    tolerance: float
    unit_weight: float
    due_date: date
    priority: int
    status: int


@dataclass(frozen=True)
class PlanRow:
    sales_order_id: int
    product_id: int
    resource_id: int
    operation_id: int
    plan_date: date
    hours: float
    tons: float
    units: float
