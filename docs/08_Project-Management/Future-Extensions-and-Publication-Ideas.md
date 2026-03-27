---
title: Future Extensions and Publication Ideas
tags:
  - future-work
  - research-ideas
  - extensions
---

# Future Extensions and Publication Ideas

## 1. Why Future Work Should Be Explicit

The current concept already contains more ideas than a first prototype can execute well. A good documentation set should separate core scope from future expansion so the project stays finishable without losing ambition.

## 2. High-Value Future Technical Extensions

### 2.1 Physics-Informed Surrogate Models

Instead of learning purely from data, incorporate vertical-motion equations and drag relationships into the training loss. This could improve extrapolation and reduce data needs.

### 2.2 Uncertainty-Aware Prediction

Predict not only apogee, but also confidence. That enables conservative decisions when the system is uncertain.

### 2.3 Nonlinear Model Predictive Control

Use a learned or reduced-order dynamics model to optimize deployment across a finite horizon. This is stronger academically but should likely remain future work unless the basic system is already stable.

### 2.4 Hardware-in-the-Loop Validation

Inject simulated flight states into the embedded controller in real time and verify actuator behavior before field trials.

### 2.5 Adaptive or Online Calibration

Use early-flight observations to update drag or environmental assumptions during the same flight.

### 2.6 Multi-Objective Control

Extend beyond apogee targeting to consider recovery drift, structural load, or stability margin.

## 3. Strong Publication Angles

### Publication Angle A

**Simulation-driven embedded apogee prediction for low-cost active drag control in model rockets**

Focus on data generation, model benchmarking, and real-time inference.

### Publication Angle B

**Integrated design of a prototype airbrake system for predictive aerodynamic altitude control**

Focus on full systems integration.

### Publication Angle C

**Comparative study of analytical, ML, and hybrid apogee predictors under flight uncertainty**

Focus on model comparison and evaluation discipline.

## 4. Stronger Experimental Extensions

- compare different flap geometries,
- compare deployment schedules,
- compare onboard vs offboard prediction,
- and compare deterministic vs uncertainty-aware controllers.

## 5. Long-Term Vision

In the long run, the project can evolve into a reusable altitude-control test platform for student rocketry, allowing future teams to investigate:

- adaptive guidance,
- robust embedded ML,
- intelligent recovery triggering,
- and broader active-aerodynamics concepts.

## 6. Best Strategic Advice

Finish the simple version well, document it rigorously, and use the future-work section to show technical maturity. Reviewers usually trust a disciplined roadmap more than an overloaded first prototype.

## See Also

- [Research Gap and Novelty](../04_Research/Research-Gap-and-Novelty.md)
- [Control, AI, and State Estimation](../05_Architecture/Control-AI-and-State-Estimation.md)
- [Deliverables and Expected Outcomes](Deliverables-and-Expected-Outcomes.md)