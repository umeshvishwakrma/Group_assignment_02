
**Files:** `smart_home_bn.py` (source code), `network.png` (network diagram), `error_plot.png` (error vs dataset size), screenshots of console output.
**Random seed:** 42

---

## Part A: Expert Bayesian Network

**Structure:** W → A, D → O, O → A, O → L, A → E, L → E.
All CPT rows were checked programmatically and sum to 1.

### Query results

| Query | Value |
|---|---|
| Q1 P(E=High) | 0.5806 |
| Q2 P(E=High \| W=Hot) | 0.7063 |
| Q3 P(E=High \| D=Weekend) | 0.6402 |
| Q4 P(E=High \| W=Cold, O=High) | 0.4842 |
| Q5 P(W=Hot \| E=High) | 0.6082 |
| Q6 P(A=On \| E=High) | 0.6929 |
| Q7 P(A=On \| E=High, L=Heavy) | 0.6499 |

### Explaining away (Q6 vs Q7)

Q6 = 0.6929 and Q7 = 0.6499, so the probability that the AC is on falls by about 0.043 once we also know the appliance load is Heavy. AC usage and appliance load are two possible causes of high energy consumption. High energy is evidence for the AC being on, but if heavy appliance load is also known, that already explains much of the high consumption (P(E=High | AC=Off, Heavy) = 0.55). The AC is then less needed as an explanation, so its probability decreases. This is explaining away: observing a common effect makes its causes compete.

### Hand calculation of Q1

P(E=High) = sum over a, l of P(E=High | a, l) · P(a, l), where
P(a, l) = sum over w, d, o of P(w) P(d) P(o|d) P(a|w,o) P(l|o).

First, P(O=High) = 0.7·0.45 + 0.3·0.80 = 0.555 and P(O=Low) = 0.445.
Then P(A=On | O=High) = 0.5·0.9 + 0.3·0.4 + 0.2·0.1 = 0.59, and P(A=On | O=Low) = 0.5·0.6 + 0.3·0.15 + 0.2·0.05 = 0.355.

Example: P(A=On, L=Heavy) = 0.555·0.59·0.75 + 0.445·0.355·0.35 = 0.24559 + 0.05529 = 0.30088.

| A | L | P(A,L) | P(E=High \| A,L) | Product |
|---|---|---|---|---|
| On | Heavy | 0.30088 | 0.92 | 0.27681 |
| On | Light | 0.18455 | 0.68 | 0.12549 |
| Off | Heavy | 0.27112 | 0.55 | 0.14912 |
| Off | Light | 0.24345 | 0.12 | 0.02921 |
| | | | **Sum** | **0.58063** |

Q1 = 0.5806, which matches the code output.

---

## Part B: Conditional Independence

1. **Weather ⊥ DayType: holds.** The only path is W → A ← O ← D. A is a collider and neither A nor its descendant E is observed, so the path is blocked. Check: P(W=Hot) = 0.5000 and P(W=Hot | D=Weekend) = 0.5000.

2. **Weather ⊥ DayType | EnergyConsumption: does not hold.** E is a descendant of the collider A, so observing E opens the path W → A ← O ← D (O is an unobserved chain node, so it passes). Check: P(W=Hot | E=High) = 0.6082, but P(W=Hot | E=High, D=Weekend) = 0.5998. The values differ, so the variables are dependent (the effect is small because DayType affects AC only indirectly through Occupancy).

3. **Weather ⊥ ApplianceLoad | Occupancy: holds.** Path W → A ← O → L is blocked because O is an observed fork node (and A is an unobserved collider). Path W → A → E ← L is blocked at the unobserved collider E. Check: P(W=Hot | O=High) = 0.5000 and P(W=Hot | O=High, L=Heavy) = 0.5000.

---

## Part C: Synthetic Data (ancestral sampling, seed = 42)

Nodes were sampled in topological order W, D, O, A, L, E, each from its CPT row given the parents already sampled.

**Empirical weather frequencies**

| n | Hot | Mild | Cold |
|---|---|---|---|
| 500 | 0.5000 | 0.2780 | 0.2220 |
| 5000 | 0.5020 | 0.2904 | 0.2076 |
| 20000 | 0.5010 | 0.2969 | 0.2021 |

**Sample counts per (Weather, Occupancy)**

| n | Hot,High | Hot,Low | Mild,High | Mild,Low | Cold,High | Cold,Low |
|---|---|---|---|---|---|---|
| 500 | 144 | 106 | 78 | 61 | 56 | 55 |
| 5000 | 1416 | 1094 | 830 | 622 | 559 | 479 |
| 20000 | 5606 | 4415 | 3327 | 2610 | 2222 | 1820 |

The frequencies approach the true priors (0.5, 0.3, 0.2) as n grows.

---

## Part D: Learning from Data

Parameters were learned with MLE and with Bayesian estimation (BDeu prior, equivalent sample size 10) on the expert structure. BDeu pseudo-count per cell = 10 / (q·r), where q = number of parent configurations and r = number of states.

**AC Usage CPT, P(A=On | W, O)**

