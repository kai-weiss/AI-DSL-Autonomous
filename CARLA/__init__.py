"""CARLA runtime bridge.

Provides a interpreter that consumes the JSON export of
DSL models. The interpreter reads the model, prepares the
CARLA world, spawns vehicles, and executes component behaviours according to
their scheduling attributes.
"""

from .json_loader import load_scenario
from .executor import CarlaScenarioExecutor
from .behaviour import BehaviourRegistry, ComponentBehaviour
from .model import ScenarioSpec, VehicleSpec, ComponentSpec, ConnectionSpec

__all__ = [
    "load_scenario",
    "CarlaScenarioExecutor",
    "BehaviourRegistry",
    "ComponentBehaviour",
    "ScenarioSpec",
    "VehicleSpec",
    "ComponentSpec",
    "ConnectionSpec",
]