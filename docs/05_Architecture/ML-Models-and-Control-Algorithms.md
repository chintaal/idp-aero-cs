---
title: ML Models and Control Algorithms
tags:
  - machine-learning
  - control
  - state-estimation
  - model-selection
---

# ML Models and Control Algorithms

## 1. Why This Note Exists

The original concept note listed several machine-learning methods, estimation methods, and control algorithms in slide form. This page reorganizes them into an engineering note that makes model selection easier for the active airbrake system.

The key point is that these methods do not all solve the same problem. Some are meant to predict apogee, some estimate the rocket state from noisy sensors, some support validation under uncertainty, and some directly compute control actions.

## 2. Use the Methods by Role

### 2.1 Prediction and Surrogate Modeling

These methods are candidates for mapping the current flight state to a future quantity such as final apogee or apogee error:

- Physics-Informed Neural Networks (PINNs)
- Gaussian Process Regression (GPR)
- CatBoost
- LightGBM
- Decision Tree Regressor
- Extra Trees
- Ridge Regression

### 2.2 State Estimation

This method is used to improve the quality of the flight state before prediction or control:

- Extended Kalman Filter (EKF)

### 2.3 Decision and Control Logic

These methods are useful when the system must choose a deployment action instead of only predicting a value:

- AdaBoost
- Logistic Regression
- Nonlinear Model Predictive Control (NMPC)

### 2.4 Uncertainty and Robustness Evaluation

This method is not a predictor for deployment by itself, but it is critical for evaluating controller reliability:

- Monte Carlo Trajectory Dispersion Modelling

## 3. At-a-Glance Comparison

| Method | Primary role | Main strength | Main limitation | Embedded suitability | Recommendation |
| --- | --- | --- | --- | --- | --- |
| PINNs | Physics-aware regression | Preserves physical consistency | Higher training complexity | Medium | Stretch goal |
| GPR | Probabilistic regression | Uncertainty estimation | Inference can scale poorly | Low to medium | Research option |
| EKF | State estimation | Robust sensor fusion | Needs careful model tuning | High | Strong candidate |
| AdaBoost | Classification or regression baseline | Handles structured tabular data well | Can be sensitive to noise and model setup | Medium | Secondary baseline |
| CatBoost | Tabular regression | Strong performance with limited tuning | Embedded deployment path may be less direct | Medium | Strong offline benchmark |
| LightGBM | Tabular regression | Fast training and good accuracy on tabular data | Less interpretable than simple baselines | Medium | Strong offline benchmark |
| Decision Tree Regressor | Interpretable regression baseline | Simple and explainable | Overfits easily | High | Basic baseline |
| Extra Trees | Ensemble regression baseline | Good robustness and fast training | Larger ensemble footprint | Medium | Good comparison model |
| Logistic Regression | Binary decision model | Simple and efficient | Not suitable for direct apogee regression | High | Only for deploy or no-deploy logic |
| Ridge Regression | Linear regression baseline | Stable and lightweight | Misses strong nonlinear effects | High | Must-have baseline |
| Monte Carlo Dispersion | Validation and uncertainty study | Quantifies robustness across uncertainties | Not a direct onboard controller | Offline only | Required for validation |
| NMPC | Advanced control | Optimizes action over a prediction horizon | Heavy computational cost | Low to medium | Advanced extension |

## 4. Detailed Notes by Method

### 4.1 Physics-Informed Neural Networks (PINNs)

**What it is:** A neural network that includes governing physics in the training objective instead of learning only from data.

**How it works here:** The loss function can penalize violations of drag-force and vertical-motion relationships while the network learns the mapping from altitude, velocity, deployment angle, and environmental conditions to future apogee.

**Why it is attractive:**

- reduces dependence on very large datasets,
- keeps predictions closer to physically plausible behavior,
- and fits a flight-dynamics problem better than a purely black-box model.

**What to watch:** PINNs are harder to train and justify than simpler baselines. They make more sense after the team has a good simulator and a clean baseline predictor.

