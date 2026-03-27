---
title: Embedded Electronics and Sensing
tags:
  - embedded-systems
  - sensing
  - avionics
---

# Embedded Electronics and Sensing

## 1. Subsystem Mission

This subsystem must turn a noisy physical flight environment into a reliable real-time digital representation that can drive deployment decisions.

## 2. Core Hardware Blocks

### 2.1 Microcontroller

The microcontroller must support:

- sensor sampling,
- real-time filtering,
- model inference,
- servo PWM generation,
- logging,
- and deterministic loop timing.

Selection criteria should include:

- clock speed,
- RAM and flash,
- floating-point support,
- ADC and bus interfaces,
- low-latency interrupts,
- and development ecosystem maturity.

### 2.2 Barometric Sensor

Used to infer altitude from pressure.

Important considerations:

- update rate,
- pressure resolution,
- temperature sensitivity,
- response lag,
- and dynamic pressure contamination.

### 2.3 IMU

Used to measure acceleration and angular rates.

Important considerations:

- accelerometer range,
- gyro range,
- bias drift,
- noise density,
- and mounting alignment.

### 2.4 Servo Actuator

The servo must provide:

- adequate torque,
- sufficient speed,
- low backlash,
- predictable power draw,
- and mechanical compatibility with the linkage.

### 2.5 Power Subsystem

The power system must handle:

- sensor operation,
- transient servo current draw,
- logging electronics,
- and safe voltage regulation under load.

## 3. Sensor Fusion and State Estimation

### 3.1 Why Filtering Is Needed

Raw sensor readings are noisy, delayed, biased, and sometimes contradictory. The controller should not act directly on unfiltered data if a better state estimate is possible.

### 3.2 Minimum Estimation Stack

A practical first version can use:

- barometric altitude,
- velocity estimated from filtered altitude change,
- and IMU acceleration for phase/event awareness.

### 3.3 Better Estimation Stack

An improved version can use an EKF or complementary filter to estimate:

- altitude,
- vertical velocity,
- vertical acceleration,
- and confidence in the estimate.

## 4. Control-Loop Timing

The loop should be designed around a fixed update schedule. At each cycle the firmware should:

1. sample sensors,
2. update state estimate,
3. run apogee prediction,
4. compute deployment command,
5. issue actuator output,
6. log important data.

Timing discipline matters because inconsistent loop intervals can degrade both estimation and control stability.

## 5. Logging Strategy

Minimum useful fields to log:

- timestamp,
- pressure,
- estimated altitude,
- accelerometer data,
- estimated vertical velocity,
- predicted apogee,
- target apogee,
- commanded deployment,
- actual servo position if available,
- and fault flags.

These logs are essential for diagnosing why a flight succeeded or failed.

## 6. Fault Handling

The firmware should define clear responses for:

- sensor timeout,
- impossible altitude jump,
- servo stall,
- low-voltage event,
- memory overflow,
- and inference failure.

Typical fallback behaviors might include holding the last safe deployment command or reverting to a conservative default state.

## 7. Good Embedded Design Practice

- isolate high-current servo power from sensitive sensor supply where possible,
- use timestamped sampled data rather than ad hoc polling assumptions,
- implement watchdog recovery,
- and keep the control path deterministic and debuggable.

## 8. Strong Prototype Principle

The objective is not to build a feature-rich avionics board on the first attempt. The objective is to build a loop that is:

- observable,
- stable,
- testable,
- and fast enough.

## See Also

- [Control, AI, and State Estimation](Control-AI-and-State-Estimation.md)
- [Test and Validation Plan](../07_Experiments/Test-and-Validation-Plan.md)
- [Risks, Mitigations, and Safety](../08_Project-Management/Risks-Mitigations-and-Safety.md)