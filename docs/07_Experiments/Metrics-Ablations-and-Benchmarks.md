---
title: Metrics, Ablations, and Benchmarks
tags:
  - evaluation
  - metrics
  - benchmarking
---

# Metrics, Ablations, and Benchmarks

## 1. Why This Note Exists

Many student projects show that something works once. Stronger projects show **how well**, **under what conditions**, and **compared to what**.

## 2. Primary System Metrics

### 2.1 Apogee Error

The most important top-level metric.

$$
e_h = h_{predicted\ or\ achieved} - h_{target}
$$

Use:

- mean absolute error,
- median absolute error,
- worst-case error,
- and dispersion under uncertainty.

### 2.2 Prediction Error

For the ML model itself, compare predicted final apogee to true final apogee at multiple points in the ascent.

### 2.3 Inference Latency

Measure time per inference on the target hardware or a hardware-representative platform.

### 2.4 Control Responsiveness

Measure how quickly the actuator responds after a significant predicted overshoot is detected.

### 2.5 Mechanical Reliability

Track failed deployments, partial deployments, and deployment repeatability across cycles.

## 3. Baselines That Must Be Included

To justify an ML-based controller, compare against at least these baselines:

- no airbrake deployment,
- fixed-threshold deployment,
- simple rule-based stepped deployment,
- and if possible a simplified analytical predictor.

## 4. Ablation Studies

### 4.1 Feature Ablation

Remove one feature family at a time, such as velocity or acceleration, and measure impact.

### 4.2 Noise Ablation

Increase sensor noise levels to see how quickly performance degrades.

### 4.3 Model Complexity Ablation

Compare small, medium, and large predictor variants to find the best accuracy-latency balance.

### 4.4 Control Resolution Ablation

Compare binary, stepped, and continuous deployment logic.

### 4.5 Estimation Ablation

Compare raw-state inputs against filtered or EKF-estimated inputs.

## 5. Robustness Benchmarks

The system should be evaluated across varied conditions rather than only nominal cases:

- low-thrust flights,
- high-drag flights,
- atmospheric variation,
- delayed actuator response,
- and off-nominal launch conditions.

## 6. Best Performance Storyline

A persuasive results section should be able to say something like:

> Compared with a fixed-threshold deployment baseline, the predictive controller reduced median apogee error, handled a wider range of atmospheric conditions, and remained fast enough for embedded execution.

## 7. What Reviewers Usually Ask

- Why use ML instead of a simpler model?
- What happens under conditions not seen during training?
- What is the computational cost?
- Is the gain worth the additional complexity?

The benchmark design should answer these directly.

## See Also

- [Control, AI, and State Estimation](../05_Architecture/Control-AI-and-State-Estimation.md)
- [Test and Validation Plan](Test-and-Validation-Plan.md)
- [Research Gap and Novelty](../04_Research/Research-Gap-and-Novelty.md)