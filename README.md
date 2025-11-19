# A Software Framework for Optimization and Verification of Real-Time Models in Cooperative Autonomous Driving

This framework is for modelling autonomous driving scenarios with a DSL, checking their schedulability with UPPAAL, optimising their timing attributes with an optimisation algorithm, and exporting the final scenario to CARLA for closed-loop simulation. 

## Features
- **DSL** – The `DSL/Robotics.g4` grammar, parser, and visitor build strongly-typed models (`metamodel.Model`) capturing components, vehicles, connections, CPU policies, and optimisation goals.
- **Formal verification** – `Backend/UPPAAL` translates DSL models into UPPAAL templates and evaluates user-specified constraints before a simulation is launched.
- **Multi-objective optimisation** – `Backend/Optim` hosts NSGA-II, SMS-EMOA, MOEA/D, ε-constraint, and qEHVI optimisers that tune timing variables, priorities, and CPU parameters.
- **CARLA integration** – The `CARLA` package converts optimised DSL models into executable CARLA scenarios with reusable behaviours, schedulers, and connection logic.
- **Evaluation scripts** – Utilities under `Evaluation/` streamline dataset creation, algorithm sweeps, Pareto-front visualisation, and CARLA log aggregation.

## Repository layout
```
.
├── Backend/              
│   ├── Optim/            # Optimisation entry points and multi-objective solvers
│   └── UPPAAL/           # UPPAAL verifier wrappers and XML generation helpers
├── CARLA/                # Scenario executor, behaviour registry, and schedulers
├── DSL/                  # DSL grammar, parser, metamodel, and AST visitor
├── Data/                 # Example inputs (DSL & CARLA) and optimisation/eval outputs
├── Evaluation/           # Batch evaluation scripts, converters, and plotting helpers
└── requirements.txt      # Python dependencies for the complete toolchain
```

## Getting started
1. **Prerequisites**
   - Python 3.10 or newer.
   - A CARLA simulator installation (for scenario execution), download this release: https://github.com/carla-simulator/carla/releases/tag/0.10.0.
   - UPPAAL installed and reachable on your PATH for model checking.
2. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Prepare the data folders** – Populate `Data/DSLInput/` with your `.adsl` files, otherwise use the preexisting .adsl files; `Data/OptimOutput/`, `Data/EvalOutput/`, and `Data/CARLAInput/` are used by the scripts described below.

## Typical workflow
1. **Author or import a scenario** in the DSL (see the examples under `Data/DSLInput/`).
2. **Validate the model** with UPPAAL before optimisation:
   ```bash
   python -m Backend.UPPAAL.verify Data/DSLInput/Overtaking_Hard.adsl
   ```
   This parses the DSL, instantiates `UppaalVerifier`, and prints the result for every constraint listed inside the `OPTIMISATION { CONSTRAINTS { ... } }` block.
3. **Optimise timing parameters** using the evolutionary back-end.  `Backend/Optim/optimise.py` exposes a `main()` helper that loads a `.adsl` file, runs the requested algorithm, and returns the optimised model together with the best individual.
   ```python
   from Backend.Optim.optimise import main

   optimised_model, best = main(
       "Data/DSLInput/Overtaking_Hard.adsl",
       generations=200,
       algorithm="nsga2",
   )
   print(best.values, best.objectives)
   ```
   Algorithms available through the `algorithm` argument include `nsga2`, `smsemoa`, `moead`, `eps-constraint`, and `qehvi`.  Each optimisation run uses `UppaalVerifier` internally to discard constraint-violating individuals and logs hypervolume statistics under `Data/OptimOutput/`.
4. **Convert DSL to CARLA JSON** once you are satisfied with the model:
   ```bash
   python -m Evaluation.dsl_to_json Data/DSLInput/Overtaking_Hard.adsl \
       -o Data/CARLAInput/Overtaking_Hard.json
   ```
   The converter uses the metamodel visitor to translate vehicles, components, and connections into the CARLA scenario schema while filling in defaults (map, blueprint, spawn points, behaviours, etc.).
5. **Run the scenario in CARLA** via the packaged executor:
   ```bash
   python -m CARLA.run_scenario Data/CARLAInput/Overtaking_Hard.json \
       --host localhost --port 2000 --duration 120
   ```
   `CarlaScenarioExecutor` takes care of connecting to the simulator, scheduling behaviours from `CARLA/behaviour/`, and running until the requested duration or step count is reached.
