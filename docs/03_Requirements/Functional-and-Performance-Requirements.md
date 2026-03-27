---
title: Functional and Performance Requirements
tags:
  - requirements
  - verification
  - system-specification
---

# Functional and Performance Requirements

## 1. Purpose of This Note

This note converts the idea into concrete engineering requirements that can later be traced to tests, simulations, and design decisions.

## 2. Functional Requirements

### FR-1 Sensing

The system shall acquire barometric and inertial sensor data during flight at a sampling rate sufficient for real-time state estimation and deployment decisions.

### FR-2 State Estimation

The system shall estimate at least altitude and vertical velocity, either directly or through filtering/fusion.

### FR-3 Apogee Prediction

The system shall estimate future apogee from the current state during ascent or coast.

### FR-4 Target Comparison

The system shall compare predicted apogee against a user-defined or mission-defined target apogee.

### FR-5 Airbrake Actuation

The system shall command an actuator to deploy or retract drag surfaces according to the control policy.

### FR-6 Event Awareness

The system shall identify or infer important flight phases such as launch detection, burnout, coast, and near-apogee transition.

### FR-7 Data Logging

The system shall log key sensor, state, prediction, and actuator data for post-flight analysis.

### FR-8 Safe Behavior

The system shall enter a safe fallback mode when sensing becomes invalid, power is insufficient, or actuator commands exceed safe bounds.

## 3. Performance Requirements

### PR-1 Prediction Latency

Inference and decision logic should complete within a bounded time budget that is small compared with the control-loop interval.

### PR-2 Sensor Update Rate

The effective update rate should be high enough to capture velocity change and actuator timing during coast.

### PR-3 Actuator Response

The airbrake mechanism should reach commanded positions quickly and repeatably without excessive overshoot or jamming.

### PR-4 Targeting Accuracy

The prototype should demonstrate reduced apogee error relative to at least one simpler baseline method.

### PR-5 Mechanical Durability

The airbrake mechanism should survive repeated ground deployment cycles and expected aerodynamic loading within the intended prototype envelope.

### PR-6 Estimation Stability

The state estimator should remain numerically stable under realistic sensor noise and brief disturbances.

## 4. Design Constraints

### 4.1 Embedded Constraints

- Limited flash and RAM.
- Limited floating-point performance.
- Finite servo power budget.
- Real-time scheduling and interrupt constraints.

### 4.2 Mechanical Constraints

- Limited body tube volume.
- Mass penalty from servo and linkage.
- Need to preserve center-of-gravity margin.
- Need to prevent structural interference with ejection and recovery systems.

### 4.3 Flight Constraints

- Actuation must not destabilize the rocket.
- Drag change must be significant enough to matter.
- Deployment timing must occur before useful control authority is lost.

## 5. Derived Engineering Questions

The requirements immediately imply several design questions:

- What state vector is sufficient for prediction?
- Should the control output be binary, stepped, or continuous deployment?
- What is the acceptable tradeoff between prediction accuracy and embedded footprint?
- How much additional drag is needed to reduce overshoot by a useful amount?
- What is the best fallback strategy when the predictor becomes unreliable?

## 6. Verification Mapping

Each major requirement should map to at least one validation method:

- **Simulation:** FR-2, FR-3, FR-4, PR-4, PR-6
- **Bench test:** FR-5, FR-7, FR-8, PR-1, PR-3, PR-5
- **Mechanical inspection:** FR-5, PR-5
- **Integrated testing:** all core functional requirements together

## 7. Recommended Minimum Acceptance Criteria

For a first academic prototype, the team can define acceptance in practical terms:

- successful sensor acquisition and logging,
- repeatable actuator deployment on command,
- stable real-time execution loop,
- visible change in simulated apogee under controlled deployment,
- and evidence that predictive control outperforms a naive rule-based baseline.

## See Also

- [System Overview](../02_System-Overview.md)
- [Test and Validation Plan](../07_Experiments/Test-and-Validation-Plan.md)
- [Metrics, Ablations, and Benchmarks](../07_Experiments/Metrics-Ablations-and-Benchmarks.md)