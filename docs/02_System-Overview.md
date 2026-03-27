---
title: System Overview
tags:
  - architecture
  - systems-view
  - integration
---

# System Overview

## 1. System Goal

The system aims to regulate rocket altitude by actively increasing aerodynamic drag when predicted apogee exceeds a desired target.

## 2. High-Level Closed Loop

The complete loop can be described as:

1. Sense current flight state.
2. Estimate altitude, vertical velocity, and related state variables.
3. Predict the final apogee if the current trajectory continues.
4. Compare predicted apogee to the target apogee.
5. Decide required airbrake deployment.
6. Command servo motion.
7. Change drag.
8. Observe new state and repeat.

## 3. Major Subsystems

### 3.1 Mechanical Subsystem

Includes:

- airbrake flaps or fins,
- deployment linkage,
- servo mounting,
- structural support,
- and packaging within the rocket body.

### 3.2 Sensing Subsystem

Includes:

- barometric pressure sensing for altitude estimation,
- IMU sensing for acceleration and angular motion,
- optional temperature compensation,
- and possibly event detection for motor burnout and coast-phase entry.

### 3.3 Embedded Computation Subsystem

Includes:

- microcontroller firmware,
- sensor acquisition,
- filtering/state estimation,
- model inference,
- decision logic,
- servo actuation,
- and logging.

### 3.4 Prediction and Control Subsystem

Includes:

- apogee surrogate model,
- confidence or uncertainty logic,
- deployment command computation,
- actuator rate limiting,
- and fail-safe fallback behavior.

### 3.5 Validation Subsystem

Includes:

- RocketPy trajectory simulation,
- CFD-informed drag characterization,
- structural validation,
- hardware bench tests,
- and flight or drop-test style integrated experiments.

## 4. Flight Phases and Relevance to Control

### 4.1 Powered Ascent

During thrust, the system may log data and estimate state, but aggressive deployment may be undesirable depending on mechanical load and mission design.

### 4.2 Coast Phase

This is the most important phase for altitude control. The motor has burned out, but the rocket still has upward velocity. Reducing drag too late is useless; increasing drag early enough during coast can shift the final apogee materially.

### 4.3 Near Apogee and Descent

The airbrake control objective is mostly complete. The system transitions to safe stowage or passive mode unless the mechanical design requires another configuration.

## 5. Minimum Viable Prototype

The first strong prototype does not need every advanced feature. A credible MVP would contain:

- one deployable airbrake mechanism,
- one barometer,
- one IMU,
- one microcontroller,
- one servo actuator,
- one onboard predictor,
- and one logging pipeline.

## 6. Expanded Research Prototype

An advanced version can additionally include:

- EKF-based state estimation,
- uncertainty-aware prediction,
- multiple control policies,
- lookup-table fallback,
- hardware-in-the-loop testing,
- and model compression for embedded deployment.

## 7. Example Data Flow

```text
Barometer + IMU -> preprocessing -> state estimate -> apogee predictor
-> target comparison -> deployment policy -> servo command -> airbrake angle
-> altered drag -> changed trajectory
```

## 8. Design Philosophy

The architecture should prefer:

- simple mechanical reliability over exotic mechanisms,
- state features that are observable in real time,
- lightweight inference over oversized models,
- and safe fallback logic over aggressive control behavior.

## 9. Key Integration Constraint

The overall system is only as good as its slowest weak link. High prediction accuracy is not useful if:

- the servo is too slow,
- the sensors are too noisy,
- the flap produces negligible drag,
- or the structure cannot survive deployment loads.

That is why this project must be treated as a full systems problem.

## See Also

- [Airbrake Mechanical Architecture](05_Architecture/Airbrake-Mechanical-Architecture.md)
- [Embedded Electronics and Sensing](05_Architecture/Embedded-Electronics-and-Sensing.md)
- [Simulation and Dataset Pipeline](06_Simulation/Simulation-and-Dataset-Pipeline.md)