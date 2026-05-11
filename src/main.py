from __future__ import annotations

import logging

from src.config import settings
from src.database import create_db_engine, load_planning_data, save_plan
from src.export import export_csv_reports, plot_gantt, plot_resource_load
from src.planner import CRPPlanner


def configure_logging() -> None:
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    engine = create_db_engine(settings.db_url)
    data = load_planning_data(engine)

    planner = CRPPlanner(
        orders=data["orders"],
        routes=data["routes"],
        capacity=data["capacity"],
        horizon_start=settings.HORIZON_START,
        product_labels=data["product_labels"],
        resource_labels=data["resource_labels"],
    )
    plan = planner.run()

    saved_rows = save_plan(engine, plan)
    logger.info("Saved %s rows to mrp_plan", saved_rows)

    csv_paths = export_csv_reports(plan, data["product_labels"], settings.OUTPUT_DIR)
    gantt_path = plot_gantt(
        plan,
        data["resource_labels"],
        settings.HORIZON_START,
        settings.HORIZON_END,
        settings.OUTPUT_DIR,
    )
    load_path = plot_resource_load(
        plan,
        planner.initial_capacity,
        data["resource_labels"],
        settings.HORIZON_START,
        settings.HORIZON_END,
        settings.OUTPUT_DIR,
    )

    for path in [*csv_paths, gantt_path, load_path]:
        if path is not None:
            logger.info("Exported %s", path)


if __name__ == "__main__":
    main()
