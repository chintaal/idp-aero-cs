# Weekly project report (generic)

Use this for **formal** weekly submissions to a guide or program office. It stays **high level**; put **measured** figures, file names, and day-by-day notes in [`Weekly-Progress-Diary.md`](./Weekly-Progress-Diary.md) instead.

**Reporting period:** [start date] — [end date]  
**Project:** Predictive apogee estimation for a rocket with deployable air brakes; hybrid **aerospace simulation**, **machine learning**, and **embedded** telemetry path.

---

## 1. Summary

In one short paragraph, state what the team set out to do this week and whether the **Gantt** milestone for this slot is **met**, **partially met**, or **at risk** (and why in one line).

*Example (replace with your text):* Work continued on linking trajectory reference runs to data-driven apogee models, hardening the inference API, and bench-level MCU bring-up for future telemetry feeds.

---

## 2. Objectives vs outcomes

| Objective (this week) | Outcome | Notes |
|------------------------|---------|--------|
| e.g. Align CFD / experiment drag with model inputs | | |
| e.g. Train or refine estimator; compare to baseline | | |
| e.g. Stabilize embedded stack + uplink | | |

---

## 3. Workstreams (generic detail)

**Simulation and aerodynamics**  
Progress on 3-DoF or six-DoF trajectory tools (e.g. OpenRocket-class), CFD- or wind-tunnel-derived drag at relevant Mach and deployment states, and clear assumptions for atmosphere, motor, and brake release.

**Learning and software**  
Dataset curation and splits; regression vs physics-aware (e.g. PINN) models; domain-aware validation of API inputs/outputs; hosting and reproducible runs with config, logging, and version tags tied to design revisions.

**Embedded and communications**  
Microcontroller bring-up (e.g. ESP32-class), placeholder or real sensing, timing discipline, power budget, and a wireless path to a dev or test server where applicable.

---

## 4. Risks and mitigations

| Risk | Mitigation / status |
|------|----------------------|
| e.g. Simulation–model feature mismatch | e.g. Shared metadata schema; spot checks on reference cases |
| e.g. Hardware slip vs software | e.g. Decouple bench demo from flight hardware | 

---

## 5. Next reporting period

List three to five concrete intentions (not “continue work”): e.g. close a validation matrix row, freeze a model checkpoint, refine CFD mesh or flight sampling in a named regime, add a HIL-style telemetry string.

---

## 6. For advisor / faculty (optional)

- **Integration angle:** One sentence on how aero data, inference, and embedded work connect this week.  
- **Ethics & safety (if required):** Range rules, static fire / bench safety, or *N/A*.

---

*End of report.*
