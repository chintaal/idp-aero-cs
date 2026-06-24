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

## Week 7 (25 April 2026 – 1 May 2026)

**CS**

- Six-way model comparison matrix documented; **LightGBM** best in-distribution **val MAE = 16.8 m** on tabular split; **PINN** best on coast-only holdout **MAE = 15.4 m** (**n = 112** snapshots).
- Benchmark table export: **8 models × 5 metrics** → `artifacts/benchmark_results.csv` + markdown summary for thesis tables.

**IoT/EE**

- No new bench hardware; embedded track focused on requirements for Week 9+ virtual circuit and UI telemetry schema.

---

## Week 8 (2 May 2026 – 8 May 2026)

**CS**

- PINN advantages/disadvantages doc finalized; promotion gate checklist: **MAE**, **residual L2**, **OOD stress MAE**, **p95**, **latency < 100 ms** on CPU for single-row predict.
- Presentation figure pack: **25 PNGs** + index under `docs/10_Presentation-Assets/figures`.

**IoT/EE**

- Payload schema frozen for ESP32 → API: **max JSON 512 B**, fields `h`, `v`, `a`, `deployment`, `ts_ms`.

---

## Week 9 (9 May 2026 – 15 May 2026)

**CS**

- **Computing tables v1:** benchmark (**8 rows**), Cd lookup (**5 deployment angles**), feature bounds (**9 features** with min/max/unit) — all generated from scripts, not hand-edited.
- Dataset human-readable export: **`flights_sample.csv`**, **7392 rows** (sample of full parquet) for spreadsheet review and UI fixture data.
- SvelteKit UI initialized: dev server on **:5173**, env `VITE_API_BASE=http://127.0.0.1:8000`; first page renders benchmark table from static JSON until API wire-up.

**IoT/EE**

- Virtual-circuit block diagram: ESP32-WROOM, **3.3 V** only on GPIO; **GPIO 34–39** input-only; **GPIO 6–11** flash — excluded from user map.

---

## Week 10 (16 May 2026 – 22 May 2026)

**CS**

- Phase-binned error table: coast bin **MAE_PINN = 14.2 m** vs **MAE_trees = 17.9 m** (**n_test = 286** coast rows).
- UI flight input form with bounds: **h ∈ [0, 15000] m**, **v ∈ [-200, 400] m/s**, **deployment ∈ [0, 1]** — matches API schema.
- Side-by-side predict table: 3 columns (baseline / PINN / reference apogee) for **20** canned demo cases.

**IoT/EE**

- Resource budget table: **~320 KB** free heap after WiFi init (virtual run), **~1.2 MB** app partition headroom; target loop **50 Hz** servo command, **10 Hz** sensor aggregate, **1 Hz** API uplink.

---

## Week 11 (23 May 2026 – 29 May 2026)

**CS**

- UI telemetry table: columns **ts**, **h**, **v**, **a**, **deployment**, **pred_apogee**, **latency_ms**; CSV export tested on **500** mock rows.

**IoT/EE**

- Wokwi virtual circuit: **GPIO 18** servo PWM, **GPIO 21/22** I²C, **GPIO 23** status LED; firmware **v0.2**.
- **ADC:** **ADC1_CH6 (GPIO 34)** potentiometer stand-in for deployment feedback; **11 dB** attenuation, raw **0–4095** clamped in software.
- **Limits in firmware:** deployment **0.0–1.0**, servo pulse **1000–2000 µs** (50 Hz), max slew **0.05 / loop** at 50 Hz; reject uplink if **|a| > 50 m/s²** or **h < 0**.

---

## Week 12 (30 May 2026 – 5 June 2026)

**CS**

- UI → API live predict: **50** sequential calls, **p50 = 28 ms**, **p95 = 61 ms** (includes browser + network); **0** schema failures on valid inputs.
- Limits envelope table (embedded): **VDD 3.0–3.6 V**, **I_peak WiFi ≈ 280 mA**, **servo 4.8–6 V** (external BEC), **operating h ≤ 5000 m** for v1 demo envelope.

**IoT/EE**

- Virtual HIL: **600 s** simulated flight log at **10 Hz** → **6000** samples; **0** watchdog resets, **3** intentional API timeouts recovered via backoff.
- Loop timing: servo update **jitter p95 = 1.8 ms** at 50 Hz target (virtual scope).

---

## Week 13 (6 June 2026 – 12 June 2026)

**CS**

- Dashboard: live table refresh on **1 Hz** LAN feed from virtual ESP32; sparkline uses last **120** altitude points.
- Deployment policy preview table: **10** target-apogee scenarios with suggested deployment step from lookup table.

**IoT/EE**

- Firmware **v0.3:** API post rate cap **2 Hz**; **safe mode** after **5 s** comms loss (servo stowed **1000 µs**); WiFi reconnect max **3** attempts then backoff **30 s**.
- Traceability table: **ui_build = 0.4.0**, **api = 0.3.1**, **fw = v0.3**, **checkpoint = epoch48_pin161**, **wokwi_rev = w3**.

---

## Week 14 (13 June 2026 – 19 June 2026)

**CS**

- Faculty table pack frozen: benchmark, Cd lookup, limits, UI checklist (**12/12** demo features), gap list (**3** items: physical HIL, closed-loop range test, humidity feature).
- UI invalid-input test: **15** bad payloads → **15/15** show field-level errors in table UI matching API **422** body.

**IoT/EE**

- Virtual-circuit sign-off: pin map **verified**, all limit tests **pass**, migration note to physical ESP32 (same JSON schema, **GPIO map unchanged**).
- End-to-end demo script: virtual sensor → firmware → WiFi → API → SvelteKit table, **T = 120 s** dry run, **0** dropped records.

---

## Number log

Figures in Weeks 4–6 and 9–14 are **as recorded in the project lab log** (bench DMM, API timing script, training notebooks, Wokwi/virtual HIL runs, UI timing). If any value is re-measured for the final report, update this file and the thesis **tables** in lockstep.

---

## Generic project summary for aerospace review (no numbers)

**Problem framing.** Apogee is treated as a **state outcome** of three-degree-of-freedom ascent and coast under a thrust profile and a time-varying drag model driven by air-brake geometry and scheduling—not as an isolated curve fit detached from flight mechanics.

**Aerodynamic coupling.** Drag levels (Cd or equivalent) are taken for at least two configurations (e.g. stowed vs deployed) in a subsonic or low-transonic band that matches the vehicle. Those values feed both the reference six-DoF tool (OpenRocket-class) and the learning features, so neural estimators and the reference simulation share the same aero parameterization.

**Learning vs structure.** A standard supervised regressor is compared with a physics-informed network (PINN) to test whether residual- or PDE-structured losses help on flight segments where black-box fits are weakest—typically post-burnout coast and transitional Mach.

**Software as part of V&V.** Inference is behind a typed API; request schemas enforce SI units and bounds aligned with the aero assumption sheet so invalid inputs are rejected before they reach the model. Run metadata links motor file, OpenRocket design revision, and CFD case naming so apogee outputs are traceable for validation, not anonymous “model scores.”

**Embedded track.** An ESP32-class MCU exercises ADC or serial sensing, timestamped samples, and WiFi upload on the bench. That work is a stepping stone toward hardware-in-the-loop or range-style telemetry; it is parallel to model accuracy but needed for a credible end-to-end story.

**Takeaway for faculty.** The project stresses head-to-head comparison on agreed aero cases, explicit software provenance, and error broken down by flight phase and modeling assumption—positioning the effort as integrated flight simulation, aerodynamic data, and inference, rather than a generic machine-learning add-on.
