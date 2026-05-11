from __future__ import annotations

import logging
import math
from datetime import date, timedelta

from src.models import OperationSpec, PlanRow, SalesOrder

logger = logging.getLogger(__name__)


class CRPPlanner:
    """Builds a backward MRP/CRP plan with resource and order-day capacity limits."""

    def __init__(
        self,
        orders: list[SalesOrder],
        routes: dict[int, list[OperationSpec]],
        capacity: dict[tuple[date, int], float],
        horizon_start: date,
        product_labels: dict[int, str],
        resource_labels: dict[int, str],
    ) -> None:
        self.orders = orders
        self.routes = routes
        self.initial_capacity = capacity.copy()
        self.remaining_capacity = capacity.copy()
        self.horizon_start = horizon_start
        self.product_labels = product_labels
        self.resource_labels = resource_labels
        self.plan: list[PlanRow] = []

    @staticmethod
    def _round_up_to_multiple(weight: float, unit: float) -> float:
        if unit <= 0:
            return weight
        return math.ceil(weight / unit) * unit

    def run(self) -> list[PlanRow]:
        logger.info("Starting MRP/CRP calculation for %s orders", len(self.orders))
        for order in self.orders:
            self._schedule_order(order)
        logger.info("MRP/CRP calculation finished: %s plan rows", len(self.plan))
        return self.plan

    def _schedule_order(self, order: SalesOrder) -> None:
        qty = math.floor(order.target_weight / order.unit_weight)
        delivery_weight = qty * order.unit_weight
        if abs(delivery_weight - order.target_weight) > order.tolerance:
            logger.warning(
                "Skipping order %s: delivery weight %.3f is outside %.3f +/- %.3f",
                order.sales_order_id,
                delivery_weight,
                order.target_weight,
                order.tolerance,
            )
            return

        route = self.routes.get(order.product_id)
        if not route:
            logger.warning(
                "Skipping order %s: product %s has no route",
                order.sales_order_id,
                order.product_id,
            )
            return

        stages = self._calculate_stages(route, delivery_weight, order.unit_weight)
        logger.info(
            "Order %s (%s), due=%s, delivery=%.1f t, units=%s",
            order.sales_order_id,
            self.product_labels.get(order.product_id, str(order.product_id)),
            order.due_date,
            delivery_weight,
            qty,
        )

        order_day_load: dict[date, float] = {}
        day_cursor = order.due_date
        for op, total_tons, total_units, total_hours in reversed(stages):
            remaining_hours = total_hours
            while remaining_hours > 1e-9:
                key = (day_cursor, op.resource_id)
                resource_slack = self.remaining_capacity.get(key, 0.0)
                order_slack = 24.0 - order_day_load.get(day_cursor, 0.0)
                free_hours = min(resource_slack, order_slack)

                if free_hours <= 1e-9:
                    day_cursor -= timedelta(days=1)
                    if day_cursor < self.horizon_start - timedelta(days=30):
                        resource_name = self.resource_labels.get(
                            op.resource_id, str(op.resource_id)
                        )
                        raise RuntimeError(
                            f"Order {order.sales_order_id}: not enough capacity on {resource_name}"
                        )
                    continue

                portion = min(free_hours, remaining_hours)
                self.remaining_capacity[key] = resource_slack - portion
                order_day_load[day_cursor] = order_day_load.get(day_cursor, 0.0) + portion

                tons_slice = portion / total_hours * total_tons
                units_slice = portion / total_hours * total_units
                self.plan.append(
                    PlanRow(
                        sales_order_id=order.sales_order_id,
                        product_id=order.product_id,
                        resource_id=op.resource_id,
                        operation_id=op.operation_id,
                        plan_date=day_cursor,
                        hours=round(portion, 3),
                        tons=round(tons_slice, 3),
                        units=round(units_slice, 3),
                    )
                )

                remaining_hours -= portion
                if remaining_hours > 1e-9:
                    day_cursor -= timedelta(days=1)

    def _calculate_stages(
        self,
        route: list[OperationSpec],
        delivery_weight: float,
        unit_weight: float,
    ) -> list[tuple[OperationSpec, float, float, float]]:
        stages: list[tuple[OperationSpec, float, float, float]] = []
        downstream_weight = delivery_weight
        for index in range(len(route) - 1, -1, -1):
            op = route[index]
            if index == len(route) - 1:
                current_weight = downstream_weight
            else:
                current_weight = self._round_up_to_multiple(
                    downstream_weight / op.yield_,
                    unit_weight,
                )
            current_units = current_weight / unit_weight
            current_hours = current_weight / op.performance
            stages.append((op, current_weight, current_units, current_hours))
            downstream_weight = current_weight
        stages.reverse()
        return stages