6. **Evaluate experiments** using the utilities under `Evaluation/`:
   - `evaluate_moea.py` runs the comparative experimental study and stores them in `Data/EvalOutput/`.
   - `evaluate_carla.py` replays CARLA experiments, collecting timing traces.
   - `plot_hv_convergence.py` visualises hypervolume convergence from previous optimisation runs.

## Results
### Scenario Intersection_Easy:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |       0.103   |   0.009871 | [0.09259, 0.1055]  |        0.006191 |     0.01078  | [0.004184, 0.01521]  |                34.81 |            1.31   |              4860 |                289.3   |             4667 |                    281.8   |                 1490 |                       97.47 |               1696   |                   3164 |                     0.349   |
| sms-emoa       |       0.1032  |   0.00151  | [0.1019, 0.1038]   |        0.005849 |     0.001568 | [0.005075, 0.007096] |                36.87 |            1.629  |              4860 |                286.5   |             4663 |                    279.7   |                 1529 |                       97.66 |               1708   |                   3152 |                     0.3515  |
| qehvi          |       0.1086  |   0        | [0.1086, 0.1086]   |        0        |     0        | [0, 0]               |                12.73 |            0.6051 |                40 |                  3.114 |               47 |                      3.081 |                   47 |                       98.98 |                 41   |                      6 |                     0.8727  |
| moead          |       0.1086  |   0        | [0.1086, 0.1086]   |        0        |     0        | [0, 0]               |                34.09 |            5.328  |              4560 |                276     |             3758 |                    269.4   |                 1384 |                       97.49 |               2242   |                   2298 |                     0.4825  |
| eps-constraint |       0.06233 |   0.02765  | [0.04094, 0.08141] |        0.393    |     0.3991   | [0.153, 0.7136]      |                13.56 |            5.194  |              1981 |                 13.51  |             1981 |                     13.32  |                  199 |                       98.62 |                182.5 |                   1806 |                     0.09091 |

### Scenario Intersection_Hard:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |        0.3674 |  0.01018   | [0.3577, 0.3741]   |       0.008421  |    0.002767  | [0.006753, 0.01005]  |                39.52 |            2.094  |              4860 |                325.5   |             4666 |                    315.4   |                 1536 |                       97.15 |                 1737 |                   3124 |                     0.3573  |
| sms-emoa       |        0.3788 |  0.0349    | [0.3416, 0.3895]   |       0.004865  |    0.009147  | [0.001813, 0.01272]  |                38.06 |            0.9901 |              4860 |                309.2   |             4654 |                    301.5   |                 1552 |                       97.43 |                 1764 |                   3097 |                     0.3629  |
| qehvi          |        0.3967 |  0         | [0.3847, 0.3967]   |       0         |    0         | [0, 0.003061]        |                15.27 |            1.145  |                44 |                  3.243 |               46 |                      3.208 |                   46 |                       98.91 |                   45 |                      1 |                     0.9783  |
| moead          |        0.3966 |  6.903e-05 | [0.3966, 0.3967]   |       4.954e-06 |    1.759e-05 | [0, 2.229e-05]       |                33.31 |            1.666  |              4860 |                289.3   |             3939 |                    283     |                 1406 |                       97.65 |                 2339 |                   2489 |                     0.4816  |
| eps-constraint |        0.2955 |  0.1207    | [0.173, 0.3162]    |       0.3064    |    0.3731    | [0.1944, 0.6771]     |                15.19 |            6.379  |              2201 |                 15.13  |             2201 |                     14.9   |                  221 |                       98.46 |                  216 |                   1985 |                     0.09812 |

