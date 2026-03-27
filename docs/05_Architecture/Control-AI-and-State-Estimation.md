---
title: Control, AI, and State Estimation
tags:
  - machine-learning
  - control
  - prediction
  - estimation
---

# Control, AI, and State Estimation

## 1. Problem Formulation

The system must choose airbrake deployment based on the current estimated state so that final apogee approaches a target altitude.

At a high level, the controller is solving:

$$
u_t = f(x_t, h_{target})
$$

where:

- $x_t$ is the current estimated flight state,
- $h_{target}$ is the desired apogee,
- and $u_t$ is the deployment command.

## 2. What the Predictor Should Estimate

The most useful prediction target is usually one of the following:

- predicted final apogee under current deployment,
- predicted apogee error relative to target,
- or predicted change in apogee for a candidate deployment level.

For a first prototype, direct prediction of final apogee is the clearest choice.

## 3. Candidate Input Features

Likely useful features include:

- current altitude,
- vertical velocity,
- vertical acceleration,
- elapsed time since launch,
- detected flight phase,
- current deployment angle,
- estimated mass or motor class as a mission parameter,
- and environmental assumptions such as density model index or nominal wind class.

Feature choice should be driven by what can actually be measured or estimated onboard.

## 4. Candidate Model Families

### 4.1 Multilayer Perceptron

Best overall first choice for this project.

Why:

- handles nonlinear relationships,
- compact enough for embedded use,
- simple inference graph,
- and straightforward quantization path.

### 4.2 Gradient-Boosted Trees

Useful as strong tabular-data baselines.

Why:

- often excellent on structured datasets,
- fast training,
- strong baseline for comparison.

Concern:

- deployment on constrained embedded systems can be less elegant depending on the toolchain.

### 4.3 Gaussian Process Regression

Interesting because it provides uncertainty, but scalability and inference cost can become limiting.

### 4.4 Physics-Informed Neural Networks

Conceptually attractive, especially because the flight obeys known equations. However, they may be too ambitious for a first prototype unless the team already has experience with them.

### 4.5 Classical Analytical Estimator

A simplified ballistic or drag-adjusted predictor is a strong baseline and should not be skipped. The ML model must outperform something credible, not just something trivial.

## 5. Recommended Modeling Strategy

### Phase 1

- train a simple analytical baseline,
- train a small MLP,
- train one tree-based model,
- compare accuracy and latency.

### Phase 2

- compress or quantize the chosen model,
- validate robustness under noisy input,
- benchmark embedded inference timing.

### Phase 3

- optionally extend toward uncertainty-aware prediction or hybrid physics-informed learning.

## 6. State Estimation Layer

The predictor should ideally not consume raw sensor signals directly. A better stack is:

```text
raw sensors -> filtered state estimate -> prediction model -> deployment policy
```

An EKF is attractive if the team can implement it reliably, because it explicitly models process evolution and measurement correction.

## 7. Control Policy Options

### 7.1 Binary Deployment

Deploy or do not deploy.

**Pros:** simple, easy to test.

**Cons:** limited control resolution.

### 7.2 Stepped Deployment

Choose among a few discrete angles.

**Pros:** good compromise between simplicity and flexibility.

**Cons:** still approximate.

### 7.3 Continuous Deployment

Command a continuous flap angle.

**Pros:** potentially better control quality.

**Cons:** higher sensitivity to actuator precision and control noise.

For a first prototype, stepped deployment is often the best compromise.

## 8. Example Control Logic

One practical decision structure is:

1. Estimate current state.
2. Predict final apogee.
3. Compute error: predicted apogee minus target.
4. Map error to deployment level.
5. Apply rate limits and safety checks.
6. Command servo.

This is simpler and more defensible than jumping directly to a complex optimal controller.

## 9. Important Failure Modes

- prediction drift due to out-of-distribution flight conditions,
- unstable velocity estimate from noisy altitude differentiation,
- overaggressive deployment causing oscillatory commands,
- and poor correlation between commanded flap angle and actual drag effect.

## 10. Strong Evaluation Questions

- How early in flight can the model predict apogee accurately?
- Which features contribute most to performance?
- Does the control policy improve mean apogee error, worst-case error, or both?
- How much latency can the loop tolerate before benefits disappear?

## 11. Best Practical Recommendation

The best first full-stack version is likely:

- filtered altitude and velocity estimate,
- small MLP predictor,
- stepped deployment policy,
- and safe fallback lookup behavior.

This is sophisticated enough to be interesting and simple enough to finish well.

## See Also

- [ML Models and Control Algorithms](ML-Models-and-Control-Algorithms.md)
- [Simulation and Dataset Pipeline](../06_Simulation/Simulation-and-Dataset-Pipeline.md)
- [Metrics, Ablations, and Benchmarks](../07_Experiments/Metrics-Ablations-and-Benchmarks.md)
- [Future Extensions and Publication Ideas](../08_Project-Management/Future-Extensions-and-Publication-Ideas.md)