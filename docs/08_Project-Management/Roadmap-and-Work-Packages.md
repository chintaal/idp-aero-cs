---
title: Roadmap and Work Packages
tags:
  - roadmap
  - planning
  - execution
---

# Roadmap and Work Packages

## 1. Execution Philosophy

The project should be executed as interacting work packages, not as isolated tasks. Mechanical design, simulation, and embedded development must inform one another continuously.

## 2. Recommended Work Packages

### WP-1 Problem Definition and Review

- finalize project scope,
- stabilize the literature review,
- define clear research questions,
- and agree on success metrics.

### WP-2 Mechanical Concept and CAD

- choose airbrake mechanism type,
- complete initial geometry,
- estimate packaging and mass budget,
- prepare prototype fabrication plan.

### WP-3 Simulation Backbone

- build nominal rocket model,
- integrate variable drag logic,
- perform parameter sweeps,
- generate first training dataset.

### WP-4 Estimation and Control Logic

- define state variables,
- build baseline predictor,
- build ML surrogate,
- define deployment policy and fallback logic.

### WP-5 Embedded and Electronics Integration

- select hardware,
- build firmware loop,
- integrate sensors,
- integrate servo and logging.

### WP-6 CFD and Structural Checks

- evaluate deployment aerodynamics,
- estimate loading,
- adjust design if required.

### WP-7 Testing and Demonstration

- execute bench tests,
- execute integrated validation,
- document performance and lessons learned.

## 3. Recommended Order of Attack

The best execution path is usually:

1. stabilize requirements and evaluation criteria,
2. start simulation early,
3. design hardware in parallel,
4. build the smallest working embedded loop,
5. integrate only after subcomponents are individually tested.

## 4. Suggested Milestones

- **M1:** problem statement, literature review, and requirements locked.
- **M2:** nominal simulation pipeline working.
- **M3:** first mechanical concept and CAD ready.
- **M4:** first predictor trained and benchmarked.
- **M5:** electronics stack reading sensors and commanding servo.
- **M6:** integrated prototype functional on bench.
- **M7:** final validation and documentation complete.

## 5. Team Collaboration Model

Since the project is interdisciplinary, each work package should have:

- one primary owner,
- one secondary reviewer from another discipline,
- and one integration checkpoint.

This reduces siloed work and late-stage incompatibility.

## 6. Practical Advice

The biggest execution mistake would be spending too long polishing models before confirming that the airbrake can create the required drag change and that the embedded stack can run the loop on time.

## See Also

- [Deliverables and Expected Outcomes](Deliverables-and-Expected-Outcomes.md)
- [Risks, Mitigations, and Safety](Risks-Mitigations-and-Safety.md)
- [Simulation and Dataset Pipeline](../06_Simulation/Simulation-and-Dataset-Pipeline.md)