**Best use in this project:** A research-grade extension after a simpler surrogate model is already working.

### 4.2 Gaussian Process Regression (GPR)

**What it is:** A probabilistic regression model that predicts both an output value and its uncertainty.

**How it works here:** It models covariance across flight states so the system can estimate final apogee while also reporting confidence.

**Why it is attractive:**

- performs well on smaller datasets,
- gives uncertainty bounds that are useful for safety-aware deployment,
- and can serve as a high-quality surrogate in offline studies.

**What to watch:** Standard GPR becomes expensive as the dataset grows, which makes it less attractive for direct onboard inference.

**Best use in this project:** Offline benchmarking, uncertainty studies, or reduced-size datasets.

### 4.3 Extended Kalman Filter (EKF)

**What it is:** A nonlinear state estimator for combining a flight model with noisy sensor measurements.

**How it works here:** The EKF predicts the next rocket state, linearizes around the current estimate, and then corrects that estimate using IMU and barometric data.

**Why it is attractive:**

- improves reliability of altitude and velocity estimates,
- supports real-time correction of noisy measurements,
- and provides a cleaner input to the apogee predictor.

**What to watch:** Performance depends on model quality, covariance tuning, and sensor calibration.

**Best use in this project:** A primary state-estimation layer ahead of any predictive model.

### 4.4 AdaBoost

**What it is:** An ensemble method that combines many weak learners into a stronger model.

**How it works here:** It can be used either as a regressor for apogee prediction or as a classifier for deployment decisions, depending on how the target is defined.

**Why it is attractive:**

- provides a useful structured-data baseline,
- can focus on hard-to-predict cases,
- and is simpler to explain than deeper models.

**What to watch:** It is not the most natural first choice for noisy aerospace regression unless it clearly outperforms simpler baselines.

**Best use in this project:** Secondary comparison model rather than the lead candidate.

### 4.5 CatBoost

**What it is:** A gradient-boosting method that performs strongly on structured tabular datasets.

**How it works here:** It can learn the mapping from current state variables and deployment conditions to final apogee without large feature-engineering effort.

**Why it is attractive:**

- strong performance with modest tuning,
- robust regularization,
- and effective handling of complex interactions in simulation-generated data.

**What to watch:** Deployment onto constrained hardware is possible, but the toolchain is usually less clean than for a very small neural network or a simple linear model.

**Best use in this project:** One of the strongest offline benchmark models.

### 4.6 LightGBM

**What it is:** A highly efficient gradient-boosting framework for large tabular datasets.

**How it works here:** It trains quickly on simulation sweeps and captures nonlinear relationships among altitude, velocity, atmosphere, and flap settings.

**Why it is attractive:**

- fast training,
- strong predictive accuracy on tabular data,
- and efficient handling of large synthetic datasets.

**What to watch:** It still requires export and deployment care if the final controller is running on a microcontroller.

**Best use in this project:** Top-tier benchmark for simulated apogee prediction.

### 4.7 Decision Tree Regressor

**What it is:** A simple tree model that predicts a continuous value through threshold-based splits.

**How it works here:** It partitions the flight-state space into simple regions and assigns an apogee estimate to each region.

**Why it is attractive:**

- easy to interpret,
- easy to visualize,
- and useful for building intuition about which features matter.

**What to watch:** Single trees can overfit quickly and usually underperform ensemble methods on realistic datasets.

**Best use in this project:** Interpretable baseline only.

### 4.8 Extra Trees

**What it is:** An ensemble of randomized decision trees designed to reduce variance and improve generalization.

**How it works here:** It learns from many randomized trees and averages their regression outputs for a more stable apogee estimate.

**Why it is attractive:**

- often trains quickly,
- is robust to noisy features,
- and provides a strong tree-based benchmark.

**What to watch:** A large ensemble may still be heavier than the final embedded target prefers.

**Best use in this project:** A practical benchmark against LightGBM and CatBoost.

### 4.9 Logistic Regression

