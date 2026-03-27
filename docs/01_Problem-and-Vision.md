---
title: Problem and Vision
tags:
  - problem-definition
  - research-gap
  - motivation
---

# Problem and Vision

## 1. The Real Problem

The immediate problem is not simply that rockets go too high or too low. The deeper issue is that **rocket altitude is highly sensitive to uncertainty**, while common low-cost systems have only limited ability to adapt during flight.

Key uncertainty sources include:

- variation in motor impulse and burn profile,
- atmospheric density and wind changes,
- drag uncertainty due to surface finish and manufacturing deviations,
- launch angle and rail-exit perturbations,
- sensor noise and estimation drift,
- and delay between measurement, decision, and actuator response.

Because of this, two flights of nominally identical rockets can end with noticeably different apogees.

## 2. Why Target Apogee Matters

Accurate altitude control matters for multiple reasons:

- recovery becomes safer when flights stay within a known envelope,
- competition and mission rules may impose altitude windows,
- payload testing is more meaningful under repeatable flight conditions,
- and overshoot can increase drift distance, recovery time, and hardware loss risk.

In short, apogee targeting is not just a convenience metric. It is a systems-performance metric with operational consequences.

## 3. Shortcomings of Common Approaches

### 3.1 Passive Drag Devices

Fixed drag devices are simple, but once designed they cannot adapt to different atmospheric or motor conditions.

### 3.2 Basic Threshold Control

A simple rule such as "deploy after a fixed altitude" is easy to implement but usually ignores actual flight energy and future trajectory.

### 3.3 Classical PID-Only Thinking

PID control is powerful for many engineering systems, but for this problem it has limitations:

- the key output of interest, final apogee, is a future event,
- control authority is strongest only during certain flight phases,
- nonlinear drag behavior makes gain tuning less portable,
- and sensor/actuator latency can make correction too late.

PID can still be useful as a low-level actuator regulator, but it is not automatically the best high-level decision policy.

## 4. The Central Insight

The project becomes more interesting when the controller asks:

> "Given the current state, where is this rocket likely to end up if I do nothing, and how should I change drag now to shift that outcome?"

That changes the architecture from reactive control to predictive control.

## 5. Proposed Vision

The envisioned system uses:

- onboard sensor readings,
- a lightweight predictive model,
- a deployment policy linked to target altitude,
- and an actuated airbrake mechanism,

to decide how much aerodynamic drag to introduce during ascent or coast.

## 6. Research Positioning

This project sits in the overlap of four ideas:

1. **Active aerodynamics:** changing the aerodynamic profile in flight.
2. **Embedded intelligence:** making useful predictions on constrained hardware.
3. **State estimation:** cleaning sensor data into a control-ready state vector.
4. **Simulation-driven engineering:** using physics-based simulation to create data for design and control.

## 7. Stronger Framing for Reports and Viva

Instead of presenting the project as "airbrakes plus ML," a stronger framing is:

> An intelligent drag-modulation platform for controlled apogee targeting in uncertain flight environments.

This phrasing highlights that the innovation is in the integrated decision loop, not only in the actuator.

## 8. Key Questions the Project Should Answer

- Can a compact airbrake system provide enough control authority to matter?
- Which flight variables are sufficient to predict final apogee reliably?
- How early does the model need to act for meaningful correction?
- What is the best tradeoff between accuracy, interpretability, and embedded efficiency?
- How much improvement is possible compared with simple baseline strategies?

## 9. Project Storyline in One Paragraph

The project begins with the observation that altitude variation in model rockets is unavoidable under real operating conditions. It then proposes a predictive control framework in which onboard sensing and a fast surrogate model estimate future apogee, allowing a servo-actuated airbrake to deploy before overshoot becomes locked in. The result is a practical research prototype that links aerodynamic design, simulation, embedded intelligence, and closed-loop validation.

## See Also

- [Research Gap and Novelty](04_Research/Research-Gap-and-Novelty.md)
- [Control, AI, and State Estimation](05_Architecture/Control-AI-and-State-Estimation.md)
- [Metrics, Ablations, and Benchmarks](07_Experiments/Metrics-Ablations-and-Benchmarks.md)