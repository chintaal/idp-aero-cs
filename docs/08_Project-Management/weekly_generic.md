# Weekly progress (generic, technical)

Three to four points per week, aligned with the Gantt. No measured numbers here—those go in the lab diary.

---

## Week 1 (12 March 2026 – 19 March 2026)

- Surveyed air-brake usage, **apogee** control options, and **3-DoF** / **coast** dynamics so the estimator is grounded in **flight mechanics**, not a context-free ML exercise.
- Committed to **supervised regression** plus a **PINN** branch, with explicit milestones across **aero**, **inference** code, and **embedded** follow-on.
- Short-listed **architectures** and **loss** terms (MSE, optional physics **residuals** on state-like channels) against **v1** data volume and **CPU/GPU** budget.
- Assembled the **v1 dataset** with train/val policy and QC for gaps and outliers; bootstrapped PINN training skeleton and logged physics holes (e.g. post-burn **coast**) for the aero loop to target next.

## Week 2 (20 March 2026 – 27 March 2026)

- Froze preliminary **air-brake** layout and span so **Cd** targets and structural envelope stay comparable across **CFD** cases.
- Built an **OpenRocket** `.ork` with a **COTS motor** and a transonic **Mach** band tied to the CFD sweep; exported time histories for labels and sanity checks.
- Brought the **CFD** pre/post path online: mesh convention, turbulence model rationale, and **Cd** from force integration into deployment-angle lookups.
- Stood up **FastAPI** with pluggable checkpoints; began **regression vs PINN** on a fixed split to see which tracks **OpenRocket** better in ascent vs **coast**.

## Week 3 (28 March 2026 – 3 April 2026)

- Ran at least two **air-brake** CFD cases at a common **Mach**; compared stowed vs deployed **Cd** and iterated mesh where **y+** or separation looked weak.
- Wired the **aerospace domain layer** into inference: SI units, bounds, and thrust / atmosphere / brake schedule as explicit assumptions with validation errors that fail fast.
- Hardened lab operations: **YAML/CLI** config, idempotent restarts, **structured logging** with request correlation for traceability of each PINN/regression run.
- Pushed the team review on **mesh** convergence: documented residual trends and which **drag** values are **release candidates** for the next OpenRocket and dataset refresh.

## Week 4 (4 April 2026 – 10 April 2026)

- Drove **v1 apogee** training to convergence; binned residuals by **Mach** and flight phase and compared to **OpenRocket** on rows sharing the same **Cd** and mass model.
- Tightened **Pydantic** on public JSON so spreadsheets and code cannot drift silently on names, keys, or units.
- Chased systematic bias in **coast** and higher-**Mach** bins; raised **aero** action items (extra CFD or thrust-tail data) where PINN residuals were largest.
- **ESP32** bring-up: clock, UART console, DMM currents for idle vs **WiFi** TX—anchors the power and I/O narrative for documentation.

## Week 5 (11 April 2026 – 17 April 2026)

- Closed the formal **regression vs PINN** comparison on a held-out set with linked **OpenRocket** / CFD provenance; documented where each wins (often **coast** for PINN when tuned).
- Load-tested the serving path on CPU; recorded **p50** / **p95** latency and queued tensor layout or batching fixes at the bottlenecks.
- Built a mismatch table: tight agreement when thrust and **ISA** atmosphere line up; larger gaps when **OpenRocket** used custom wind or humidity not yet in the feature vector—feeds the next feature pull.
- Exercised ESP32 **WiFi** uplink to the dev API; clean runs on LAN and a frozen payload schema for future **HIL**-style demos.

## Week 6 (18 April 2026 – 24 April 2026)

