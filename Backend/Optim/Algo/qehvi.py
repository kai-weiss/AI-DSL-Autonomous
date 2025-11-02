from __future__ import annotations

import random
from dataclasses import dataclass
from multiprocessing.pool import ThreadPool
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np
import torch
from botorch import settings
from botorch.acquisition.multi_objective import qLogExpectedHypervolumeImprovement
from botorch.exceptions.errors import BotorchError
from botorch.fit import fit_gpytorch_mll
from botorch.models import ModelListGP, SingleTaskGP
from botorch.models.transforms.outcome import Standardize
from botorch.optim import optimize_acqf
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.utils.multi_objective.box_decompositions.non_dominated import NondominatedPartitioning
from botorch.utils.multi_objective.pareto import is_non_dominated
from botorch.utils.transforms import normalize, unnormalize
from gpytorch.mlls import ExactMarginalLogLikelihood

from .common import Individual, PlateauDetector

__all__ = ["QEHVIOptimizer", "QEHVI"]


def _nondominated(points: Sequence[Sequence[float]]) -> List[List[float]]:
    """Return the Pareto front for a list of minimisation points."""

    pts = np.asarray(points, dtype=float)
    if pts.size == 0:
        return []

    keep = np.ones(len(pts), dtype=bool)
    for i, p in enumerate(pts):
        if not keep[i]:
            continue
        dominated = np.all(pts <= p, axis=1) & np.any(pts < p, axis=1)
        keep &= ~dominated
        keep[i] = True
    return pts[keep].tolist()


@dataclass
class _EvaluationRecord:
    values: Dict[str, float]
    objectives: List[float]