### Scenario LaneMerge_Easy:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |        0.1686 |  0.02363   | [0.1431, 0.1855]   |       0.01404   |    0.008154  | [0.008263, 0.02277]  |                35.31 |             1.565 |              4860 |                301.9   |             4675 |                    294.5   |                 1530 |                       97.59 |               1670   |                   3190 |                     0.3437  |
| sms-emoa       |        0.1713 |  0.0525    | [0.1343, 0.1942]   |       0.013     |    0.0182    | [0.004883, 0.02565]  |                35.5  |             1.112 |              4860 |                296     |             4668 |                    289.5   |                 1508 |                       97.65 |               1646   |                   3216 |                     0.3385  |
| qehvi          |        0.2083 |  0.05394   | [0.1357, 0.2083]   |       0         |    0.05173   | [0, 0.1206]          |                14.05 |             1.809 |                36 |                  4.034 |               66 |                      3.995 |                   58 |                       99.04 |                 37   |                     34 |                     0.5189  |
| moead          |        0.2083 |  0.0001417 | [0.2081, 0.2083]   |       1.203e-06 |    4.908e-05 | [0, 9.578e-05]       |                31.61 |             1.194 |              4860 |                278     |             3952 |                    272.3   |                 1354 |                       97.89 |               2208   |                   2652 |                     0.4543  |
| eps-constraint |        0.1838 |  0.09613   | [0.08698, 0.1922]  |       0.08187   |    0.06685   | [0.03711, 0.1867]    |                15.65 |             3.001 |              2226 |                 15.59  |             2226 |                     15.38  |                  223 |                       98.65 |                173.5 |                   2052 |                     0.07809 |

### Scenario LaneMerge_Hard:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |        0.3834 |  0.05909   | [0.3213, 0.3946]   |       0.01748   |    0.04017   | [0.007525, 0.0538]   |                41.88 |             1.378 |              4860 |                351.8   |             4680 |                    343.4   |                 1556 |                       97.53 |               1711   |                 3150   |                     0.352   |
| sms-emoa       |        0.3654 |  0.04902   | [0.3247, 0.3843]   |       0.01757   |    0.04652   | [0.0107, 0.06132]    |                46.44 |             7.834 |              4860 |                384.7   |             4668 |                    374.5   |                 1578 |                       97.57 |               1714   |                 3147   |                     0.3526  |
| qehvi          |        0.3724 |  0.09452   | [0.2081, 0.4107]   |       0.01807   |    0.122     | [0, 0.1766]          |                18.52 |             1.974 |                40 |                  5.762 |               78 |                      5.708 |                   68 |                       99.07 |                 40.5 |                   37.5 |                     0.5098  |
| moead          |        0.4105 |  0.0003816 | [0.4102, 0.4107]   |       6.875e-05 |    0.0001459 | [0, 0.0001691]       |                41.33 |             3.482 |              4860 |                341.6   |             4006 |                    334.6   |                 1425 |                       97.86 |               2242   |                 2619   |                     0.4612  |
| eps-constraint |        0.1781 |  0.1555    | [0.1274, 0.2987]   |       0.3829    |    0.5781    | [0.1243, 0.7623]     |                16.56 |             2.675 |              2031 |                 16.5   |             2031 |                     16.29  |                  204 |                       98.75 |                152   |                 1885   |                     0.07237 |

### Scenario ObstacleAvoidance_Easy:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |       0.08872 |   0.008221 | [0.08403, 0.09383] |        0.007643 |     0.009963 | [0.001422, 0.01339]  |                44.38 |            2.96   |              4860 |                345.7   |             4657 |                    339.2   |                 1550 |                       97.79 |                 1722 |                   3140 |                     0.3541  |
| sms-emoa       |       0.09154 |   0.003153 | [0.0877, 0.09312]  |        0.004176 |     0.008317 | [0.002423, 0.01248]  |                45.41 |            1.111  |              4860 |                362.5   |             4665 |                    355.1   |                 1548 |                       98.02 |                 1705 |                   3156 |                     0.3508  |
| qehvi          |       0.095   |   0        | [0.095, 0.095]     |        0        |     0        | [0, 0]               |                13.35 |            0.9608 |                38 |                  3.424 |               54 |                      3.388 |                   52 |                       98.97 |                   39 |                     15 |                     0.7222  |
| moead          |       0.095   |   0        | [0.09497, 0.095]   |        0        |     0        | [0, 3.065e-05]       |                32.22 |            3.56   |              4800 |                273.9   |             3868 |                    267.3   |                 1363 |                       97.6  |                 2214 |                   2505 |                     0.4684  |
| eps-constraint |       0.05672 |   0.0437   | [0.02692, 0.07755] |        0.208    |     0.4417   | [0.08306, 0.7104]    |                13.79 |            7.874  |              2041 |                 13.74  |             2041 |                     13.56  |                  205 |                       98.63 |                  174 |                   1868 |                     0.08854 |

