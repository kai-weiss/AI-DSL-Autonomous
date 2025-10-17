from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import CarlaScenarioExecutor, load_scenario


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute an AI-DSL scenario inside CARLA")
    parser.add_argument("scenario", type=Path, help="Path to the DSL JSON export")
    parser.add_argument("--host", default="localhost", help="CARLA host address")
    parser.add_argument("--port", type=int, default=2000, help="CARLA RPC port")
    parser.add_argument("--timeout", type=float, default=300.0, help="Connection timeout in seconds")
    parser.add_argument("--duration", type=float, default=None, help="Simulation duration in seconds")
    parser.add_argument("--max-steps", type=int, default=None, help="Maximum number of simulation steps to execute")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s:%(name)s:%(message)s")

    scenario = load_scenario(args.scenario)
    executor = CarlaScenarioExecutor(
        scenario,
        host=args.host,
        port=args.port,
        timeout=args.timeout,
    )

    executor.setup()
    try:
        executor.run(duration_seconds=args.duration, max_steps=args.max_steps)
    finally:
        executor.teardown()


if __name__ == "__main__":
    main()