| W, O | Expert | MLE 500 | BDeu 500 | MLE 5000 | BDeu 5000 | MLE 20000 | BDeu 20000 |
|---|---|---|---|---|---|---|---|
| Hot, High | 0.900 | 0.882 | 0.878 | 0.895 | 0.894 | 0.895 | 0.895 |
| Hot, Low | 0.600 | 0.623 | 0.621 | 0.607 | 0.607 | 0.601 | 0.601 |
| Mild, High | 0.400 | 0.449 | 0.450 | 0.395 | 0.395 | 0.398 | 0.398 |
| Mild, Low | 0.150 | 0.180 | 0.189 | 0.158 | 0.158 | 0.153 | 0.153 |
| Cold, High | 0.100 | 0.054 | 0.066 | 0.095 | 0.096 | 0.103 | 0.103 |
| Cold, Low | 0.050 | 0.018 | 0.032 | 0.054 | 0.056 | 0.055 | 0.055 |

Q1 to Q7 for the learned models are given in the tables of Part E.

---

## Part E: Comparative Analysis

**n = 500**

| Query | Expert | MLE | Bayesian | \|Diff\| MLE | \|Diff\| Bayesian |
|---|---|---|---|---|---|
| Q1 | 0.5806 | 0.5905 | 0.5888 | 0.0099 | 0.0082 |
| Q2 | 0.7063 | 0.7003 | 0.6951 | 0.0060 | 0.0112 |
| Q3 | 0.6402 | 0.6493 | 0.6434 | 0.0091 | 0.0032 |
| Q4 | 0.4842 | 0.5073 | 0.5100 | 0.0230 | 0.0257 |
| Q5 | 0.6082 | 0.5929 | 0.5863 | 0.0153 | 0.0218 |
| Q6 | 0.6929 | 0.6619 | 0.6589 | 0.0310 | 0.0340 |
| Q7 | 0.6499 | 0.6326 | 0.6305 | 0.0173 | 0.0194 |
| **Mean** | | | | **0.01592** | **0.01765** |

**n = 5000**

| Query | Expert | MLE | Bayesian | \|Diff\| MLE | \|Diff\| Bayesian |
|---|---|---|---|---|---|
| Q1 | 0.5806 | 0.5874 | 0.5872 | 0.0067 | 0.0066 |
| Q2 | 0.7063 | 0.7168 | 0.7162 | 0.0105 | 0.0099 |
| Q3 | 0.6402 | 0.6468 | 0.6462 | 0.0066 | 0.0060 |
| Q4 | 0.4842 | 0.4846 | 0.4850 | 0.0004 | 0.0007 |
| Q5 | 0.6082 | 0.6126 | 0.6119 | 0.0044 | 0.0037 |
| Q6 | 0.6929 | 0.6957 | 0.6953 | 0.0028 | 0.0024 |
| Q7 | 0.6499 | 0.6511 | 0.6508 | 0.0012 | 0.0009 |
| **Mean** | | | | **0.00466** | **0.00432** |

**n = 20000**

| Query | Expert | MLE | Bayesian | \|Diff\| MLE | \|Diff\| Bayesian |
|---|---|---|---|---|---|
| Q1 | 0.5806 | 0.5866 | 0.5865 | 0.0059 | 0.0059 |
| Q2 | 0.7063 | 0.7117 | 0.7116 | 0.0055 | 0.0053 |
| Q3 | 0.6402 | 0.6452 | 0.6451 | 0.0050 | 0.0049 |
| Q4 | 0.4842 | 0.4899 | 0.4899 | 0.0056 | 0.0057 |
| Q5 | 0.6082 | 0.6080 | 0.6078 | 0.0002 | 0.0004 |
| Q6 | 0.6929 | 0.6913 | 0.6912 | 0.0016 | 0.0017 |
| Q7 | 0.6499 | 0.6492 | 0.6491 | 0.0007 | 0.0008 |
| **Mean** | | | | **0.00351** | **0.00352** |

### 1. Plot
See `error_plot.png` (mean absolute difference over Q1 to Q7 against dataset size, for MLE and Bayesian). Both errors fall as the dataset grows.

### 2. Largest error for the 500-sample dataset
In our run (seed 42) the largest error is **Q6** (|Diff| = 0.0310 for MLE, 0.0340 for Bayesian). Q6 depends on the AC CPT and on every table feeding E, so it is sensitive to poorly estimated AC rows. At n = 500 the Cold rows of the AC table rest on few samples (56 for Cold/High and 55 for Cold/Low), and the learned values (0.054 and 0.018) are far from the true 0.10 and 0.05.
The query whose evidence is rarest is **Q4**, which conditions on Weather = Cold and Occupancy = High, seen in only 56 of 500 samples (about 11%). It has the second largest error (0.0230 MLE, 0.0257 Bayesian). Queries with rare evidence rely on few rows of data, so their estimates vary more. Which query comes out worst depends on the random seed.

### 3. Which estimator is better for small datasets?
In theory, Bayesian estimation is better for small datasets. Its BDeu pseudo-counts pull sparse estimates toward uniform, so it never produces zero probabilities and handles parent configurations that are rare or unseen, where MLE can be extreme or undefined. In our single run, however, the two were close at n = 500, and MLE was slightly lower (mean 0.01592 vs 0.01765). Bayesian was slightly lower at n = 5000 (0.00432 vs 0.00466) and they were equal at n = 20000. This shows the advantage depends on the particular sample: shrinking toward uniform helps when MLE overshoots to extremes but can move estimates away from true small probabilities such as 0.05. As data grows, the prior's weight (10 pseudo-samples) becomes negligible and both estimators converge to the expert model. Averaging over several seeds would give a more reliable comparison.

