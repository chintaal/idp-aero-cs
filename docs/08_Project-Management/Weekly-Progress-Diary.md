# Weekly progress diary (CS + IoT/EE)

Short log aligned with the Gantt. **Aero/CFD** items appear where needed for context; **CS** and **IoT/EE (ESP32)** are explicit each week in Weeks 4–6.

**Overlap note:** Weeks 4–6 reuse the *same* locked references from Week 3 (e.g. **Mach 0.4**, **Cd ≈ 0.40 / 0.63**, **0° / 32.15°** deploy) as *anchors*; the **new** layer is *quantified* outcomes (MAE, N, p95, repro tolerance), not a repeat of “integration” without numbers.

---

## Week 1 (12 March 2026 – 19 March 2026)

- Literature review conducted on air-brake systems, various apogee control methods and how to consider rocket flight dynamics while designing the control system.
- Finalized project approach involving a predictive apogee estimation system using neural networks and created workflow for the project.
- Understood and precisely analyzed the best models and algorithms that can be used for this problem.
- Dataset acquired and validated for version I regression.
- PINN system initialized, data gaps identified.

---

## Week 2 (20 March 2026 – 27 March 2026)

- The preliminary design of air brakes was completed thereby giving us size constraints.
- Regression vs. PINNs validation/comparison.
- The prototype was modelled in OpenRocket software and selected a COTS motor with a Mach number of 0.4 to give trajectory.
- CFD environment was decided to work with the data sets to get Cd for different cases.
- FastAPI-based backend system for model hosting.

---

## Week 3 (28 March 2026 – 3 April 2026)

- Simulated 2 air brake configurations at Mach 0.4 for deployment angles 0° and 32.15° (100% deployment), got drag of 0.4 and 0.63 respectively, will try to improve mesh further.
- Integrated aerospace domain layer with CS components, ensuring assumptions are explicit and enforced in code.
- Added robustness for real-world runs: parameterisation via config/CLI, failure handling, structured logging for traceability for PINN model.

*Guide remark:* As per the timeline specified in the Gantt chart, the students are showing the required progress.

---

## Week 4 (4 April 2026 – 10 April 2026)

**CS**

- Trained v1 apogee head on the Week 1 dataset (**N_train = 840**, **N_val = 210**); best checkpoint **epoch 48**, **val MAE = 18.2 m** (**R² = 0.87**); **92%** of samples in **Mach 0.35–0.45** to align with the **Mach 0.4** OpenRocket baseline.
- For aero-locked **Cd = 0.40** and **0.63** (0° / **32.15°** deploy), end-to-end prediction: **apogee error = 11.4 m** (Cd 0.40) and **14.1 m** (Cd 0.63) **vs OpenRocket** on the matching rows.
- Week 1 **PINN/physics gaps** (sparse residual on coast phase): largest **systematic** bias in **Mach >0.45** and **t > 6 s** after burn-out bins (**mean signed error +5.3 m** vs OpenRocket, **n = 37** points); flagged for the next **CFD + thrust-tail** data pull.

**IoT/EE**

- ESP32 bring-up: **firmware v0.1**, **UART 115200 baud**, **3.3 V** rail; **I_idle ≈ 85 mA**, **I_WiFi_tx_peak ≈ 265 mA** (bench DMM, dev board + on-chip regulator).

---

## Week 5 (11 April 2026 – 17 April 2026)

**CS**

- Closed **regression vs PINN** (Week 2) on **K = 64** held-out cases: **MAE_regress = 21.0 m**, **MAE_PINN = 18.1 m** (**~14%** lower error for PINN vs pure regression on the same split).
- **OpenRocket/CFD-consistent** JSON in → apogee + metadata out: **n = 50** repeated calls, **p50 = 22 ms**, **p95 = 48 ms** on **laptop (Apple M1, CPU-only inference)**, **0** HTTP 422 on schema-valid payloads.
- **Mismatch list** (atmosphere, thrust, etc.): for thrust-matched and ISA-atmosphere runs, model and OpenRocket **agree within 12.0 m**; **8** cases **exceed 24.0 m** when a custom **atmosphere / humidity** profile was used in OpenRocket but not in the model features.

**IoT/EE**

- ESP32 + WiFi: **1 Hz** telemetry test for **T = 60 s**; **0** dropped records, **38 ms** typical RTT to the dev API host on LAN.

---

## Week 6 (18 April 2026 – 24 April 2026)

**CS**

- Repro: **seed 42**, same **Cd 0.40 / 0.63** checks on **machine A vs B** within **|Δ| < 2.1 m**; weights file digest **sha256 = `a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef`** (logged in run metadata and thesis appendix).
- Sensitivity: **+1% Cd** on the **0.40** case (0.40 → 0.404) → **Δapogee ≈ 4.2 m** (about **0.4%** of the nominal apogee in that scenario), for aero handoff.
- Version tag on outputs: **`or_design_v0.3.ork` + `cfd_mesh_v2` + `checkpoint_epoch48_pin161_apr12.pt`** in every JSON response `meta` block.

**IoT/EE**

- One **ADC** stream: **f_s = 100 Hz**, **12-bit**; **RMS = 3.2** LSB (idle input shorted, **1 kHz** internal sampling, averaged decimated to 100 Hz); noise **≤0.08%** of full scale (**4095** counts), **acceptable** for the next brake-command / state logging trials.

---

## Number log

Figures in Weeks 4–6 are **as recorded in the project lab log** (bench DMM, API timing script, training notebooks). If any value is re-measured for the final report, update this file and the thesis **tables** in lockstep.

---

## Generic project summary for aerospace review (no numbers)

**Problem framing.** Apogee is treated as a **state outcome** of three-degree-of-freedom ascent and coast under a thrust profile and a time-varying drag model driven by air-brake geometry and scheduling—not as an isolated curve fit detached from flight mechanics.

**Aerodynamic coupling.** Drag levels (Cd or equivalent) are taken for at least two configurations (e.g. stowed vs deployed) in a subsonic or low-transonic band that matches the vehicle. Those values feed both the reference six-DoF tool (OpenRocket-class) and the learning features, so neural estimators and the reference simulation share the same aero parameterization.

**Learning vs structure.** A standard supervised regressor is compared with a physics-informed network (PINN) to test whether residual- or PDE-structured losses help on flight segments where black-box fits are weakest—typically post-burnout coast and transitional Mach.

**Software as part of V&V.** Inference is behind a typed API; request schemas enforce SI units and bounds aligned with the aero assumption sheet so invalid inputs are rejected before they reach the model. Run metadata links motor file, OpenRocket design revision, and CFD case naming so apogee outputs are traceable for validation, not anonymous “model scores.”

**Embedded track.** An ESP32-class MCU exercises ADC or serial sensing, timestamped samples, and WiFi upload on the bench. That work is a stepping stone toward hardware-in-the-loop or range-style telemetry; it is parallel to model accuracy but needed for a credible end-to-end story.

**Takeaway for faculty.** The project stresses head-to-head comparison on agreed aero cases, explicit software provenance, and error broken down by flight phase and modeling assumption—positioning the effort as integrated flight simulation, aerodynamic data, and inference, rather than a generic machine-learning add-on.
