# CS Component Technical Report

## Document metadata

- **Project:** Active Airbrake System for Controlled Rocket Apogee
- **Focus of this report:** Computer Science component (software, data, ML, API, evaluation, reproducibility)
- **Audience:** Technical reviewers (CS/AI/software) and interdisciplinary faculty (aerospace, embedded, project board)
- **Version:** 1.0

---

## 1) Executive overview

### 1.1 Technical summary

The CS component implements a full simulation-to-inference pipeline for apogee estimation under active drag control. The system integrates:

- deterministic physics simulation for trajectory generation,
- Monte Carlo dataset synthesis with noise modeling,
- multi-model learning stack (baselines + PINN branch),
- benchmark framework with metric/latency comparisons,
- API serving path with schema-driven contracts,
- reproducibility and traceability practices for engineering review.

The software architecture is intentionally modular to decouple physics, training, benchmarking, and service layers while preserving end-to-end compatibility.

### 1.2 Non-technical summary

This project builds the “brain” and software workflow behind the airbrake idea: it generates realistic flight data, trains prediction models, compares them fairly, and makes predictions available through an engineering API in a way that is testable and traceable.

---

## 2) Scope of the CS component

### 2.1 Technical scope

Included in this report:

- data generation and curation workflow,
- feature and target formulation,
- model-development strategy and PINN integration,
- evaluation/benchmarking methodology,
- API and software engineering design choices,
- quality assurance, reproducibility, and current limitations.

Out of scope:

- detailed mechanical design of airbrakes,
- full CFD mesh methodology details,
- embedded power electronics hardware details (covered in dedicated tracks).

### 2.2 Non-technical summary

This report covers the software and AI side thoroughly, while mechanical and hardware details are only referenced where needed for context.

---

## 3) System architecture (CS view)

### 3.1 Technical architecture

The CS workflow follows this sequence:

1. **Physics simulation layer** produces trajectory states under parameterized rocket/aero conditions.
2. **Dataset layer** converts trajectories into supervised examples for apogee prediction.
3. **Model layer** trains baseline regressors and PINN-based models.
4. **Benchmark layer** compares models on held-out data and computes deployment-relevant metrics.
5. **Service layer** exposes inference capability via FastAPI with validated input contracts.
6. **Traceability layer** records metadata for reproducibility and auditability.

Key software characteristics:

- modular package structure (`physics`, `models`, `training`, `api`),
- scriptable workflows for generation/training/benchmarking,
- CI-friendly evaluation hooks via deterministic splits and explicit artifacts.

### 3.2 Non-technical summary

Think of the CS system as a factory line: simulate flights, prepare training examples, train and compare models, and then serve predictions through a reliable API with records of how each result was produced.

---

## 4) Data pipeline and feature engineering

### 4.1 Technical details

The data pipeline synthesizes supervised data from many simulated flights:

- random sampling of physical parameters (`mass`, `A_ref`, `Cd`, `burn_time`, `impulse`, `launch altitude`),
- simulation under selected deployment levels,
- extraction of coast-phase snapshots (after burnout, before apogee),
- controlled noise injection in sensor-like channels (`h`, `v`, `a`),
- per-flight grouping to prevent data leakage in train/val/test splits.

Representative feature set includes:

- `h`, `v`, `a`,
- `deployment`,
- `rho`,
- `t_since_burnout`,
- `mass_dry`,
- `A_ref`,
- `Cd_total`.

Target:

- `target_apogee` (final achieved apogee).

Data quality design choices:

- coast-phase sampling ensures relevance to active apogee control,
- split-by-flight prevents optimistic bias from near-duplicate snapshots,
- noise-injected training improves robustness against idealized simulation artifacts.

### 4.2 Non-technical summary

The software creates realistic training examples by simulating many flights and taking meaningful “snapshots” during coast phase. It avoids cheating by keeping data from the same flight in only one split and adds measurement noise so models are less fragile.

---

## 5) Model strategy and PINN integration

### 5.1 Technical details

The modeling strategy is deliberately pluralistic:

- **Conventional baselines** (linear/tree/boosting families) for speed, interpretability, and strong tabular baselines.
- **PINN branch** for physics-informed regularization and consistency under low-label/uncertain regimes.

PINN-related design goals:

- incorporate dynamics knowledge (kinematic and force-balance structure),
- decompose losses into data-fit and physics residual components,
- use residual behavior as a diagnostic signal (not only scalar prediction error).

Why keep both branches:

- prevents over-committing to one paradigm too early,
- provides robust review narrative (“best empirical fit” vs “best physics consistency”),
- supports promotion gates based on combined criteria (accuracy + residual consistency + latency + robustness).

### 5.2 Non-technical summary

Instead of trusting one model type blindly, the project compares standard ML models with a physics-aware model (PINN). This gives both practical performance and scientific confidence.

---

## 6) Training workflow and experiment control

### 6.1 Technical details

The training stack is script-driven with reproducibility considerations:

- deterministic seeds where feasible,
- artifact-based persistence (checkpoints, scalers, stats),
- clean separation between generation, training, and benchmark scripts,
- configuration discipline for repeatable runs.

Typical run flow:

1. Generate/refresh dataset.
2. Split by flight ID.
3. Train baseline and PINN candidates.
4. Save best artifacts.
5. Execute benchmark script on held-out test partition.
6. Compare ranked outputs and archive results.

Engineering rationale:

- avoids hidden notebook-state dependence,
- supports rerun capability across machines,
- enables future CI automation and regression checks.

### 6.2 Non-technical summary

Model training is done through repeatable scripts, not ad-hoc manual steps, so results can be reproduced later and trusted in reviews.

---

## 7) Evaluation framework and metrics

### 7.1 Technical details

Benchmarking includes both prediction quality and deployment practicality:

- **MAE**: primary absolute error metric (interpretable in meters),
- **RMSE**: emphasizes larger misses,
- **R2**: variance-explained goodness,
- **p95 absolute error**: tail-risk indicator,
- **latency per sample (us)**: service viability for near-real-time contexts.

Evaluation principles:

- test set isolated by flight IDs,
- model ranking sorted by MAE for quick decision support,
- retained baseline analytical comparator (ballistic estimate) for sanity.

Interpretation policy:

- do not accept model promotion based on one metric only,
- inspect both central tendency (MAE/RMSE) and tails (p95),
- include runtime profile in model selection to avoid non-deployable winners.

### 7.2 Non-technical summary

The project measures not just “how accurate” a model is, but also “how bad worst-case errors are” and “how fast it runs,” so chosen models are practical, not just academically good.

---

## 8) API and software productization

### 8.1 Technical details

The CS component exposes model capability through FastAPI endpoints with typed schemas:

- structured request/response contracts,
- explicit units/field expectations,
- compatibility with experiment and embedded integrations.

API engineering goals:

- predictable behavior on valid/invalid payloads,
- stable interface for downstream consumers,
- metadata inclusion for traceability (`model/checkpoint/source tags` where configured).

Operational implications:

- benchmark artifacts can be connected to serving outputs,
- enables robust team collaboration across model developers and integration engineers,
- foundation for future staged deployment.

### 8.2 Non-technical summary

The model is not just trained; it is made usable through a proper API so other team members (and future onboard systems) can query it reliably.

---

## 9) Reliability, reproducibility, and traceability

### 9.1 Technical details

Current reliability practices include:

- fixed seeds in major workflows,
- split logic designed to prevent leakage,
- artifact versioning (models/scalers/stats),
- script-based benchmark output persistence (CSV/JSON),
- metadata-centric workflow for linking data/model/run context.

Traceability objective:

- every meaningful result should be attributable to
  dataset conditions + model artifact + evaluation script + runtime context.

Benefits:

- easier debugging,
- stronger thesis defensibility,
- reduced ambiguity in interdisciplinary discussions.

### 9.2 Non-technical summary

The team can explain where each result came from and rerun most of it, which makes the work trustworthy for faculty and future project handovers.

---

## 10) Testing and quality assurance

### 10.1 Technical details

The repository includes test scaffolding for physics, model, estimator, and API components. QA intent is to verify:

- physics behavior sanity,
- model-path correctness,
- service contract consistency,
- integration stability under expected input conditions.

Recommended QA strengthening (next phase):

- expand property-based tests for edge conditions,
- add automated benchmark-regression checks,
- add artifact integrity checks in CI (schema + model compatibility),
- formalize acceptance thresholds per milestone.

### 10.2 Non-technical summary

There is already a testing foundation, and the next step is to make it stricter and more automated so quality can be maintained as complexity grows.

---

## 11) CS-specific interpretation of the 25-figure pack

### 11.1 Technical interpretation

The generated figure pack supports CS deliverables across four dimensions:

- **Dynamics/data validity:** figures 1-12.
- **Model selection/performance:** figures 13-19.
- **Control and uncertainty reasoning:** figures 20-21.
- **Project systems/governance:** figures 22-25.

CS value:

- communicates feature-target structure,
- supports model tradeoff decisions,
- provides visual diagnostics for error/robustness,
- aligns software architecture and risk planning with engineering outcomes.

### 11.2 Non-technical summary

The 25 images are not decorative—they tell the full software story: data quality, model performance, robustness, control logic, and system maturity.

---

## 12) Limitations and technical debt

### 12.1 Technical limitations

1. Some high-level comparison visuals are illustrative and need empirical replacement for final thesis-grade evidence.
2. OOD stress testing can be expanded with formal perturbation suites.
3. Uncertainty calibration is not yet fully quantified with confidence calibration metrics.
4. Hardware-in-the-loop closure remains partial; API/embedded integration can be deepened.
5. End-to-end CI for model retraining + benchmark gating is not fully automated yet.

### 12.2 Non-technical summary

The core system is strong, but final-stage polish requires more empirical charts, stronger robustness proofs, and tighter automation.

---

## 13) Roadmap for the CS component (next phase)

### 13.1 Technical roadmap

**Phase A: Evidence hardening**

- regenerate all model-comparison figures from latest benchmark outputs,
- standardize evaluation report templates with version stamps.

**Phase B: Robustness expansion**

- structured OOD test matrix (drag, atmosphere, thrust-tail, noise),
- add reliability metrics beyond mean error (calibration/tail analyses).

**Phase C: Productization**

- stricter API validation and compatibility checks,
- latency/load profiling under realistic call patterns,
- artifact registry conventions for deployment-ready checkpoints.

**Phase D: Automation**

- CI job chain: data sanity -> train smoke -> benchmark -> threshold gate,
- reproducibility dashboard/report generation script.

### 13.2 Non-technical summary

Next, the CS team should focus on turning strong prototype work into fully defensible evidence and reliable automation so the system is ready for higher-stakes demonstrations.

---

## 14) Conclusion

### 14.1 Technical conclusion

The CS component has progressed from concept to an integrated engineering pipeline: simulation-driven data, model training (including PINN), comparative benchmarking, API exposure, and reproducibility-aware workflow. This already supports interdisciplinary review and forms a credible base for final validation and deployment-oriented maturation.

### 14.2 Non-technical summary

The software side is now a real system, not just experiments. It can generate, train, compare, and serve predictions in a structured way, and it is ready for the final refinement phase toward thesis and faculty presentation goals.

---

## Appendix A) Quick reference: where artifacts live

- CS report (this file): `docs/10_Presentation-Assets/CS-Component-Technical-Report.md`
- Comprehensive project report: `docs/10_Presentation-Assets/Comprehensive-Project-Report-and-Figure-Guide.md`
- Figure index: `docs/10_Presentation-Assets/Figure-Index.md`
- Figure assets: `docs/10_Presentation-Assets/figures`
- Figure generation script: `airbrake/scripts/generate_presentation_figures.py`

---

## Appendix B) Suggested viva/oral defense script (CS-focused)

1. Start with the software pipeline architecture in one minute.
2. Explain why split-by-flight and noise-aware data design matter.
3. Present baseline vs PINN strategy and evaluation metrics.
4. Show robustness/sensitivity visuals and discuss limits honestly.
5. Close with reproducibility, API readiness, and next-phase automation plan.