- Replayed **Cd**-anchored cases on two machines with identical seed and weights; verified **reproducibility** within agreed tolerance and filed **SHA** hashes with the evidence bundle.
- Sensitivity: small **%** bump to stowed **Cd** and read-out **apogee** delta for aero (couples drag uncertainty to mission output).
- Inlined version tags in API responses (OR file id, CFD case id, checkpoint id) so every figure is one-hop traceable.
- Bench-tested one 12-bit **ADC** path: sampling rate, noise vs full scale, and go/no-go for upcoming brake- or state-feedback trials.

## Week 7 (25 April 2026 – 1 May 2026)

- Completed a detailed **PINN vs conventional model** benchmark design across six classes: (1) polynomial / linear regression, (2) tree ensembles (**XGBoost/Random Forest**), (3) dense **MLP** regression, (4) sequence models (**LSTM/GRU**) for trajectory chunks, (5) Kalman-style model-based estimators, and (6) lookup/interpolation baselines from **CFD/OpenRocket** tables.
- Compared each class on decision criteria used in this project: **sample efficiency**, **extrapolation to unseen Mach/drag regimes**, **physical consistency** (mass depletion, drag sign, monotonic trends where expected), **noise robustness**, **compute budget** for training/inference, **interpretability**, and readiness for **embedded/real-time** use.
- Observed clear trade-space: tabular ML (especially boosted trees) reached low validation error fastest on in-distribution data, but degraded sharply when queried beyond the training manifold; plain MLP was flexible but required more tuning and still violated physics constraints unless regularized with engineered penalties.
- Sequence models handled temporal smoothness better than static regressors, yet needed longer trajectory windows and were sensitive to misaligned thrust/coast phase labels; this increased data-engineering overhead compared to a PINN that directly penalizes ODE residuals.
- Pure model-based estimators remained most interpretable and stable under sparse data, but were bottlenecked by fidelity of simplified drag/thrust assumptions; PINNs provided a middle ground by absorbing data-driven corrections while preserving dynamics through the residual loss.
- Compiled a comparative matrix for documentation: **best in-distribution fit** (trees/MLP), **best physics consistency under sparse labels** (PINN + model-based), **lowest implementation complexity** (linear/tree baselines), and **best long-term extensibility** for coupled aero-ML loops (PINN path).

## Week 8 (2 May 2026 – 8 May 2026)

- Produced a structured **PINN advantages/disadvantages** review for project decision-making. Core advantages: stronger **data efficiency** in low-label settings, built-in **physical priors** via residual constraints, improved **generalization/extrapolation** near regime boundaries, and easier diagnosis when outputs fail known laws.
- Recorded additional PINN strengths relevant to this stack: supports hybrid supervision (full-state labels when available, sparse scalar labels otherwise), allows incorporation of CFD-informed terms without retraining the entire data pipeline, and improves traceability because each prediction can be decomposed into data-fit and physics-residual contributions.
- Cataloged practical PINN disadvantages from implementation cycles: higher **loss balancing** sensitivity (data term vs residual term), longer and less stable optimization, extra cost for automatic differentiation on stiff regions, and requirement for well-posed equations/boundary conditions that are sometimes uncertain in real flight conditions.
- Highlighted deployment risks versus conventional models: heavier training complexity, harder hyperparameter search, potential false confidence if physics terms are misspecified, and non-trivial portability to constrained microcontrollers if inference graph or feature conditioning grows.
- Benchmarked when to prefer alternatives: use simple regression/trees for quick baselines and explainability, sequence models when rich time history is guaranteed, and model-based filters when telemetry is sparse but equations are trusted; keep PINN as primary path for mixed-data, mixed-fidelity regimes where physics-guided extrapolation is critical.
- Finalized the recommendation logic for future milestones: maintain **baseline conventional models** as guardrails, continue **PINN** as the main research branch, and gate promotions on joint criteria (error, residual consistency, robustness under perturbed drag/thrust inputs, and serving latency).

---

*See also: [`Weekly-Progress-Diary.md`](./Weekly-Progress-Diary.md) (measured), [`Weekly-Report.md`](./Weekly-Report.md) (formal template).*
