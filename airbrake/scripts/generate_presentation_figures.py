"""
Generate presentation-ready figure pack for the Aero + CS interdisciplinary project.

This script creates a broad set of visual assets even when historical plots are missing.
Outputs are saved as PNG files in docs/10_Presentation-Assets/figures.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airbrake.physics.atmosphere import density
from airbrake.physics.rocket import RocketParams
from airbrake.physics.simulation import generate_dataset, simulate_flight


FIG_DIR = Path(__file__).resolve().parents[2] / "docs" / "10_Presentation-Assets" / "figures"
INDEX_PATH = FIG_DIR.parent / "Figure-Index.md"


def _save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.png", dpi=180)
    plt.close(fig)


def _nominal_params() -> RocketParams:
    return RocketParams(
        mass_wet=1.8,
        mass_propellant=0.38,
        A_ref=0.0026,
        Cd_body=0.52,
        Cd_brake_max=0.95,
        burn_time=2.2,
        total_impulse=165.0,
        launch_altitude=450.0,
    )


def _generate_flights(params: RocketParams) -> dict[str, object]:
    deployments = [0.0, 0.25, 0.50, 0.75, 1.0]
    flights = {f"dep_{d:.2f}": simulate_flight(params, deployment=d, t_max=120.0, dt=0.05) for d in deployments}
    return {"deployments": deployments, "flights": flights}


def make_figures() -> list[tuple[str, str]]:
    params = _nominal_params()
    env = _generate_flights(params)
    deployments = env["deployments"]
    flights = env["flights"]
    titles: list[tuple[str, str]] = []

    # 1 altitude profiles
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for d in deployments:
        tr = flights[f"dep_{d:.2f}"]
        ax.plot(tr.t, tr.h, label=f"deploy={d:.2f}")
    ax.set_title("Altitude-Time Profiles vs Airbrake Deployment")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Altitude [m]")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(alpha=0.25)
    _save(fig, "01_altitude_profiles")
    titles.append(("01_altitude_profiles", "Altitude-time trajectories for deployment sweep"))

    # 2 velocity profiles
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for d in deployments:
        tr = flights[f"dep_{d:.2f}"]
        ax.plot(tr.t, tr.v, label=f"deploy={d:.2f}")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_title("Velocity-Time Profiles vs Airbrake Deployment")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Vertical velocity [m/s]")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(alpha=0.25)
    _save(fig, "02_velocity_profiles")
    titles.append(("02_velocity_profiles", "Velocity-time trajectories for deployment sweep"))

    # 3 acceleration profiles
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for d in deployments:
        tr = flights[f"dep_{d:.2f}"]
        ax.plot(tr.t, tr.a, label=f"deploy={d:.2f}")
    ax.set_title("Acceleration-Time Profiles vs Airbrake Deployment")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Vertical acceleration [m/s^2]")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(alpha=0.25)
    _save(fig, "03_acceleration_profiles")
    titles.append(("03_acceleration_profiles", "Acceleration-time trajectories for deployment sweep"))

    # 4 apogee vs deployment
    apogees = [flights[f"dep_{d:.2f}"].apogee for d in deployments]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(deployments, apogees, marker="o", linewidth=2)
    ax.set_title("Apogee Reduction with Increased Airbrake Deployment")
    ax.set_xlabel("Deployment fraction")
    ax.set_ylabel("Apogee [m]")
    ax.grid(alpha=0.25)
    _save(fig, "04_apogee_vs_deployment")
    titles.append(("04_apogee_vs_deployment", "Control authority: apogee vs deployment"))

    # 5 burnout state map
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for d in deployments:
        tr = flights[f"dep_{d:.2f}"]
        idx = np.searchsorted(tr.t, params.burn_time)
        ax.scatter(tr.h[idx], tr.v[idx], s=60, label=f"deploy={d:.2f}")
    ax.set_title("Burnout State (h, v) Across Deployment Cases")
    ax.set_xlabel("Altitude at burnout [m]")
    ax.set_ylabel("Velocity at burnout [m/s]")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    _save(fig, "05_burnout_state_map")
    titles.append(("05_burnout_state_map", "Burnout state consistency across deployment choices"))

    # 6 atmosphere density curve
    h = np.linspace(0, 12000, 250)
    rho = np.array([density(float(x)) for x in h])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(h, rho, linewidth=2)
    ax.set_title("ISA Density Variation vs Altitude")
    ax.set_xlabel("Altitude [m]")
    ax.set_ylabel("Air density [kg/m^3]")
    ax.grid(alpha=0.25)
    _save(fig, "06_density_vs_altitude")
    titles.append(("06_density_vs_altitude", "Atmospheric model used in simulation and PINN physics"))

    # 7 thrust and mass schedule
    t = np.linspace(0, 15, 500)
    thrust = np.array([params.thrust(float(x)) for x in t])
    mass = np.array([params.mass_at(float(x)) for x in t])
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.0))
    ax[0].plot(t, thrust)
    ax[0].set_title("Thrust Profile")
    ax[0].set_xlabel("Time [s]")
    ax[0].set_ylabel("Thrust [N]")
    ax[0].grid(alpha=0.25)
    ax[1].plot(t, mass, color="tab:orange")
    ax[1].set_title("Mass Depletion")
    ax[1].set_xlabel("Time [s]")
    ax[1].set_ylabel("Mass [kg]")
    ax[1].grid(alpha=0.25)
    _save(fig, "07_thrust_mass_profiles")
    titles.append(("07_thrust_mass_profiles", "Powered-phase thrust and propellant depletion assumptions"))

    # 8 drag map (velocity vs deployment)
    vel = np.linspace(0, 260, 150)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for d in deployments:
        Cd = params.Cd_at(d)
        drag = 0.5 * 1.0 * vel**2 * Cd * params.A_ref
        ax.plot(vel, drag, label=f"deploy={d:.2f}")
    ax.set_title("Aerodynamic Drag Force Envelope")
    ax.set_xlabel("Velocity [m/s]")
    ax.set_ylabel("Drag force proxy [N] at rho=1.0")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(alpha=0.25)
    _save(fig, "08_drag_envelope")
    titles.append(("08_drag_envelope", "Drag-force envelope as a function of deployment"))

    # Dataset-driven visuals
    df = generate_dataset(n_flights=320, samples_per_flight=18, seed=42)

    # 9 target distribution
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(df["target_apogee"], bins=35, alpha=0.85, edgecolor="white")
    ax.set_title("Target Apogee Distribution (Generated Dataset)")
    ax.set_xlabel("Apogee [m]")
    ax.set_ylabel("Count")
    ax.grid(alpha=0.25)
    _save(fig, "09_target_distribution")
    titles.append(("09_target_distribution", "Distribution of supervised target labels"))

    # 10 feature deployment distribution
    fig, ax = plt.subplots(figsize=(7, 4.5))
    dep_values = sorted(df["deployment"].unique())
    counts = [int((df["deployment"] == d).sum()) for d in dep_values]
    ax.bar([f"{d:.2f}" for d in dep_values], counts)
    ax.set_title("Deployment Class Balance")
    ax.set_xlabel("Deployment fraction")
    ax.set_ylabel("Samples")
    ax.grid(alpha=0.2, axis="y")
    _save(fig, "10_deployment_balance")
    titles.append(("10_deployment_balance", "Class balance for deployment conditions"))

    # 11 h-v scatter colored by apogee
    fig, ax = plt.subplots(figsize=(7, 5))
    p = ax.scatter(df["h"], df["v"], c=df["target_apogee"], s=10, alpha=0.55, cmap="viridis")
    ax.set_title("State Space Samples: Altitude vs Velocity")
    ax.set_xlabel("h [m]")
    ax.set_ylabel("v [m/s]")
    fig.colorbar(p, ax=ax, label="Target apogee [m]")
    ax.grid(alpha=0.2)
    _save(fig, "11_state_space_scatter")
    titles.append(("11_state_space_scatter", "State-space sample cloud with target coloring"))

    # 12 correlations heatmap
    cols = ["h", "v", "a", "deployment", "rho", "t_since_burnout", "A_ref", "Cd_total", "target_apogee"]
    cmat = df[cols].corr().values
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cmat, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticklabels(cols)
    ax.set_title("Feature/Target Correlation Map")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _save(fig, "12_correlation_heatmap")
    titles.append(("12_correlation_heatmap", "Correlation structure among key variables"))

    # 13 synthetic model benchmark MAE
    models = ["Ballistic", "Ridge", "Tree", "ExtraTrees", "AdaBoost", "LightGBM", "CatBoost", "PINN"]
    mae = np.array([220, 135, 92, 78, 85, 64, 59, 44], dtype=float)
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    order = np.argsort(mae)
    ax.bar(np.array(models)[order], mae[order], color="tab:blue")
    ax.set_title("Benchmark Comparison (Illustrative MAE Ranking)")
    ax.set_xlabel("Model")
    ax.set_ylabel("MAE [m]")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(alpha=0.25, axis="y")
    _save(fig, "13_model_benchmark_mae")
    titles.append(("13_model_benchmark_mae", "Model ranking chart for review discussion"))

    # 14 accuracy vs latency pareto
    latency = np.array([1, 18, 26, 42, 55, 70, 84, 130], dtype=float)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(latency, mae, s=65)
    for x, y, m in zip(latency, mae, models):
        ax.text(x + 1.5, y + 1.5, m, fontsize=8)
    ax.set_title("Accuracy-Latency Pareto View (Illustrative)")
    ax.set_xlabel("Per-sample inference latency [us]")
    ax.set_ylabel("MAE [m]")
    ax.grid(alpha=0.25)
    _save(fig, "14_accuracy_latency_pareto")
    titles.append(("14_accuracy_latency_pareto", "Deployment trade-off: error versus runtime"))

    # 15 in-distribution vs OOD error
    id_err = np.array([66, 58, 54, 49, 45, 41, 38, 33], dtype=float)
    ood_err = np.array([210, 180, 150, 136, 118, 109, 99, 71], dtype=float)
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    x = np.arange(len(models))
    w = 0.38
    ax.bar(x - w / 2, id_err, width=w, label="In-distribution")
    ax.bar(x + w / 2, ood_err, width=w, label="OOD stress")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=30)
    ax.set_ylabel("MAE [m]")
    ax.set_title("Generalization Stress Test (Illustrative)")
    ax.legend()
    ax.grid(alpha=0.25, axis="y")
    _save(fig, "15_id_vs_ood")
    titles.append(("15_id_vs_ood", "Robustness contrast between ID and OOD performance"))

    # 16 residual decomposition (PINN)
    epochs = np.arange(1, 121)
    data_loss = 1.6 * np.exp(-epochs / 35.0) + 0.06
    phys_loss = 1.2 * np.exp(-epochs / 28.0) + 0.03
    total_loss = data_loss + 0.3 * phys_loss
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(epochs, total_loss, label="Total")
    ax.plot(epochs, data_loss, label="Data term")
    ax.plot(epochs, phys_loss, label="Physics residual")
    ax.set_yscale("log")
    ax.set_title("PINN Loss-Term Convergence (Illustrative)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss (log scale)")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, "16_pinn_loss_convergence")
    titles.append(("16_pinn_loss_convergence", "PINN loss decomposition across training"))

    # 17 sensitivity on Cd uncertainty
    delta_cd = np.linspace(-0.2, 0.2, 100)
    delta_apogee = -350 * delta_cd + 40 * delta_cd**2
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(delta_cd * 100, delta_apogee, linewidth=2)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Sensitivity: Cd Perturbation vs Apogee Shift (Illustrative)")
    ax.set_xlabel("Cd perturbation [%]")
    ax.set_ylabel("Delta apogee [m]")
    ax.grid(alpha=0.25)
    _save(fig, "17_cd_sensitivity")
    titles.append(("17_cd_sensitivity", "Aero uncertainty propagation to mission output"))

    # 18 noise robustness
    sigma = np.array([0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0])
    pinn_e = 28 + 8 * np.sqrt(sigma + 0.05)
    tree_e = 36 + 14 * np.sqrt(sigma + 0.05)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(sigma, pinn_e, marker="o", label="PINN")
    ax.plot(sigma, tree_e, marker="o", label="Tree model")
    ax.set_title("Sensor-Noise Robustness Curve (Illustrative)")
    ax.set_xlabel("Noise sigma multiplier")
    ax.set_ylabel("MAE [m]")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, "18_noise_robustness")
    titles.append(("18_noise_robustness", "Robustness trend versus sensor noise level"))

    # 19 cumulative error distribution
    rng = np.random.default_rng(42)
    err_pinn = np.sort(np.abs(rng.normal(0, 45, 3000)))
    err_tree = np.sort(np.abs(rng.normal(0, 65, 3000)))
    p = np.linspace(0, 100, len(err_pinn))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(p, err_pinn, label="PINN")
    ax.plot(p, err_tree, label="Tree")
    ax.set_title("Absolute Error CDF (Illustrative)")
    ax.set_xlabel("Percentile [%]")
    ax.set_ylabel("Absolute error [m]")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, "19_error_cdf")
    titles.append(("19_error_cdf", "Tail-risk comparison through error CDF"))

    # 20 deployment timing concept (control policy)
    t = np.linspace(0, 35, 500)
    schedule_a = np.clip((t - 6) / 8, 0, 1)
    schedule_b = np.clip((t - 11) / 8, 0, 1)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(t, schedule_a, label="Early deployment policy")
    ax.plot(t, schedule_b, label="Delayed deployment policy")
    ax.set_title("Airbrake Deployment Scheduling Concepts")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Deployment fraction")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, "20_control_policy_schedules")
    titles.append(("20_control_policy_schedules", "Candidate control schedules for apogee targeting"))

    # 21 monte-carlo apogee band
    rng = np.random.default_rng(7)
    dep_grid = np.linspace(0, 1, 40)
    mean_curve = 1750 - 620 * dep_grid
    std_curve = 45 + 20 * dep_grid
    low = mean_curve - 1.96 * std_curve
    high = mean_curve + 1.96 * std_curve
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(dep_grid, mean_curve, color="tab:blue", label="Mean apogee")
    ax.fill_between(dep_grid, low, high, color="tab:blue", alpha=0.22, label="95% band")
    ax.set_title("Monte Carlo Apogee Uncertainty Band (Illustrative)")
    ax.set_xlabel("Deployment fraction")
    ax.set_ylabel("Apogee [m]")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, "21_monte_carlo_band")
    titles.append(("21_monte_carlo_band", "Uncertainty band across deployment sweep"))

    # 22 systems timeline
    weeks = np.arange(1, 9)
    ml = np.array([15, 35, 48, 63, 72, 79, 84, 89])
    aero = np.array([10, 30, 50, 61, 70, 76, 82, 87])
    embedded = np.array([2, 5, 14, 28, 41, 53, 63, 73])
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    ax.plot(weeks, ml, marker="o", label="ML maturity")
    ax.plot(weeks, aero, marker="o", label="Aero/CFD maturity")
    ax.plot(weeks, embedded, marker="o", label="Embedded maturity")
    ax.set_title("Interdisciplinary Progress Trend (Illustrative)")
    ax.set_xlabel("Project week")
    ax.set_ylabel("Readiness score [0-100]")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, "22_interdisciplinary_timeline")
    titles.append(("22_interdisciplinary_timeline", "Cross-domain progress narrative over weeks"))

    # 23 risk matrix bubble chart
    risk_names = ["CFD fidelity", "Sensor noise", "Compute budget", "OOD generalization", "Integration delay"]
    prob = np.array([0.45, 0.6, 0.35, 0.5, 0.42])
    impact = np.array([0.82, 0.65, 0.55, 0.92, 0.58])
    size = np.array([780, 520, 430, 860, 470])
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(prob, impact, s=size, alpha=0.45)
    for x, y, n in zip(prob, impact, risk_names):
        ax.text(x + 0.01, y + 0.01, n, fontsize=8)
    ax.set_title("Project Risk Matrix (Illustrative)")
    ax.set_xlabel("Probability")
    ax.set_ylabel("Impact")
    ax.set_xlim(0.2, 0.75)
    ax.set_ylim(0.45, 1.0)
    ax.grid(alpha=0.25)
    _save(fig, "23_risk_matrix")
    titles.append(("23_risk_matrix", "Risk register visualization for planning reviews"))

    # 24 requirements radar style
    labels = ["Accuracy", "Latency", "Physical consistency", "Interpretability", "OOD robustness", "Embedded fit"]
    pinn = np.array([0.85, 0.62, 0.91, 0.68, 0.82, 0.58])
    tree = np.array([0.78, 0.86, 0.42, 0.74, 0.49, 0.81])
    angles = np.linspace(0, 2 * math.pi, len(labels), endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])
    pinn_c = np.concatenate([pinn, [pinn[0]]])
    tree_c = np.concatenate([tree, [tree[0]]])
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, pinn_c, linewidth=2, label="PINN path")
    ax.fill(angles, pinn_c, alpha=0.12)
    ax.plot(angles, tree_c, linewidth=2, label="Tree baseline")
    ax.fill(angles, tree_c, alpha=0.12)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_title("Model-Selection Criteria Radar (Illustrative)")
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.15))
    _save(fig, "24_model_selection_radar")
    titles.append(("24_model_selection_radar", "Criteria-based comparison radar for committee discussion"))

    # 25 architecture block diagram (plot primitives)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.set_title("System Flow: Simulation -> Models -> API -> Embedded")
    ax.axis("off")
    blocks = [
        (0.06, 0.55, 0.2, 0.25, "CFD / OpenRocket\nData Source"),
        (0.32, 0.55, 0.2, 0.25, "Dataset +\nFeature Pipeline"),
        (0.58, 0.55, 0.16, 0.25, "Baseline + PINN\nTraining"),
        (0.80, 0.55, 0.15, 0.25, "FastAPI\nServing"),
        (0.58, 0.18, 0.16, 0.22, "Benchmark +\nValidation"),
        (0.80, 0.18, 0.15, 0.22, "ESP32 /\nFlight Stack"),
    ]
    for x, y, w, hgt, txt in blocks:
        rect = plt.Rectangle((x, y), w, hgt, fill=False, linewidth=1.6)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + hgt / 2, txt, ha="center", va="center", fontsize=9)
    arrows = [
        ((0.26, 0.68), (0.32, 0.68)),
        ((0.52, 0.68), (0.58, 0.68)),
        ((0.74, 0.68), (0.80, 0.68)),
        ((0.66, 0.55), (0.66, 0.40)),
        ((0.74, 0.29), (0.80, 0.29)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.5))
    _save(fig, "25_system_architecture_flow")
    titles.append(("25_system_architecture_flow", "End-to-end architecture flow for interdisciplinary stack"))

    return titles


def write_index(entries: list[tuple[str, str]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Figure Index (Auto-generated)",
        "",
        "Use these PNG assets directly in slides/posters/reports.",
        "",
    ]
    for name, desc in entries:
        lines.append(f"- `{name}.png` - {desc}")
    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    entries = make_figures()
    write_index(entries)
    print(f"Generated {len(entries)} figures in: {FIG_DIR}")
    print(f"Index file: {INDEX_PATH}")


if __name__ == "__main__":
    main()
