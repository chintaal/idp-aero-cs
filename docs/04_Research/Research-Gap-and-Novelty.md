---
title: Research Gap and Novelty
tags:
  - research-gap
  - novelty
  - contributions
---

# Research Gap and Novelty

## 1. The Gap in One Sentence

Existing small-rocket airbrake systems often demonstrate either mechanical drag modulation or conventional control, but not a tightly integrated predictive embedded system that uses real-time state information to estimate and regulate future apogee efficiently.

## 2. Detailed Gap Analysis

### 2.1 Mechanical Work Often Stops at Deployment Feasibility

Many airbrake-focused projects answer:

- Can the mechanism deploy?
- Does it generate additional drag?
- Can it survive the load?

These are necessary questions, but not sufficient for a complete altitude-control system.

### 2.2 Control Work Often Assumes Too Much Compute

Advanced predictive control methods are theoretically strong, but they can be impractical for lightweight embedded hardware because they require repeated model evaluation or online optimization.

### 2.3 ML Work Is Rarely Closed-Loop and Hardware-Grounded

General ML literature shows that nonlinear predictors are feasible, but many studies are not tied to an actual actuation mechanism, real sensor pipeline, or control budget.

### 2.4 Systems Integration Is the Missing Layer

The real gap is not in any single component. The gap is in end-to-end integration:

- sensing,
- estimation,
- prediction,
- control,
- actuation,
- and validation.

## 3. What Is Novel About This Project

The project can claim novelty in the combination of the following features:

### 3.1 Predictive Apogee Estimation for Airbrake Deployment

Instead of using only instantaneous thresholds, the system acts on predicted future altitude.

### 3.2 Lightweight Surrogate Modeling for Embedded Use

The project explicitly targets models that are fast enough for real-time microcontroller deployment rather than only offline analysis.

### 3.3 Cross-Domain Prototype

It combines aerodynamic design, embedded avionics, control logic, and ML inference in a single prototype.

### 3.4 Simulation-Driven Development Pipeline

It uses RocketPy or equivalent physics-based simulation to synthesize training data under variable conditions, reducing dependence on expensive experimental datasets.

## 4. Strong Candidate Contributions

If executed cleanly, the project can present these as its main contributions:

1. A prototype active airbrake hardware platform suitable for controlled drag deployment.
2. A real-time apogee-prediction workflow based on simulated flight data.
3. A comparative evaluation of predictive control against simpler baselines.
4. A systems-level methodology that links simulation, ML, embedded deployment, and physical validation.

## 5. Contribution Positioning by Audience

### For Aerospace Faculty

Emphasize aerodynamic drag modulation, coast-phase control authority, flight envelope reasoning, and simulation-backed validation.

### For Computer Science or Information Science Faculty

Emphasize edge inference, model compression, surrogate learning, sensor fusion, and embedded decision-making.

### For Interdisciplinary Reviewers

Emphasize integrated engineering and the conversion of a simulation insight into a hardware-aware control prototype.

## 6. What Not to Overclaim

The project should avoid overclaiming in these areas unless directly proven:

- full autonomous GNC capability,
- robust performance across all rocket classes,
- guaranteed optimality,
- or direct transfer from simulation to all real flight conditions without calibration.

The best claim is a careful one: the prototype demonstrates the feasibility and benefit of predictive drag modulation under a defined flight envelope.

## 7. Best Thesis-Style Contribution Statement

> This work presents a prototype active airbrake system that integrates simulation-based apogee prediction, embedded sensing, and real-time drag modulation to improve altitude targeting in model rocket flight under uncertainty.

## See Also

- [Project Charter](../00_Project-Charter.md)
- [Problem and Vision](../01_Problem-and-Vision.md)
- [Future Extensions and Publication Ideas](../08_Project-Management/Future-Extensions-and-Publication-Ideas.md)