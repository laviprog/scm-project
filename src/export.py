from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from src.models import PlanRow


def export_csv_reports(
    plan: list[PlanRow],
    product_labels: dict[int, str],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dates = _sorted_plan_dates(plan)
    reports = [
        ("plan_hours.csv", "hours", 2),
        ("plan_tons.csv", "tons", 0),
        ("plan_units.csv", "units", 0),
    ]
    paths: list[Path] = []
    for filename, metric, decimals in reports:
        path = output_dir / filename
        _write_pivot_csv(path, plan, product_labels, dates, metric, decimals)
        paths.append(path)
    return paths


def plot_gantt(
    plan: list[PlanRow],
    resource_labels: dict[int, str],
    horizon_start: date,
    horizon_end: date,
    output_dir: Path,
) -> Path | None:
    if not plan:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "gantt_plan.png"
    order_ids = sorted({row.sales_order_id for row in plan})
    resource_ids = sorted({row.resource_id for row in plan})
    palette = _resource_palette(resource_ids)

    fig, ax = plt.subplots(figsize=(13.5, 0.8 * len(order_ids) + 2))
    for order_index, order_id in enumerate(order_ids):
        order_rows = [row for row in plan if row.sales_order_id == order_id]
        operation_groups = sorted(
            {
                (row.resource_id, row.operation_id): min(
                    r.plan_date
                    for r in order_rows
                    if r.resource_id == row.resource_id and r.operation_id == row.operation_id
                )
                for row in order_rows
            }.items(),
            key=lambda item: (item[1], item[0][1]),
        )
        lane_count = max(1, len(operation_groups))
        band_height = 0.82
        lane_height = band_height / lane_count * 0.9

        for lane_index, ((resource_id, operation_id), _first_date) in enumerate(operation_groups):
            lane_y = (
                order_index
                - band_height / 2
                + lane_height / 2
                + lane_index * (band_height / lane_count)
            )
            rows = [
                row
                for row in order_rows
                if row.resource_id == resource_id and row.operation_id == operation_id
            ]
            for row in rows:
                ax.barh(
                    lane_y,
                    0.9,
                    left=mdates.date2num(row.plan_date) + 0.05,
                    height=lane_height,
                    color=palette[resource_id],
                    edgecolor="black",
                    linewidth=0.4,
                    align="center",
                )
                ax.text(
                    mdates.date2num(row.plan_date) + 0.5,
                    lane_y,
                    f"{row.hours:.1f}",
                    ha="center",
                    va="center",
                    fontsize=6.2,
                    color="black",
                )

    ax.set_yticks(range(len(order_ids)))
    ax.set_yticklabels([str(order_id) for order_id in order_ids])
    ax.invert_yaxis()
    _format_date_axis(ax, horizon_start, horizon_end)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.set_title("План MRP/CRP: загрузка агрегатов по заказам")

    handles = [plt.Rectangle((0, 0), 1, 1, color=palette[r]) for r in resource_ids]
    labels = [resource_labels.get(r, str(r)) for r in resource_ids]
    ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)

    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_resource_load(
    plan: list[PlanRow],
    initial_capacity: dict[tuple[date, int], float],
    resource_labels: dict[int, str],
    horizon_start: date,
    horizon_end: date,
    output_dir: Path,
) -> Path | None:
    if not plan:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "resource_load.png"
    resource_ids = sorted({resource_id for _, resource_id in initial_capacity})
    dates = list(_date_range(horizon_start, horizon_end))
    used = defaultdict(float)
    for row in plan:
        used[(row.plan_date, row.resource_id)] += row.hours

    fig, axes = plt.subplots(
        len(resource_ids),
        1,
        figsize=(13.5, max(4.0, 1.2 * len(resource_ids))),
        sharex=True,
    )
    if len(resource_ids) == 1:
        axes = [axes]

    for ax, resource_id in zip(axes, resource_ids, strict=True):
        values = [used[(day, resource_id)] for day in dates]
        capacities = [initial_capacity.get((day, resource_id), 0.0) for day in dates]
        ax.bar(dates, values, width=0.8, color="#5b8def", edgecolor="#2f4f7f", linewidth=0.3)
        ax.plot(dates, capacities, color="#c0392b", linewidth=1.1)
        ax.set_ylabel(resource_labels.get(resource_id, str(resource_id)), rotation=0, ha="right")
        ax.set_ylim(0, max([1.0, *capacities, *values]) * 1.15)
        ax.grid(axis="y", linestyle=":", alpha=0.35)

    _format_date_axis(axes[-1], horizon_start, horizon_end)
    fig.suptitle("Загрузка агрегатов: часы по дням")
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close(fig)
    return path


def _write_pivot_csv(
    path: Path,
    plan: list[PlanRow],
    product_labels: dict[int, str],
    dates: list[date],
    metric: str,
    decimals: int,
) -> None:
    values = defaultdict(float)
    product_ids = sorted(
        {row.product_id for row in plan}, key=lambda pid: product_labels.get(pid, str(pid))
    )
    for row in plan:
        values[(row.product_id, row.plan_date)] += getattr(row, metric)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Материал", *[day.isoformat() for day in dates]])
        for product_id in product_ids:
            writer.writerow(
                [
                    product_labels.get(product_id, str(product_id)),
                    *[
                        _format_number(values.get((product_id, day), 0.0), decimals)
                        if values.get((product_id, day), 0.0)
                        else ""
                        for day in dates
                    ],
                ]
            )


def _sorted_plan_dates(plan: list[PlanRow]) -> list[date]:
    return sorted({row.plan_date for row in plan})


def _format_number(value: float, decimals: int) -> str:
    if decimals == 0:
        return str(round(value))
    return f"{value:.{decimals}f}".replace(".", ",")


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _format_date_axis(ax, horizon_start: date, horizon_end: date) -> None:
    ticks = list(_date_range(horizon_start, horizon_end))
    ax.set_xlim(ticks[0], ticks[-1] + timedelta(days=1))
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=60, ha="right")


def _resource_palette(resource_ids: list[int]) -> dict[int, tuple[float, float, float, float]]:
    cmap = plt.get_cmap("Set2")
    return {resource_id: cmap(index % cmap.N) for index, resource_id in enumerate(resource_ids)}
