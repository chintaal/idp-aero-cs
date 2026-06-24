# Comprehensive Project Report and Figure Guide

## 1) Project identity and interdisciplinary context

**Project title:** Design and Development of a Prototype Active Airbrake System for Controlled Aerodynamic Drag in Rocket Applications.

This work is an interdisciplinary aerospace + computer science effort to achieve better apogee control using a deployable airbrake system, simulation-grounded data generation, machine-learning-based apogee prediction, and an embedded telemetry/control path. The objective is not only a model with low error, but a traceable engineering pipeline that links aerodynamic assumptions, simulation tools, software inference, and hardware readiness.

Primary outcomes so far:

- A physics-based 1D rocket dynamics simulation with thrust, drag, gravity, atmosphere, and airbrake deployment effects.
- A reproducible dataset generation pipeline from Monte Carlo flight simulation with controlled noise injection.
- Baseline ML models and a PINN branch for physics-informed learning and comparison.
- Benchmarking infrastructure for multi-model evaluation using MAE/RMSE/R2/p95 and latency.
- API and software scaffolding for deployment-oriented inference workflows.
- Embedded progress on ESP32 bring-up, telemetry path checks, and sensing readiness.
- A 25-image figure pack for faculty presentation (`docs/10_Presentation-Assets/figures`).

---

## 2) Problem statement and why this matters

In practical rocketry, reaching a target apogee consistently is difficult because drag, mass changes, atmosphere, and thrust profile variations all affect trajectory. Passive designs can be conservative but are less adaptable. Active airbrakes enable drag modulation in flight, but require:

- reliable state understanding,
- robust apogee prediction under uncertainty,
- and implementation discipline across software and hardware.

This project addresses that by combining aerospace modeling with CS/ML methods and embedded systems integration.

---

## 3) Technical system implemented so far

## 3.1 Physics and simulation backbone

The simulation stack models vertical motion with state `[h, v]`:

- **Forces modeled:** thrust (during burn), aerodynamic drag, gravity.
- **Atmosphere model:** altitude-dependent density (ISA-like behavior).
- **Airbrake model:** deployment fraction in `[0,1]` modifies drag coefficient.
- **Mass model:** wet-to-dry mass transition during burn.
- **Flight outputs:** time histories of altitude, velocity, acceleration, plus apogee and apogee time.

This provides physics-consistent trajectories and forms the basis of both synthetic data generation and interpretation of model behavior.

## 3.2 Dataset engineering

A Monte Carlo simulation workflow is in place:

- Randomized rocket parameters within realistic ranges.
- Deployment cases sampled across discrete fractions.
- Coast-phase snapshots extracted as supervised learning rows.
- Controlled sensor-like noise added to `h`, `v`, `a`.
- Flight-ID-aware split strategy to prevent leakage across train/val/test.

This is crucial for making model comparisons meaningful and reproducible.

## 3.3 Modeling and benchmarking

Two modeling philosophies are maintained:

- **Conventional baselines:** linear/tree/boosting style models for fast, interpretable benchmarks.
- **PINN path:** combines data fitting and physics residual regularization for improved physical consistency and potential OOD robustness.

Benchmarking pipeline supports:

- MAE, RMSE, R2, p95 error,
- inference latency,
- ranked summaries for side-by-side model decisions.

## 3.4 API and software engineering

Software work includes:

- FastAPI serving path for prediction workflows.
- Data/schema discipline (typed input-output handling).
- Config-driven and scriptable experiment execution.
- Logging and metadata alignment for traceability.

## 3.5 Embedded/IoT track

Embedded efforts focus on system closure:

- ESP32 bring-up and bench measurements.
- Telemetry path validation over WiFi.
- ADC/noise characterization for future control/sensing loops.

This keeps the project grounded beyond pure offline ML.

---

## 4) Work completed timeline summary (Weeks 1-8)

## Week 1

- Literature and control framing for airbrake apogee control.
- Initial architecture decisions (regression + PINN branch).
- Early dataset curation and training skeleton setup.

## Week 2

- Preliminary airbrake geometry constraints.
- OpenRocket and Mach-aligned trajectory setup.
- CFD direction for drag case extraction.
- FastAPI model hosting path initialized.

## Week 3

- Simulated stowed/deployed drag scenarios (0° and full deploy case).
- Aerospace-domain assumptions integrated into CS stack.
- Improved run robustness via config, error handling, and logging.

## Week 4

- v1 apogee model training convergence and validation outcomes.
- OpenRocket-aligned case checks and phase-binned error inspection.
- ESP32 electrical baseline bring-up and current profiling.

## Week 5

- Formal regression vs PINN comparison on held-out cases.
- CPU serving latency profiling (p50/p95) and payload stability.
- Mismatch analysis for atmosphere/thrust assumptions.
- ESP32-to-API telemetry trials on LAN.

## Week 6

- Cross-machine reproducibility checks with fixed seed.
- Cd sensitivity quantification to apogee delta.
- Version tagging discipline in API metadata.
- ADC quality/noise bench assessment for sensor path readiness.

## Week 7

- Structured comparison across six model families:
  linear/polynomial, tree ensembles, MLP, sequence models, model-based estimators, and lookup methods.
