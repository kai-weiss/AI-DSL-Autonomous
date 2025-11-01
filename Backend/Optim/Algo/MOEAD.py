from __future__ import annotations

import random
from multiprocessing.pool import ThreadPool
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from deap import base, creator, tools
from deap.tools import emo

from .common import Individual, PlateauDetector

__all__ = ["MOEAD"]


class MOEAD:
    """Bi-objective MOEA/D with Tchebycheff aggregation."""

    def __init__(
        self,
        variables: Dict[str, Tuple[float, float]],
        evaluate: Callable[[Dict[str, float]], Sequence[float]],
        *,
        pop_size: int = 50,
        generations: int = 50,
        crossover_prob: float = 1.0,
        mutation_prob: float = 1.0,
        neighbor_size: int | None = None,
        workers: int | None = None,
    ) -> None:
        if pop_size <= 0:
            raise ValueError("pop_size must be positive")
        if generations <= 0:
            raise ValueError("generations must be positive")

        self.variables = variables
        self.evaluate = evaluate
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.workers = workers

        self.names = list(self.variables.keys())
        self.bounds = [tuple(map(float, b)) for b in self.variables.values()]
        sample = {n: (lo + hi) / 2 for n, (lo, hi) in self.variables.items()}
        objectives = self.evaluate(sample)
        self.num_objectives = len(objectives)
        if self.num_objectives < 2:
            raise ValueError("MOEA/D requires at least two objectives")

        self.neighbor_size = (
            int(neighbor_size)
            if neighbor_size is not None
            else max(2, min(10, self.pop_size // 5))
        )

    # ------------------------------------------------------------------
    def run(
        self,
        log_history: bool = False,
        plateau_detector: PlateauDetector | None = None,
    ) -> (
        List[Individual]
        | Tuple[List[Individual], List[List[List[float]]], int, bool]
    ):
        self._ensure_creators()
        toolbox = base.Toolbox()

        lows = [b[0] for b in self.bounds]
        highs = [b[1] for b in self.bounds]

        def make_ind() -> creator.MOEADInd:
            values = [random.uniform(l, h) for l, h in self.bounds]
            return creator.MOEADInd(values)

        toolbox.register("individual", make_ind)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("clone", lambda ind: creator.MOEADInd(ind))

        def eval_ind(ind: Sequence[float]) -> Tuple[float, ...]:
            values = {n: float(v) for n, v in zip(self.names, ind)}
            return tuple(float(x) for x in self.evaluate(values))

        toolbox.register("evaluate", eval_ind)
        toolbox.register(
            "mate",
            tools.cxSimulatedBinaryBounded,
            low=lows,
            up=highs,
            eta=15.0,
        )
        toolbox.register(
            "mutate",
            tools.mutPolynomialBounded,
            low=lows,
            up=highs,
            eta=20.0,
            indpb=1.0 / len(self.bounds),
        )

        pool: ThreadPool | None = None
        if self.workers is not None and self.workers <= 1:
            toolbox.register("map", map)
        elif self.workers is None:
            pool = ThreadPool()
            toolbox.register("map", pool.map)
        else:
            pool = ThreadPool(processes=self.workers)
            toolbox.register("map", pool.map)

        try:
            population = toolbox.population(n=self.pop_size)
            fitnesses = list(toolbox.map(toolbox.evaluate, population))
            for ind, fit in zip(population, fitnesses):
                ind.fitness.values = fit

            evaluations = len(population)
            history: List[List[List[float]]] = []
            stopped_early = False

            weight_vectors = self._generate_weights(self.pop_size)
            neighborhoods = self._build_neighborhoods(weight_vectors)
            reference = np.min(np.asarray(fitnesses, dtype=float), axis=0)

            for gen_idx in range(1, self.generations + 1):
                offspring_records: List[Tuple[int, creator.MOEADInd]] = []

                for idx in range(self.pop_size):
                    neigh = neighborhoods[idx]
                    parents = random.sample(neigh, k=min(2, len(neigh)))
                    p1 = toolbox.clone(population[parents[0]])
                    if len(parents) > 1:
                        p2 = toolbox.clone(population[parents[1]])
                    else:
                        p2 = toolbox.clone(population[idx])

                    child = toolbox.clone(population[idx])
                    if random.random() < self.crossover_prob:
                        child1, child2 = toolbox.mate(p1, p2)
                        child = child1 if random.random() < 0.5 else child2
                    if random.random() < self.mutation_prob:
                        toolbox.mutate(child)
                    self._repair(child)
                    offspring_records.append((idx, child))

                offspring = [child for _, child in offspring_records]
                offspring_fits = list(toolbox.map(toolbox.evaluate, offspring))
                evaluations += len(offspring)

                for (idx, child), fit in zip(offspring_records, offspring_fits):
                    child.fitness.values = fit
                    reference = np.minimum(reference, fit)
                    self._update_neighbors(
                        population,
                        child,
                        fit,
                        reference,
                        neighborhoods[idx],
                        weight_vectors,
                    )

                first_front = emo.sortNondominated(population, len(population))[0]
                front_values = [list(ind.fitness.values) for ind in first_front]
                if log_history:
                    history.append(front_values)
                if plateau_detector and plateau_detector.update(front_values, gen_idx):
                    stopped_early = True
                    break

            result = [self._to_individual(ind) for ind in population]
            if log_history:
                return result, history, evaluations, stopped_early
            return result
        finally:
            if pool is not None:
                pool.close()
                pool.join()

    # ------------------------------------------------------------------
    def _ensure_creators(self) -> None:
        if not hasattr(creator, "MOEADFitness"):
            creator.create(
                "MOEADFitness",
                base.Fitness,
                weights=(-1.0,) * self.num_objectives,
            )
        if not hasattr(creator, "MOEADInd"):
            creator.create("MOEADInd", list, fitness=creator.MOEADFitness)

    def _generate_weights(self, size: int) -> List[np.ndarray]:
        if size == 1:
            return [np.ones(self.num_objectives) / self.num_objectives]

        weights: List[np.ndarray] = []
        for i in range(size):
            w = np.zeros(self.num_objectives, dtype=float)
            fraction = i / (size - 1)
            w[0] = fraction
            w[1] = 1.0 - fraction
            if self.num_objectives > 2:
                # distribute remaining weight evenly across other objectives
                remaining = max(0.0, 1.0 - (w[0] + w[1]))
                for j in range(2, self.num_objectives):
                    w[j] = remaining / (self.num_objectives - 2)
            weights.append(w)
        return weights

    def _build_neighborhoods(self, weights: List[np.ndarray]) -> List[List[int]]:
        matrix = np.vstack(weights)
        distances = np.linalg.norm(matrix[:, None, :] - matrix[None, :, :], axis=2)
        neighbors: List[List[int]] = []
        for idx in range(len(weights)):
            order = np.argsort(distances[idx])
            neigh = [int(j) for j in order[: self.neighbor_size]]
            if idx not in neigh:
                neigh.append(idx)
            neighbors.append(neigh)
        return neighbors

    def _update_neighbors(
        self,
        population: List[creator.MOEADInd],
        child: creator.MOEADInd,
        fit: Sequence[float],
        reference: np.ndarray,
        neighborhood: Iterable[int],
        weights: List[np.ndarray],
    ) -> None:
        for j in neighborhood:
            incumbent = population[j]
            if self._tchebycheff(fit, weights[j], reference) <= self._tchebycheff(
                incumbent.fitness.values,
                weights[j],
                reference,
            ):
                population[j][:] = list(child)
                population[j].fitness.values = tuple(map(float, fit))

    def _tchebycheff(
        self,
        objectives: Sequence[float],
        weight: Sequence[float],
        reference: Sequence[float],
    ) -> float:
        vals = [
            w if w > 0 else 1e-6
            for w in (float(value) for value in weight)
        ]
        return max(
            val * abs(float(obj) - float(ref))
            for obj, val, ref in zip(objectives, vals, reference)
        )

    def _repair(self, individual: Sequence[float]) -> None:
        for idx, (lo, hi) in enumerate(self.bounds):
            if individual[idx] < lo:
                individual[idx] = lo
            elif individual[idx] > hi:
                individual[idx] = hi

    def _to_individual(self, deap_ind: creator.MOEADInd) -> Individual:
        values = {n: float(v) for n, v in zip(self.names, deap_ind)}
        return Individual(
            values=values,
            objectives=list(map(float, deap_ind.fitness.values)),
            rank=None,
            crowding_distance=0.0,
        )