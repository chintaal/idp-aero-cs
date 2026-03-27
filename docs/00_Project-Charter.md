---
title: Project Charter
tags:
  - charter
  - scope
  - systems-engineering
---

# Project Charter

## 1. Project Identity

**Title:** Design and Development of a Prototype Active Airbrake System for Controlled Aerodynamic Drag in Rocket Applications

**Institution:** RV College of Engineering

**Theme:** Active Aerodynamics

**Team intent:** Build a prototype system that can estimate likely final apogee during ascent and modulate aerodynamic drag using an active airbrake mechanism so that the rocket reaches a target altitude more reliably.

## 2. Problem Summary

Model rockets often miss their desired apogee because the actual flight environment is never identical to the planned one. Variation can arise from:

- motor thrust curve deviations,
- wind and atmospheric density changes,
- uncertain drag coefficients,
- manufacturing tolerance in structure and fin alignment,
- launch rail departure conditions,
- and small differences in mass and center of gravity.

Passive drag devices cannot adapt in flight. Traditional reactive controllers can also be late, because by the time altitude error is visible, the rocket may already have accumulated too much kinetic energy to correct accurately.

## 3. Vision Statement

The project vision is to move from **reactive drag control** to **predictive drag control**. Instead of waiting to see altitude error after the fact, the system continuously estimates future apogee from current flight state and decides whether airbrake deployment is needed before overshoot becomes unavoidable.

## 4. Core Hypothesis

If the system can estimate apogee fast enough and accurately enough during the coast phase, then a compact airbrake actuator can reduce overshoot and tighten altitude dispersion compared with fixed drag or simple threshold-based deployment.

## 5. Main Objectives

### 5.1 Primary Objective

Design, fabricate, and validate a prototype active airbrake system for small rocket applications.

### 5.2 Technical Objectives

- Build a deployable drag-surface mechanism that is compact, robust, and repeatable.
- Sense the rocket state using a barometer and IMU, with optional filtering or fusion.
- Generate simulated flight data across varying atmospheric and launch conditions.
- Train a lightweight surrogate model that predicts final apogee from the current state.
- Convert predicted altitude error into a real-time flap deployment command.
- Test the integrated system through simulation, bench testing, and prototype-level validation.

### 5.3 Research Objectives

- Compare ML-based apogee prediction with simpler baselines.
- Evaluate whether predictive deployment improves target-altitude accuracy.
- Establish a feasible simulation-to-embedded workflow for low-cost experimental rocketry.

## 6. Scope

### 6.1 In Scope

- Prototype airbrake mechanical design.
- Embedded sensing and actuation.
- RocketPy-based trajectory simulation for dataset generation.
- Surrogate-model development for apogee prediction.
- Real-time control logic for drag deployment.
- Ground and limited integrated validation.

### 6.2 Out of Scope for the First Prototype

- Full autonomous guidance in lateral axes.
- High-altitude certified flight campaigns.
- Production-grade avionics certification.
- Complex multi-stage rockets.
- Real-time onboard CFD or full nonlinear optimal control.

## 7. Why This Project Matters

This project is valuable because it connects several difficult engineering layers that are often studied in isolation:

- aerodynamic modulation,
- low-latency inference,
- embedded control,
- state estimation under noisy sensing,
- and flight validation under uncertainty.

That integration makes the work stronger than a purely mechanical design study or a purely simulation-driven ML exercise.

## 8. Success Criteria

The project should be considered successful if it demonstrates the following convincingly:

1. The airbrake mechanism can deploy repeatedly and safely.
2. The sensing and firmware loop can estimate usable flight state in real time.
3. The predictive model runs within embedded timing and memory limits.
4. The controller meaningfully reduces apogee error in simulation and test scenarios.
5. The final documentation clearly explains the design rationale, validation logic, and future path.

## 9. Suggested Final Narrative

When presented formally, the project should be framed as:

> A low-cost, interdisciplinary prototype for predictive aerodynamic altitude control in rockets, combining airbrake hardware, simulation-generated data, and embedded intelligence to improve apogee targeting under uncertainty.

## See Also

- [01_Problem-and-Vision](01_Problem-and-Vision.md)
- [02_System-Overview](02_System-Overview.md)
- [Deliverables and Expected Outcomes](08_Project-Management/Deliverables-and-Expected-Outcomes.md)