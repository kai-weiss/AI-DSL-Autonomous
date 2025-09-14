from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List
import random

from deap import base, creator, tools, algorithms
from deap.tools import emo


@dataclass
class Individual:
    """Represents a candidate solution returned from NSGA-II"""

    values: Dict[str, float]
    objectives: List[float]
    rank: int | None = None
    crowding_distance: float = 0.0


class NSGAII:
    """A thin wrapper around DEAP's NSGA-II implementation"""

    def __init__(
        self,
        variables: Dict[str, tuple[float, float]],
        evaluate: Callable[[Dict[str, float]], List[float]],
        pop_size: int = 20,
        generations: int = 10,
        crossover_prob: float = 0.9,
        mutation_prob: float = 0.1,
    ) -> None:
        self.variables = variables
        self.evaluate = evaluate
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob

        self.names = list(self.variables.keys())
        self.bounds = list(self.variables.values())
        sample = {n: (b[0] + b[1]) / 2 for n, b in self.variables.items()}
        self.num_objectives = len(self.evaluate(sample))

    # ------------------------------------------------------------------
    def run(self) -> List[Individual]:
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
        toolbox.register("select", tools.selNSGA2)

        pop = toolbox.population(n=self.pop_size)
        for ind in pop:
            ind.fitness.values = toolbox.evaluate(ind)

        pop, _ = algorithms.eaMuPlusLambda(
            pop,
            toolbox,
            mu=self.pop_size,
            lambda_=self.pop_size,
            cxpb=self.crossover_prob,
            mutpb=self.mutation_prob,
            ngen=self.generations,
            verbose=False,
        )

        fronts = emo.sortNondominated(pop, len(pop))
        for rank, front in enumerate(fronts):
            emo.assignCrowdingDist(front)
            for ind in front:
                ind.rank = rank

        result: List[Individual] = []
        for deap_ind in pop:
            values = {n: v for n, v in zip(self.names, deap_ind)}
            result.append(
                Individual(
                    values=values,
                    objectives=list(deap_ind.fitness.values),
                    rank=getattr(deap_ind, "rank", None),
                    crowding_distance=getattr(deap_ind, "crowding_dist", 0.0),
                )
            )
        return result