**What it is:** A linear classification model for binary outcomes.

**How it works here:** It is useful only if the project defines a classification task such as deploy versus do not deploy, or safe versus unsafe predicted overshoot.

**Why it is attractive:**

- extremely simple,
- fast to train and deploy,
- and easy to justify as a baseline controller.

**What to watch:** It is not appropriate for direct final-apogee regression.

**Best use in this project:** Simple binary deployment logic, not the primary apogee predictor.

### 4.10 Ridge Regression

**What it is:** Linear regression with L2 regularization.

**How it works here:** It predicts apogee from current state features while penalizing large coefficients, which improves stability when the feature set is noisy or correlated.

**Why it is attractive:**

- lightweight,
- fast,
- and a necessary baseline for showing whether nonlinear models are actually worth the added complexity.

**What to watch:** Rocket flight and drag deployment are nonlinear enough that Ridge Regression will likely be outperformed by stronger models.

**Best use in this project:** Must-have linear baseline.

### 4.11 Monte Carlo Trajectory Dispersion Modelling

**What it is:** A repeated-simulation method for measuring how uncertain parameters affect the flight outcome.

**How it works here:** The simulator runs many flights with randomized thrust, drag, atmosphere, or sensor variations and then measures the distribution of resulting apogees.

**Why it is attractive:**

- quantifies uncertainty directly,
- validates whether the controller remains reliable off nominal conditions,
- and supports flight-envelope definition.

**What to watch:** This is part of the validation workflow, not a replacement for the onboard prediction model.

**Best use in this project:** Required offline robustness analysis.

### 4.12 Nonlinear Model Predictive Control (NMPC)

**What it is:** An optimization-based controller that repeatedly solves for the best future control action over a moving time horizon.

**How it works here:** At each control step, NMPC predicts future rocket states under candidate airbrake deployments and chooses the command sequence that best meets the target-apogee objective while respecting constraints.

**Why it is attractive:**

- directly handles nonlinear dynamics,
- can incorporate actuator and safety constraints,
- and gives a principled closed-loop control formulation.

**What to watch:** It is computationally demanding and may be too heavy for the first embedded prototype.

**Best use in this project:** Advanced extension after a simpler predictor-plus-policy stack is complete.

## 5. Recommended Shortlist for This Project

If the goal is to finish a strong prototype with defensible engineering tradeoffs, the most practical stack is:

1. **EKF** for filtered state estimation.
2. **Ridge Regression** as the simplest regression baseline.
3. **Decision Tree Regressor** or **Extra Trees** for interpretable nonlinear baselines.
4. **LightGBM** or **CatBoost** as strong tabular-data benchmarks.
5. **Monte Carlo dispersion** for robustness validation.

PINNs, GPR, and NMPC are valuable, but they are best treated as advanced options rather than first-deliverable requirements.

## 6. How to Compare the Models Fairly

The page titled [Metrics, Ablations, and Benchmarks](../07_Experiments/Metrics-Ablations-and-Benchmarks.md) defines the full evaluation plan. For this note, the main comparison criteria are:

- final-apogee prediction error,
- inference latency,
- memory footprint,
- robustness to noisy inputs,
- and ease of embedded deployment.

No accuracy ranking should be claimed until those experiments are actually run on a common dataset split.

## 7. Best Practical Takeaway

For this project, the best first deliverable is not the most advanced algorithm. It is the simplest model stack that can predict apogee accurately enough, run fast enough on embedded hardware, and hold up under uncertainty. That usually means an EKF-backed predictor with strong tabular baselines before attempting physics-informed or optimization-heavy methods.

## See Also

- [Control, AI, and State Estimation](Control-AI-and-State-Estimation.md)
- [Simulation and Dataset Pipeline](../06_Simulation/Simulation-and-Dataset-Pipeline.md)
- [Metrics, Ablations, and Benchmarks](../07_Experiments/Metrics-Ablations-and-Benchmarks.md)
- [References](../09_Appendix/References.md)