### Scenario ObstacleAvoidance_Hard:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |        0.2064 |   0.03496  | [0.1638, 0.2158]   |        0.002779 |    0.007073  | [0.0008976, 0.01142] |                36.44 |             1.591 |              4860 |                306.8   |             4673 |                    299.1   |                 1534 |                       97.47 |                 1679 |                 3182   |                     0.3454  |
| sms-emoa       |        0.2084 |   0.01564  | [0.1892, 0.2163]   |        0.002365 |    0.002957  | [0.00105, 0.005976]  |                36.15 |             2.243 |              4860 |                309.5   |             4670 |                    300.2   |                 1530 |                       97.17 |                 1719 |                 3142   |                     0.3536  |
| qehvi          |        0.22   |   0        | [0.22, 0.22]       |        0        |    0         | [0, 0]               |                14.82 |             1.488 |                42 |                  3.662 |               52 |                      3.623 |                   52 |                       98.92 |                   43 |                   11.5 |                     0.785   |
| moead          |        0.22   |   0.000175 | [0.2197, 0.22]     |        0        |    3.557e-05 | [0, 6.132e-05]       |                32.23 |             1.164 |              4860 |                276.8   |             3969 |                    270.6   |                 1354 |                       97.67 |                 2216 |                 2633   |                     0.457   |
| eps-constraint |        0.1064 |   0.117    | [0.05149, 0.1729]  |        0.03365  |    0.01701   | [0.01811, 0.07021]   |                17.46 |             5.51  |              2506 |                 17.38  |             2506 |                     17.13  |                  251 |                       98.51 |                  214 |                 2292   |                     0.08789 |

### Scenario Overtaking_Easy:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |       0.104   |   0.01121  | [0.09691, 0.1097]  |        0.00711  |     0.008588 | [0.002762, 0.01266]  |                33.29 |            1.93   |              4860 |                288.7   |             4658 |                    281.3   |                 1498 |                       97.45 |               1695   |                   3166 |                     0.3487  |
| sms-emoa       |       0.1083  |   0.003474 | [0.1026, 0.111]    |        0.003816 |     0.002776 | [0.001835, 0.008214] |                34.07 |            0.6074 |              4860 |                294.8   |             4670 |                    287.2   |                 1536 |                       97.42 |               1707   |                   3154 |                     0.3512  |
| qehvi          |       0.1133  |   0        | [0.1133, 0.1133]   |        0        |     0        | [0, 0]               |                12.68 |            1.108  |                38 |                  3.262 |               51 |                      3.229 |                   48 |                       98.98 |                 39.5 |                     12 |                     0.767   |
| moead          |       0.1133  |   0        | [0.1133, 0.1133]   |        0        |     0        | [0, 0]               |                29.87 |            3.222  |              4860 |                271.7   |             3942 |                    265.7   |                 1375 |                       97.45 |               2232   |                   2504 |                     0.4783  |
| eps-constraint |       0.07143 |   0.04138  | [0.04836, 0.0932]  |        0.2408   |     0.5017   | [0.1212, 0.7535]     |                13.66 |            4.043  |              1981 |                 13.61  |             1981 |                     13.43  |                  199 |                       98.65 |                177   |                   1814 |                     0.08914 |

### Scenario Overtaking_Hard:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI    |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:----------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |        0.3073 |    0.08068 | [0.221, 0.3515]    |       0.02161   |      0.0155  | [0.01383, 0.03707]    |                39.27 |            1.997  |              4860 |                333.2   |             4668 |                    327.2   |                 1468 |                       98.07 |               1560   |                   3301 |                     0.3209  |
| sms-emoa       |        0.3102 |    0.1055  | [0.2108, 0.3528]   |       0.02429   |      0.01879 | [0.01375, 0.03887]    |                40.55 |            0.8104 |              4860 |                331.2   |             4673 |                    324.7   |                 1468 |                       98.14 |               1552   |                   3308 |                     0.3194  |
| qehvi          |        0.3414 |    0.07163 | [0.2455, 0.3785]   |       0.04934   |      0.174   | [0.0164, 0.2199]      |                18.33 |            3.496  |                32 |                  8.993 |             1052 |                      8.902 |                  112 |                       99.01 |                 31.5 |                   1020 |                     0.02995 |
| moead          |        0.429  |    0.01613 | [0.4107, 0.43]     |       0.0001821 |      0.00284 | [3.521e-06, 0.003393] |                36.72 |            0.9949 |              4860 |                320.9   |             3972 |                    313.4   |                 1345 |                       97.8  |               2164   |                   2696 |                     0.4453  |
| eps-constraint |        0.3539 |    0.05211 | [0.2927, 0.3806]   |       0.191     |      0.1437  | [0.09096, 0.2641]     |                20.26 |            6.066  |              2506 |                 20.19  |             2506 |                     19.97  |                  251 |                       98.94 |                131   |                   2366 |                     0.05318 |

