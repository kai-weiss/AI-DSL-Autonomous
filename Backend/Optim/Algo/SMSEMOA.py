from __future__ import annotations

from typing import Callable, Dict, List, Tuple
import random
from multiprocessing.pool import ThreadPool

from deap import base, creator, tools, algorithms
from deap.tools import emo
from deap.tools._hypervolume import hv

from .common import Individual, PlateauDetector

__all__ = ["SMSEMOA"]


class SMSEMOA:
    """A steady-state SMS-EMOA implementation built on top of DEAP"""

    def __init__(
        self,
        variables: Dict[str, tuple[float, float]],
        evaluate: Callable[[Dict[str, float]], List[float]],
        pop_size: int = 20,
        generations: int = 10,
        crossover_prob: float = 0.9,
        mutation_prob: float = 0.1,
        workers: int | None = None,
    ) -> None:
        self.variables = variables
        self.evaluate = evaluate
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.workers = workers

        self.names = list(self.variables.keys())
        self.bounds = list(self.variables.values())
        sample = {n: (b[0] + b[1]) / 2 for n, b in self.variables.items()}
        self.num_objectives = len(self.evaluate(sample))

    # ------------------------------------------------------------------
    def run(
        self,
        log_history: bool = False,
        plateau_detector: PlateauDetector | None = None,
    ) -> List[Individual] | Tuple[List[Individual], List[List[List[float]]], int, bool]:
        if not hasattr(creator, "FitnessMulti"):
            creator.create(
                "FitnessMulti",
                base.Fitness,
                weights=(-1.0,) * self.num_objectives,
            )
        if not hasattr(creator, "Ind"):
            creator.create("Ind", list, fitness=creator.FitnessMulti)
        toolbox = base.Toolbox()

        lows = [b[0] for b in self.bounds]
        highs = [b[1] for b in self.bounds]

        def make_ind():
            return [random.uniform(l, h) for l, h in self.bounds]

        toolbox.register("individual", tools.initIterate, creator.Ind, make_ind)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("clone", lambda ind: creator.Ind(ind))

        def eval_ind(ind):
            values = {n: v for n, v in zip(self.names, ind)}
            return self.evaluate(values)

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

            for gen_idx in range(1, self.generations + 1):
                offspring = algorithms.varOr(
                    population,
                    toolbox,
                    lambda_=self.pop_size,
                    cxpb=self.crossover_prob,
                    mutpb=self.mutation_prob,
                )
                fitnesses = list(toolbox.map(toolbox.evaluate, offspring))
                for ind, fit in zip(offspring, fitnesses):
                    ind.fitness.values = fit

                evaluations += len(offspring)
                population.extend(offspring)
                population = self._reduce_population(population)

                first_front = emo.sortNondominated(population, len(population))[0]
                front_values = [list(ind.fitness.values) for ind in first_front]
                if log_history:
                    history.append(front_values)
                if plateau_detector and plateau_detector.update(front_values, gen_idx):
                    stopped_early = True
                    break

            fronts = emo.sortNondominated(population, len(population))
            for rank, front in enumerate(fronts):
                emo.assignCrowdingDist(front)
                for ind in front:
                    ind.rank = rank

            result: List[Individual] = []
            for deap_ind in population:
                values = {n: v for n, v in zip(self.names, deap_ind)}
                result.append(
                    Individual(
                        values=values,
                        objectives=list(deap_ind.fitness.values),
                        rank=getattr(deap_ind, "rank", None),
                        crowding_distance=getattr(deap_ind, "crowding_dist", 0.0),
                    )
                )
            if log_history:
                return result, history, evaluations, stopped_early
            return result
        finally:
            if pool is not None:
                pool.close()
                pool.join()

    # ------------------------------------------------------------------
    def _reduce_population(self, population: List[creator.Ind]) -> List[creator.Ind]:
        fronts = emo.sortNondominated(population, len(population))
        new_population: List[creator.Ind] = []
        for front in fronts:
            if len(new_population) + len(front) <= self.pop_size:
                new_population.extend(front)
                continue

            remaining = self.pop_size - len(new_population)
            truncated = self._truncate_front(list(front), remaining, population)
            new_population.extend(truncated)
            break

        return new_population

    def _truncate_front(
        self,
        front: List[creator.Ind],
        target_size: int,
        population: List[creator.Ind],
    ) -> List[creator.Ind]:
        if target_size <= 0:
            return []

        while len(front) > target_size:
            ref_point = self._reference_point(population)
            contributions = self._hypervolume_contributions(front, ref_point)
            worst_index = contributions.index(min(contributions))
            front.pop(worst_index)

        return front

    def _reference_point(self, population: List[creator.Ind]) -> List[float]:
        ref = [float("-inf")] * self.num_objectives
        for ind in population:
            for idx, value in enumerate(ind.fitness.values):
                ref[idx] = max(ref[idx], value)
        return [value + 1.0 for value in ref]

    def _hypervolume_contributions(
        self, front: List[creator.Ind], ref_point: List[float]
    ) -> List[float]:
        points = [list(ind.fitness.values) for ind in front]
        base_hv = hv.hypervolume(points, ref_point)
        contributions: List[float] = []
        for idx in range(len(front)):
            reduced = points[:idx] + points[idx + 1 :]
            reduced_hv = hv.hypervolume(reduced, ref_point) if reduced else 0.0
            contributions.append(base_hv - reduced_hv)
        return contributions