- Evaluated tradeoffs on sample efficiency, physical consistency, robustness, compute, and deployment suitability.

## Week 8

- Formalized PINN advantages/disadvantages and decision logic.
- Consolidated recommendation:
  keep baseline models as guardrails, continue PINN as primary R&D path, and gate promotion using joint performance + physics + robustness + serving criteria.

---

## 5) Current strengths, gaps, and next steps

## Current strengths

- Clear simulation-to-data-to-model pipeline.
- Balanced use of conventional and physics-informed models.
- Stronger project narrative via software traceability and embedded progress.
- Presentation-ready technical figure pack now available.

## Current gaps

- Some presentation comparisons are illustrative and should be replaced with empirical versions where needed.
- OOD robustness and uncertainty quantification can be expanded further with stress matrices.
- Hardware-in-the-loop closure is still in progress.

## Recommended next steps

- Regenerate selected benchmark charts directly from latest real benchmark runs.
- Add explicit uncertainty calibration plots and confidence-bound validation.
- Extend telemetry/control loop tests from bench to integrated dry-run scenarios.

---

## 6) Figure guide: brief explanation of all 25 images

All figures are stored in: `docs/10_Presentation-Assets/figures`.

1. **`01_altitude_profiles.png`**  
   Shows altitude vs time for multiple deployment settings, visualizing how stronger brake deployment lowers trajectory peak.

2. **`02_velocity_profiles.png`**  
   Shows velocity evolution and near-apogee zero crossing behavior across deployment scenarios.

3. **`03_acceleration_profiles.png`**  
   Shows acceleration dynamics and how drag modulation changes deceleration trends during coast.

4. **`04_apogee_vs_deployment.png`**  
   Direct control-authority plot mapping deployment fraction to achieved apogee.

5. **`05_burnout_state_map.png`**  
   Compares burnout state points `(h, v)` to verify initial coast conditions and consistency across cases.

6. **`06_density_vs_altitude.png`**  
   Atmospheric density curve used by the dynamics and PINN physics terms.

7. **`07_thrust_mass_profiles.png`**  
   Two-panel view of powered-phase assumptions: thrust schedule and propellant-driven mass depletion.

8. **`08_drag_envelope.png`**  
   Drag-force envelope vs velocity for different deployment fractions, illustrating aerodynamic leverage.

9. **`09_target_distribution.png`**  
   Distribution of supervised apogee targets in generated training data.

10. **`10_deployment_balance.png`**  
    Class-balance check for deployment fractions in the dataset.

11. **`11_state_space_scatter.png`**  
    Scatter of `(h, v)` states colored by target apogee, showing sample manifold structure.

12. **`12_correlation_heatmap.png`**  
    Correlation map across key features and target, useful for feature-signal intuition.

13. **`13_model_benchmark_mae.png`**  
    Model ranking by MAE for quick comparative discussion in reviews.

14. **`14_accuracy_latency_pareto.png`**  
    Tradeoff between prediction error and runtime latency, supporting deployment decisions.

15. **`15_id_vs_ood.png`**  
    Contrasts in-distribution and stress/OOD error behavior for robustness interpretation.

16. **`16_pinn_loss_convergence.png`**  
    PINN training-loss decomposition (data vs physics residual) to explain optimization behavior.

17. **`17_cd_sensitivity.png`**  
    Sensitivity of apogee output to perturbations in drag coefficient; links aero uncertainty to mission outcome.

18. **`18_noise_robustness.png`**  
    Error trends under increasing sensor-noise levels, comparing model robustness.

19. **`19_error_cdf.png`**  
    Error CDF plot for percentile-based reliability and tail-risk assessment.

20. **`20_control_policy_schedules.png`**  
    Conceptual early-vs-late brake deployment schedules for control-policy discussion.

21. **`21_monte_carlo_band.png`**  
    Mean apogee with confidence band across deployment levels, summarizing uncertainty envelope.

22. **`22_interdisciplinary_timeline.png`**  
    Maturity trend lines for ML, aero, and embedded tracks across project weeks.

23. **`23_risk_matrix.png`**  
    Bubble-style risk map (probability vs impact) for management and mitigation planning.

24. **`24_model_selection_radar.png`**  
    Criteria-based visual comparison (accuracy, consistency, latency, robustness, interpretability, embedded fit).

25. **`25_system_architecture_flow.png`**  
    End-to-end system flow diagram from simulation/data to model training, API, validation, and embedded stack.

---

## 7) How to present this to aerospace faculty

Recommended flow for oral presentation:

1. Start with mission need: why active apogee control matters.
2. Show physics credibility: simulation assumptions and atmosphere/drag modeling.
3. Show ML with guardrails: baseline + PINN, not PINN-only.
4. Show validation discipline: benchmark metrics, robustness, and sensitivity.
5. Show system readiness: API traceability and embedded path.
6. Conclude with current maturity, known gaps, and a clean next-phase plan.

---

## 8) Notes on evidence level

- Figures tied to simulation outputs and dataset structure are generated from project code paths.
- Some model-comparison and management visuals are marked/treated as **illustrative presentation assets** and should be replaced with empirical run-derived versions for final thesis tables if required by evaluation policy.

---

*Prepared as a single consolidated document for interdisciplinary review and faculty presentation.*
