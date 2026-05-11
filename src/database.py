from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy import Engine, create_engine, text

from src.models import OperationSpec, PlanRow, SalesOrder


def create_db_engine(db_url: str) -> Engine:
    return create_engine(db_url, future=True)


def load_planning_data(engine: Engine) -> dict[str, Any]:
    with engine.connect() as conn:
        orders_rows = conn.execute(
            text(
                """
                SELECT sales_order_id, product_id, target_weight, tolerance,
                       unit_weight, due_date, priority, status
                FROM sales_orders
                WHERE status = 0
                ORDER BY priority, due_date, sales_order_id
                """
            )
        ).mappings()
        orders = [
            SalesOrder(
                sales_order_id=int(row["sales_order_id"]),
                product_id=int(row["product_id"]),
                target_weight=float(row["target_weight"]),
                tolerance=float(row["tolerance"]),
                unit_weight=float(row["unit_weight"]),
                due_date=row["due_date"],
                priority=int(row["priority"]),
                status=int(row["status"]),
            )
            for row in orders_rows
        ]

        operation_rows = conn.execute(
            text(
                """
                SELECT product_id, resource_id, operation_id, performance, "yield" AS yield_
                FROM standard_operations
                ORDER BY product_id, operation_id
                """
            )
        ).mappings()
        route_buckets: dict[int, list[OperationSpec]] = defaultdict(list)
        for row in operation_rows:
            route_buckets[int(row["product_id"])].append(
                OperationSpec(
                    operation_id=int(row["operation_id"]),
                    resource_id=int(row["resource_id"]),
                    performance=float(row["performance"]),
                    yield_=float(row["yield_"]),
                )
            )
        routes = {
            product_id: sorted(ops, key=lambda op: op.operation_id)
            for product_id, ops in route_buckets.items()
        }

        capacity_rows = conn.execute(
            text(
                """
                SELECT production_date, resource_id, available_hours
                FROM calendar
                """
            )
        ).mappings()
        capacity: dict[tuple[date, int], float] = {
            (row["production_date"], int(row["resource_id"])): float(row["available_hours"])
            for row in capacity_rows
        }

        product_rows = conn.execute(
            text("SELECT product_id, product_desc FROM products")
        ).mappings()
        product_labels = {int(row["product_id"]): str(row["product_desc"]) for row in product_rows}

        resource_rows = conn.execute(
            text("SELECT resource_id, resource_desc FROM resources")
        ).mappings()
        resource_labels = {
            int(row["resource_id"]): str(row["resource_desc"]) for row in resource_rows
        }

    return {
        "orders": orders,
        "routes": routes,
        "capacity": capacity,
        "product_labels": product_labels,
        "resource_labels": resource_labels,
    }


def save_plan(engine: Engine, plan: list[PlanRow]) -> int:
    aggregated: dict[tuple[int, int, int, int, date], dict[str, float]] = {}
    for row in plan:
        key = (
            row.sales_order_id,
            row.product_id,
            row.resource_id,
            row.operation_id,
            row.plan_date,
        )
        if key not in aggregated:
            aggregated[key] = {"hours": 0.0, "tons": 0.0, "units": 0.0}
        aggregated[key]["hours"] += row.hours
        aggregated[key]["tons"] += row.tons
        aggregated[key]["units"] += row.units

    rows = [
        {
            "sales_order_id": sales_order_id,
            "product_id": product_id,
            "resource_id": resource_id,
            "operation_id": operation_id,
            "plan_date": plan_date,
            "hours": round(values["hours"], 3),
            "tons": round(values["tons"], 3),
            "units": round(values["units"], 3),
        }
        for (
            sales_order_id,
            product_id,
            resource_id,
            operation_id,
            plan_date,
        ), values in aggregated.items()
    ]

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS mrp_plan (
                    plan_id BIGSERIAL PRIMARY KEY,
                    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(sales_order_id)
                        ON DELETE CASCADE,
                    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
                    resource_id INTEGER NOT NULL REFERENCES resources(resource_id)
                        ON DELETE CASCADE,
                    operation_id INTEGER NOT NULL,
                    plan_date DATE NOT NULL,
                    hours NUMERIC(12, 3) NOT NULL,
                    tons NUMERIC(18, 3) NOT NULL,
                    units NUMERIC(18, 3) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(text("TRUNCATE mrp_plan RESTART IDENTITY"))
        if rows:
            conn.execute(
                text(
                    """
                    INSERT INTO mrp_plan (
                        sales_order_id, product_id, resource_id, operation_id,
                        plan_date, hours, tons, units
                    )
                    VALUES (
                        :sales_order_id, :product_id, :resource_id, :operation_id,
                        :plan_date, :hours, :tons, :units
                    )
                    """
                ),
                rows,
            )
    return len(rows)