### Scenario Platooning_Easy:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI   |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:---------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |       0.04045 |  0.007393  | [0.03529, 0.04429] |       0.01557   |    0.01236   | [0.007091, 0.02184]  |                34.63 |            1.356  |              4860 |                303.4   |             4664 |                    294.6   |                 1576 |                       97.18 |                 1779 |                   3082 |                      0.366  |
| sms-emoa       |       0.03664 |  0.0123    | [0.02579, 0.04114] |       0.02142   |    0.02061   | [0.01335, 0.03781]   |                34.34 |            1.607  |              4860 |                299.6   |             4670 |                    291.3   |                 1550 |                       97.36 |                 1740 |                   3121 |                      0.358  |
| qehvi          |       0.04822 |  0.02857   | [0.01232, 0.04833] |       0.0001955 |    0.06401   | [0, 0.07652]         |                15.4  |            3.008  |                42 |                  2.892 |               43 |                      2.862 |                   43 |                       98.93 |                   43 |                      0 |                      1      |
| moead          |       0.04833 |  1.382e-05 | [0.04831, 0.04833] |       8.139e-06 |    2.314e-05 | [0, 3.907e-05]       |                30.12 |            0.9778 |              4860 |                273.3   |             3952 |                    266.6   |                 1382 |                       97.63 |                 2273 |                   2588 |                      0.4676 |
| eps-constraint |       0.03085 |  0.007272  | [0.0286, 0.03616]  |       0.4271    |    0.1925    | [0.2811, 0.4976]     |                15.11 |            5.117  |              2226 |                 15.05  |             2226 |                     14.84  |                  223 |                       98.57 |                  223 |                   2003 |                      0.1002 |

### Scenario Platooning_Hard:
| Algorithm      |   HV (median) |   HV (IQR) | HV median 95% CI   |   IGD+ (median) |   IGD+ (IQR) | IGD+ median 95% CI     |   Runtime (median s) |   Runtime (IQR s) |   Evaluations/run |   Eval time (median s) |   Eval calls/run |   Verifyta time (median s) |   Verifyta calls/run |   Verifyta share (median %) |   Feasible calls/run |   Infeasible calls/run |   Feasibility rate (median) |
|:---------------|--------------:|-----------:|:-------------------|----------------:|-------------:|:-----------------------|---------------------:|------------------:|------------------:|-----------------------:|-----------------:|---------------------------:|---------------------:|----------------------------:|---------------------:|-----------------------:|----------------------------:|
| nsga2          |       0.05827 |  0.01138   | [0.04973, 0.06737] |        0.03148  |    0.01658   | [0.02281, 0.04433]     |                39.59 |             3.067 |              4860 |                351.5   |             4671 |                    339.8   |                 1660 |                       96.83 |                 1853 |                   3008 |                      0.3812 |
| sms-emoa       |       0.06415 |  0.01984   | [0.05372, 0.07461] |        0.02636  |    0.02145   | [0.01485, 0.03803]     |                37.68 |             1.009 |              4860 |                331.1   |             4669 |                    322.2   |                 1574 |                       97.17 |                 1770 |                   3090 |                      0.3642 |
| qehvi          |       0.06351 |  0.03964   | [0.0304, 0.07911]  |        0.04708  |    0.05365   | [0.02301, 0.1027]      |                19.43 |             1.223 |                50 |                  3.688 |               51 |                      3.645 |                   51 |                       98.82 |                   51 |                      0 |                      1      |
| moead          |       0.08944 |  0.0007142 | [0.089, 0.08981]   |        0.000551 |    0.0007307 | [0.0002188, 0.0009821] |                44.74 |             3.2   |              4860 |                359.8   |             3972 |                    350.8   |                 1498 |                       97.6  |                 2375 |                   2486 |                      0.4886 |
| eps-constraint |       0.05865 |  0.02587   | [0.0388, 0.06958]  |        0.4544   |    0.3778    | [0.2379, 0.7425]       |                16.03 |             8.669 |              2216 |                 15.96  |             2216 |                     15.7   |                  222 |                       98.41 |                  222 |                   1994 |                      0.1002 |