class QEHVIOptimizer:
    """Bayesian optimisation with qEHVI for bi-objective problems."""

    def __init__(
            self,
            variables: Dict[str, Tuple[float, float]],
            evaluate: Callable[[Dict[str, float]], List[float]],
            *,
            generations: int = 30,
            pop_size: int = 4,
            batch_size: int | None = None,
            initial_points: int | None = None,
            seed: int | None = None,
            workers: int | None = None,
            ref_point_slack: float = 1.0,
            raw_samples: int = 128,
            num_restarts: int = 5,
            batch_limit: int = 5,
            qmc_samples: int = 64,
            max_acqf_iterations: int = 100,
            refit_interval: int = 5,
    ) -> None:
        if not variables:
            raise ValueError("No optimisation variables provided")

        self.variables = dict(variables)
        self.evaluate = evaluate
        self.generations = int(generations)
        self.batch_size = int(batch_size or pop_size)
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.initial_points = (
            int(initial_points)
            if initial_points is not None
            else max(2 * len(self.variables), self.batch_size)
        )
        self.seed = seed
        self.workers = workers
        self.ref_point_slack = float(ref_point_slack)
        self.raw_samples = int(raw_samples)
        self.num_restarts = int(num_restarts)
        self.batch_limit = int(batch_limit)
        self.qmc_samples = int(qmc_samples)
        self.max_acqf_iterations = int(max_acqf_iterations)
        self.refit_interval = int(refit_interval)

        if self.raw_samples <= 0:
            raise ValueError("raw_samples must be positive")
        if self.num_restarts <= 0:
            raise ValueError("num_restarts must be positive")
        if self.batch_limit <= 0:
            raise ValueError("batch_limit must be positive")
        if self.qmc_samples <= 0:
            raise ValueError("qmc_samples must be positive")
        if self.max_acqf_iterations <= 0:
            raise ValueError("max_acqf_iterations must be positive")
        if self.refit_interval <= 0:
            raise ValueError("refit_interval must be positive")

        self.names = list(self.variables.keys())
        self.bounds = np.asarray(list(self.variables.values()), dtype=float)
        self._dtype = torch.double
        self._device = torch.device("cpu")

        sample = {n: (lo + hi) / 2.0 for n, (lo, hi) in self.variables.items()}
        objectives = list(self.evaluate(sample))
        if len(objectives) != 2:
            raise ValueError(
                "qEHVI requires exactly two objectives; "
                f"received {len(objectives)}"
            )

        self.num_objectives = len(objectives)

        lows = torch.tensor(self.bounds[:, 0], dtype=self._dtype, device=self._device)
        highs = torch.tensor(self.bounds[:, 1], dtype=self._dtype, device=self._device)
        self._raw_bounds = torch.stack([lows, highs])
        self._unit_bounds = torch.stack(
            [torch.zeros_like(lows), torch.ones_like(highs)]
        )

    # ------------------------------------------------------------------
    def run(
            self,
            *,
            log_history: bool = False,
            plateau_detector: PlateauDetector | None = None,
    ) -> (
            List[Individual]
            | Tuple[List[Individual], List[List[List[float]]], int, bool]
    ):
        rng = torch.Generator(device=self._device)
        seed = self.seed if self.seed is not None else random.randrange(10 ** 9)
        rng.manual_seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        pool: ThreadPool | None = None
        if self.workers is not None and self.workers <= 1:
            map_func = map
        elif self.workers is None:
            pool = ThreadPool()
            map_func = pool.map
        else:
            pool = ThreadPool(processes=self.workers)
            map_func = pool.map

        records: List[_EvaluationRecord] = []
        train_x_list: List[torch.Tensor] = []
        train_obj_list: List[torch.Tensor] = []

        def _eval_point(values: Dict[str, float]) -> List[float]:
            result = self.evaluate(values)
            return [float(v) for v in result]

        try:
            # Initial design via random sampling.
            while len(train_x_list) < self.initial_points:
                raw = self._sample_uniform(rng)
                values = {name: float(val) for name, val in zip(self.names, raw)}
                objs = _eval_point(values)
                records.append(_EvaluationRecord(values=values, objectives=objs))
                objs_tensor = torch.tensor(
                    objs, dtype=self._dtype, device=self._device
                )
                if (objs_tensor >= 1e8).any():
                    continue
                train_x_list.append(
                    normalize(
                        torch.tensor(raw, dtype=self._dtype, device=self._device)
                        .unsqueeze(0)
                        .contiguous(),
                        self._raw_bounds,
                    )
                )
                train_obj_list.append(
                    -objs_tensor.unsqueeze(0).contiguous()
                )

            train_x = torch.cat(train_x_list, dim=0)
            train_obj = torch.cat(train_obj_list, dim=0)

            history: List[List[List[float]]] = []
            stopped = False

            model = self._build_model(train_x, train_obj)
            sampler = SobolQMCNormalSampler(
                sample_shape=torch.Size((self.qmc_samples,))
            )
            since_refit = 0

            for gen in range(1, self.generations + 1):
                ref_point = self._reference_point(train_obj)
                partitioning = NondominatedPartitioning(
                    ref_point=ref_point, Y=train_obj
                )
                acqf = qLogExpectedHypervolumeImprovement(
                    model=model,
                    ref_point=ref_point.tolist(),
                    partitioning=partitioning,
                    sampler=sampler,
                )

                try:
                    candidates, _ = optimize_acqf(
                        acq_function=acqf,
                        bounds=self._unit_bounds,
                        q=self.batch_size,
                        num_restarts=self.num_restarts,
                        raw_samples=self.raw_samples,
                        options={
                            "batch_limit": self.batch_limit,
                            "maxiter": self.max_acqf_iterations,
                        },
                        sequential=False,
                    )
                    candidates = candidates.detach()
                except (RuntimeError, ValueError, BotorchError):
                    candidates = torch.rand(
                        self.batch_size,
                        len(self.names),
                        dtype=self._dtype,
                        device=self._device,
                        generator=rng,
                    )

                new_points = unnormalize(candidates, self._raw_bounds)
                value_dicts = [
                    {
                        name: float(point[idx])
                        for idx, name in enumerate(self.names)
                    }
                    for point in new_points.cpu().numpy()
                ]

                if pool is not None:
                    evaluated = list(map_func(_eval_point, value_dicts))
                else:
                    evaluated = [
                        [float(val) for val in self.evaluate(v)]
                        for v in value_dicts
                    ]

                new_x_norm = candidates
                evaluated_tensor = torch.tensor(
                    evaluated, dtype=self._dtype, device=self._device
                )
                valid_mask = ~(evaluated_tensor >= 1e8).any(dim=1)
                filtered_x = new_x_norm[valid_mask]
                filtered_obj = -evaluated_tensor[valid_mask]

                if filtered_x.numel():
                    train_x = torch.cat([train_x, filtered_x], dim=0)
                    train_obj = torch.cat([train_obj, filtered_obj], dim=0)

                    since_refit += int(filtered_x.shape[0])
                    if since_refit >= self.refit_interval:
                        model = self._build_model(train_x, train_obj)
                        since_refit = 0
                    else:
                        model = self._condition_model(model, filtered_x, filtered_obj)

                for values, objs in zip(value_dicts, evaluated):
                    records.append(
                        _EvaluationRecord(values=dict(values), objectives=list(objs))
                    )

                current_front = _nondominated(
                    [rec.objectives for rec in records]
                )
                if log_history:
                    history.append(current_front)

                if plateau_detector and plateau_detector.update(current_front, gen):
                    stopped = True
                    break

            individuals = self._build_population(records)
            evaluations = len(records)

            if log_history:
                return individuals, history, evaluations, stopped
            return individuals
        finally:
            if pool is not None:
                pool.close()
                pool.join()

    # ------------------------------------------------------------------
    def _sample_uniform(self, rng: torch.Generator) -> np.ndarray:
        lows = self.bounds[:, 0]
        highs = self.bounds[:, 1]
        sample = torch.rand(
            len(self.names), dtype=self._dtype, device=self._device, generator=rng
        )
        sample = sample.cpu().numpy()
        return lows + sample * (highs - lows)

    def _standardize_objectives(self, objectives: torch.Tensor) -> torch.Tensor:
        """Return a column-wise standardized copy of the objective tensor."""
        if objectives.numel() == 0:
            return objectives.clone()

        mean = objectives.mean(dim=0, keepdim=True)
        std = objectives.std(dim=0, unbiased=False, keepdim=True)
        std = torch.where(std > 1e-8, std, torch.ones_like(std))
        return (objectives - mean) / std

    def _build_model(
            self, train_x: torch.Tensor, train_obj: torch.Tensor
    ) -> ModelListGP:
        models = []

        def _make_single_task_gp(
                train_inputs: torch.Tensor, train_features: torch.Tensor
        ) -> SingleTaskGP:
            """Instantiate a GP without triggering scaling warnings.

            The design variables are already normalised to the unit cube, so
            BoTorch's default input validation would emit InputDataWarning even
            though the data matches the expected scale. Temporarily disabling the
            validation suppresses the warning without changing the underlying
            behaviour of the model fit.
            """

            with settings.validate_input_scaling(False):
                return SingleTaskGP(
                    train_X=train_features,
                    train_Y=train_inputs,
                    outcome_transform=Standardize(1),
                )

        for obj_idx in range(self.num_objectives):
            gp = _make_single_task_gp(
                train_obj[:, obj_idx: obj_idx + 1], train_x
            )
            mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
            try:
                fit_gpytorch_mll(mll)
            except RuntimeError:
                jitter = 1e-6 * torch.randn_like(train_x)
                gp = _make_single_task_gp(
                    train_obj[:, obj_idx: obj_idx + 1], train_x + jitter
                )
                mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
                fit_gpytorch_mll(mll)
            models.append(gp)

        model = ModelListGP(*models)
        return model

    def _reference_point(self, train_obj: torch.Tensor) -> torch.Tensor:
        worst = train_obj.min(dim=0).values
        slack = torch.full_like(worst, self.ref_point_slack)
        return worst - slack

    def _condition_model(
            self,
            model: ModelListGP,
            new_x: torch.Tensor,
            new_obj: torch.Tensor,
    ) -> ModelListGP:
        conditioned = []
        for idx, gp in enumerate(model.models):
            conditioned.append(
                gp.condition_on_observations(new_x, new_obj[:, idx: idx + 1])
            )
        return ModelListGP(*conditioned)

    def _build_population(self, records: Iterable[_EvaluationRecord]) -> List[Individual]:
        objs_tensor = torch.tensor(
            [[-v for v in rec.objectives] for rec in records], dtype=self._dtype
        )
        mask = is_non_dominated(objs_tensor)
        individuals: List[Individual] = []
        for rec, keep in zip(records, mask.tolist()):
            if not keep:
                continue
            individuals.append(
                Individual(
                    values=dict(rec.values),
                    objectives=list(rec.objectives),
                    rank=0,
                    crowding_distance=0.0,
                )
            )
        individuals.sort(key=lambda ind: ind.objectives)
        return individuals


# Backwards-compatible alias with the shorter name.
QEHVI = QEHVIOptimizer
