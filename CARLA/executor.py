from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Dict, Optional

from .behaviour import BehaviourRegistry, CARLA_CLIENT_PROPERTY
from .model import LocationSpec, RotationSpec, ScenarioSpec, SpawnPointSpec, VehicleSpec
from .scheduler import Scheduler

LOGGER = logging.getLogger(__name__)


class CarlaScenarioExecutor:
    """Runtime bridge that executes DSL scenarios inside CARLA."""

    def __init__(
            self,
            scenario: ScenarioSpec,
            *,
            host: str = "localhost",
            port: int = 2000,
            timeout: float = 5.0,
            behaviour_registry: BehaviourRegistry | None = None,
    ) -> None:
        self.scenario = scenario
        self.host = host
        self.port = port
        self.timeout = timeout
        self.behaviour_registry = behaviour_registry or BehaviourRegistry.with_default_behaviours()

        self._client = None
        self._world = None
        self._original_settings = None
        self._actors: Dict[str, object] = {}
        self._scheduler = Scheduler(scenario, registry=self.behaviour_registry)

        self._spectator = None
        self._overtaking_vehicle_name: Optional[str] = None
        self._spectator_follow_distance = 7.5
        self._spectator_follow_height = 3.0

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def setup(self) -> None:
        if self._world is not None:
            LOGGER.debug("CARLA scenario already set up")
            return

        client = self._connect()
        self._store_carla_client_reference(client)
        world = self._prepare_world(client)
        self._apply_weather(world)

        self._spectator = self._safe_get_spectator(world)
        self._spawn_vehicles(world)
        self._update_spectator_follow()

        self._client = client
        self._world = world
        LOGGER.info("CARLA scenario '%s' initialised", self.scenario.name)

    def teardown(self) -> None:
        if self._world is None:
            return
        LOGGER.info("Tearing down CARLA scenario '%s'", self.scenario.name)
        try:
            self._scheduler.teardown(self._world)
        finally:
            self._destroy_actors()
            if self._original_settings is not None:
                try:
                    self._world.apply_settings(self._original_settings)
                except Exception:  # pragma: no cover - depends on CARLA API
                    LOGGER.exception("Failed to restore CARLA world settings")
            self._world = None
            self._client = None
            self._original_settings = None
            self._spectator = None
            self._actors.clear()
            self._clear_carla_client_reference()

    # ------------------------------------------------------------------
    # Execution loop
    # ------------------------------------------------------------------
    def run(self, duration_seconds: float | None = None, max_steps: int | None = None) -> None:
        if self._world is None:
            raise RuntimeError("Scenario has not been set up; call setup() first")

        synchronous = self._world.get_settings().synchronous_mode
        fixed_dt = self._world.get_settings().fixed_delta_seconds or 0.05
        sim_time = 0.0
        steps = 0

        if duration_seconds is None and max_steps is None:
            LOGGER.info("No stopping criteria supplied; simulation will run until interrupted")

        while True:
            if synchronous:
                self._world.tick()
                snapshot = self._world.get_snapshot()
                dt = getattr(snapshot.timestamp, "delta_seconds", fixed_dt)
            else:
                snapshot = self._world.wait_for_tick()
                dt = getattr(snapshot.timestamp, "delta_seconds", fixed_dt)
            sim_time += dt
            steps += 1

            self._scheduler.step(self._world, sim_time, dt)
            self._update_spectator_follow()

            if duration_seconds is not None and sim_time >= duration_seconds:
                LOGGER.info("Simulation duration %.2fs reached", sim_time)
                break
            if max_steps is not None and steps >= max_steps:
                LOGGER.info("Maximum steps %d reached", steps)
                break

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _connect(self):
        import carla  # type: ignore

        client = carla.Client(self.host, self.port)
        client.set_timeout(self.timeout)
        LOGGER.info("Connected to CARLA server %s:%s", self.host, self.port)
        return client

    def _prepare_world(self, client):
        import carla  # type: ignore

        scenario_world = self.scenario.world
        world = None

        if scenario_world.map_name:
            map_name = scenario_world.map_name
            if map_name.endswith(".xodr"):
                xodr_path = Path(map_name)
                if xodr_path.exists():
                    opendrive = xodr_path.read_text(encoding="utf-8")
                    world = client.generate_opendrive_world(opendrive)
                    LOGGER.info("Generated OpenDRIVE world from '%s'", map_name)
                else:
                    LOGGER.warning("OpenDRIVE file '%s' not found; falling back to current world", map_name)
            if world is None:
                world = client.load_world(map_name)
                LOGGER.info("Loaded CARLA map '%s'", map_name)
        else:
            world = client.get_world()
            LOGGER.info("Using existing CARLA world '%s'", world.get_map().name)

        self._original_settings = world.get_settings()
        desired = world.get_settings()
        desired.synchronous_mode = bool(scenario_world.synchronous_mode)
        if scenario_world.fixed_delta_seconds:
            desired.fixed_delta_seconds = scenario_world.fixed_delta_seconds
        world.apply_settings(desired)
        return world

    def _apply_weather(self, world) -> None:
        if not self.scenario.world.weather:
            return
        try:
            weather = world.get_weather()
            for key, value in self.scenario.world.weather.items():
                if hasattr(weather, key):
                    setattr(weather, key, value)
                else:
                    LOGGER.debug("Weather attribute '%s' not recognised by CARLA", key)
            world.set_weather(weather)
            LOGGER.info("Applied custom weather profile")
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to apply weather settings")

    def _spawn_vehicles(self, world) -> None:
        for vehicle in self.scenario.vehicles:
            actor = self._spawn_vehicle(world, vehicle)
            self._actors[vehicle.name] = actor
            self._register_vehicle_actor(vehicle.name, actor)
            self._scheduler.bind_vehicle(vehicle, actor)
            if actor is not None and self._is_overtaking_vehicle(vehicle):
                self._overtaking_vehicle_name = vehicle.name

    def _spawn_vehicle(self, world, vehicle: VehicleSpec):
        import carla  # type: ignore

        blueprint_library = world.get_blueprint_library()
        blueprint_id = vehicle.blueprint or "vehicle.tesla.model3"
        try:
            blueprint = blueprint_library.find(blueprint_id)
        except IndexError:
            matches = blueprint_library.filter(blueprint_id)
            if not matches:
                LOGGER.warning("No blueprint '%s'; defaulting to vehicle.*", blueprint_id)
                blueprint = blueprint_library.filter("vehicle.*")[0]
            else:
                blueprint = matches[0]

        actor = None
        spawn_candidates = list(self._candidate_spawn_points(world, vehicle.spawn))
        if not spawn_candidates:
            spawn_candidates = [carla.Transform()]

        for attempt, spawn_point in enumerate(spawn_candidates, start=1):
            try:
                actor = world.try_spawn_actor(blueprint, spawn_point)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception(
                    "Failed to spawn vehicle '%s' on attempt %d", vehicle.name, attempt
                )
                continue

            if actor is not None:
                if attempt > 1:
                    LOGGER.info(
                        "Spawned vehicle '%s' with blueprint '%s' after %d attempts",
                        vehicle.name,
                        blueprint.id,
                        attempt,
                    )
                else:
                    LOGGER.info(
                        "Spawned vehicle '%s' with blueprint '%s'", vehicle.name, blueprint.id
                    )
                break

            LOGGER.debug(
                "Spawn candidate %d for vehicle '%s' occupied; trying next option",
                attempt,
                vehicle.name,
            )

        if actor is None:
            LOGGER.error(
                "Unable to spawn vehicle '%s'; all %d candidate spawn points were occupied",
                vehicle.name,
                len(spawn_candidates),
            )
        return actor

    def _register_vehicle_actor(self, vehicle_name: str, actor: object | None) -> None:
        """Keep track of spawned actor identifiers for cross-component coordination."""

        if not hasattr(self.scenario, "properties"):
            return

        registry = self.scenario.properties.setdefault("_vehicle_actor_ids", {})
        if actor is None:
            registry.pop(vehicle_name, None)
            return

        actor_id = getattr(actor, "id", None)
        if actor_id is not None:
            registry[vehicle_name] = actor_id

    def _resolve_spawn_point(self, world, spec: SpawnPointSpec | None):
        import carla  # type: ignore

        map_spawn_points = world.get_map().get_spawn_points()
        if spec is None:
            return map_spawn_points[0] if map_spawn_points else carla.Transform()

        target_index = spec.index if spec.index is not None else spec.map_point
        if target_index is not None:
            if 0 <= target_index < len(map_spawn_points):
                return map_spawn_points[target_index]
            label = "index" if spec.index is not None else "map_point"
            LOGGER.warning(
                "Spawn %s %s for vehicle out of range (available %d)",
                label,
                target_index,
                len(map_spawn_points),
            )

        location = None
        rotation = None
        if spec.location:
            location = carla.Location(spec.location.x, spec.location.y, spec.location.z)
        if spec.rotation:
            rotation = carla.Rotation(spec.rotation.pitch, spec.rotation.yaw, spec.rotation.roll)
        if location or rotation:
            return carla.Transform(location or carla.Location(), rotation or carla.Rotation())
        return map_spawn_points[0] if map_spawn_points else carla.Transform()

    def _candidate_spawn_points(self, world, spec: SpawnPointSpec | None):
        import carla  # type: ignore

        map_spawn_points = world.get_map().get_spawn_points()
        if not map_spawn_points:
            yield carla.Transform()
            return

        primary = self._resolve_spawn_point(world, spec) if spec is not None else None
        yielded: set[tuple[float, float, float, float, float, float]] = set()

        def _key(transform):
            location = transform.location
            rotation = transform.rotation
            return (
                round(location.x, 3),
                round(location.y, 3),
                round(location.z, 3),
                round(rotation.pitch, 1),
                round(rotation.yaw, 1),
                round(rotation.roll, 1),
            )

        if primary is not None:
            key = _key(primary)
            yielded.add(key)
            yield primary

        for transform in map_spawn_points:
            key = _key(transform)
            if key in yielded:
                continue
            yielded.add(key)
            yield transform

        def _key(transform):
            location = transform.location
            rotation = transform.rotation
            return (
                round(location.x, 3),
                round(location.y, 3),
                round(location.z, 3),
                round(rotation.pitch, 1),
                round(rotation.yaw, 1),
                round(rotation.roll, 1),
            )

        if primary is not None:
            key = _key(primary)
            yielded.add(key)
            yield primary

        for transform in map_spawn_points:
            key = _key(transform)
            if key in yielded:
                continue
            yielded.add(key)
            yield transform

    def _destroy_actors(self) -> None:
        if not self._actors:
            return
        for name, actor in list(self._actors.items()):
            if actor is None:
                continue
            try:
                actor.destroy()
                LOGGER.debug("Destroyed actor for vehicle '%s'", name)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Failed to destroy actor for vehicle '%s'", name)
        self._actors.clear()
        if hasattr(self.scenario, "properties"):
            actor_registry = self.scenario.properties.get("_vehicle_actor_ids")
            if isinstance(actor_registry, dict):
                actor_registry.clear()

    def _store_carla_client_reference(self, client: object) -> None:
        properties = getattr(self.scenario, "properties", None)
        if isinstance(properties, dict):
            properties[CARLA_CLIENT_PROPERTY] = client

    def _clear_carla_client_reference(self) -> None:
        properties = getattr(self.scenario, "properties", None)
        if isinstance(properties, dict):
            properties.pop(CARLA_CLIENT_PROPERTY, None)

    # ------------------------------------------------------------------
    # Spectator camera helpers
    # ------------------------------------------------------------------
    def _safe_get_spectator(self, world):
        get_spectator = getattr(world, "get_spectator", None)
        if not callable(get_spectator):
            return None
        try:
            return get_spectator()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to obtain CARLA spectator")
            return None

    def _is_overtaking_vehicle(self, vehicle: VehicleSpec) -> bool:
        for component in vehicle.components:
            behaviour = (component.behaviour or "").lower()
            if behaviour in {"tm_overtake_on_ack", "overtake_on_ack"}:
                return True
        return False

    def _update_spectator_follow(self) -> None:
        if self._spectator is None or self._overtaking_vehicle_name is None:
            return

        actor = self._actors.get(self._overtaking_vehicle_name)
        if actor is None:
            return

        try:
            base_transform = actor.get_transform()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception(
                "Failed to query transform for overtaking vehicle '%s'", self._overtaking_vehicle_name
            )
            return

        try:
            import carla  # type: ignore
        except ModuleNotFoundError:  # pragma: no cover - runtime environment without CARLA
            LOGGER.debug("CARLA Python API unavailable; spectator follow disabled")
            self._spectator = None
            return

        yaw_rad = math.radians(base_transform.rotation.yaw)
        forward_x = math.cos(yaw_rad)
        forward_y = math.sin(yaw_rad)

        location = carla.Location(
            base_transform.location.x - forward_x * self._spectator_follow_distance,
            base_transform.location.y - forward_y * self._spectator_follow_distance,
            base_transform.location.z + self._spectator_follow_height,
        )

        rotation = carla.Rotation(
            pitch=-10.0,
            yaw=base_transform.rotation.yaw,
            roll=0.0,
        )

        transform = carla.Transform(location, rotation)
        try:
            self._spectator.set_transform(transform)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to update spectator transform")
