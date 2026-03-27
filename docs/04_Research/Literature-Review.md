---
title: Literature Review
tags:
  - literature-review
  - prior-work
  - research-context
---

# Literature Review

## 1. Review Objective

The literature points to three recurring themes:

1. airbrakes are a practical mechanism for altitude shaping,
2. predictive control can improve performance but is often computationally expensive,
3. embedded implementation requires simplification, approximation, or surrogate modeling.

## 2. Mechanical Airbrake Design Studies

Studies on rocket airbrake systems typically focus on deployable fins or drag panels, actuation linkages, aerodynamic characterization, and basic control integration. These works show that airbrakes are mechanically feasible and can meaningfully alter apogee, but many rely on conventional control logic.

### Key takeaway

Mechanical feasibility is established, but intelligent onboard decision-making remains underdeveloped in many small-rocket implementations.

## 3. Optimal and Predictive Control Studies

Chance-constrained and model predictive control approaches treat altitude control as a forward-looking optimization problem. These methods are conceptually strong because they account for future state evolution rather than only present error.

### Strengths

- can explicitly include constraints,
- can handle uncertainty in a principled way,
- and are aligned with the future-oriented nature of the apogee-control problem.

### Limitations

- high computational cost,
- model dependence,
- limited suitability for low-cost embedded hardware.

## 4. Drag Modulation and Trajectory Shaping

Prior work on active drag modulation shows that changing drag area can reshape trajectory without altering thrust. This is directly aligned with the present project, because the mechanism of action is aerodynamic rather than propulsive.

### Relevance to this project

These studies justify the basic control authority assumption: changing drag can influence apogee enough to be useful.

## 5. Trajectory Simulation Tools

RocketPy and related 6-DOF simulation frameworks are important because they provide a practical path to generate large amounts of flight data without needing repeated real launches.

### Why this matters

The project needs supervised data for model training. Simulation offers:

- broad parameter coverage,
- repeatability,
- controlled uncertainty injection,
- and lower development cost than repeated flight testing.

## 6. State Estimation and Control Foundations

Classical control and estimation literature, including PID, feedback systems, and extended Kalman filtering, provides the mathematical backbone for stable real-time decision-making.

### Best interpretation for this project

These methods are best treated as building blocks rather than final answers. For example:

- EKF can improve state estimation,
- PID can regulate actuator motion,
- but the high-level altitude decision may still benefit from a learned apogee predictor.

## 7. Machine Learning and Surrogate Modeling Literature

General neural-network and deep-learning references support the feasibility of nonlinear function approximation. For this project, the key question is not whether neural networks can represent the mapping, but whether they can do so accurately, compactly, and fast enough for onboard use.

Relevant surrogate-model families include:

- multilayer perceptrons,
- gradient-boosted trees,
- Gaussian process regression,
- physics-informed neural networks,
- and hybrid physics-plus-data approximators.

## 8. How the Literature Supports the Project

The combined literature supports the project in the following way:

- airbrake hardware is feasible,
- active drag changes trajectory,
- predictive control is conceptually superior for this task,
- simulation can provide large datasets,
- and ML can approximate nonlinear mappings compactly.

## 9. Where the Literature Still Leaves Space

The strongest remaining opportunity is an integrated prototype that combines:

- deployable airbrake hardware,
- real-time sensing,
- lightweight onboard apogee prediction,
- embedded deployment control,
- and validation against realistic uncertainty.

That integrated framing is the main opening for this project.

## 10. Suggested Review Narrative for Reports

The literature review should not read like ten disconnected summaries. A stronger narrative is:

1. prior work proves drag modulation is useful,
2. control literature shows predictive methods are attractive,
3. embedded constraints make direct high-fidelity optimization difficult,
4. therefore a surrogate predictor paired with an airbrake is a logical compromise.

## See Also

- [Research Gap and Novelty](Research-Gap-and-Novelty.md)
- [Simulation and Dataset Pipeline](../06_Simulation/Simulation-and-Dataset-Pipeline.md)
- [Control, AI, and State Estimation](../05_Architecture/Control-AI-and-State-Estimation.md)