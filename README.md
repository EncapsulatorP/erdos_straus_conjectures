# ESC ML Scripts — Erdős–Straus Generalized Conjecture: ML Diagnostics

This repository contains two machine-learning diagnostic tools for studying the **Erdős–Straus Conjecture (ESC)** and its generalization, alongside a cross-domain experiment coupling ESC's multiplicative structure to Goldbach's additive structure.

---

## Background

The **Erdős–Straus Conjecture** states that for every integer n ≥ 2:

```
4/n = 1/a + 1/b + 1/c
```

for some positive integers a, b, c. This is the k=4 case of the **generalized conjecture**:

```
k/n = 1/a + 1/b + 1/c,   k ∈ {4, 5, 6, 7, ...}
```

Despite being verified computationally for very large ranges, no proof exists. The obstruction concentrates on **Mordell hard residues** mod 840 — specifically n ≡ {1, 121, 169, 289, 361, 529} (mod 840), which are quadratic residues that resist easy decomposition.

---

## Scripts

### `esc_goldbach_split_ml.py` — Goldbach / ESC channel split diagnostic

**Question**: Does the multiplicative structure of ESC inversion carry predictive signal for Goldbach partition counts, beyond what Hardy–Littlewood and Ramanujan additive features already provide?

For each even N in [4, N_max], it:
1. Computes the Goldbach fiber: all prime pairs (p, q) with p + q = N
2. Computes ESC inversion statistics over the prime fiber (for each prime p | fiber, runs the gate k/p = 1/(p·m) + ... up to m_limit)
3. Trains two Random Forest regressors on the **residual** (actual count − Hardy–Littlewood estimate):
   - **Model A** — additive-only: Ramanujan sums c_q(N) for q ∈ {3,4,5,7,8,11,13,16,30,210,840}, modular residues, log features
   - **Model B** — additive + ESC: Model A features plus ESC inversion aggregates (first_m statistics, density, hard-residue rates, min-mod-gap)

Negative Δ(RMSE, MAE) means Model B outperforms Model A — ESC is carrying extra signal.

**Run:**
```
python esc_goldbach_split_ml.py --n-max 20000 --esc-m 64 --outdir results_split
```

**Outputs:**
- `results_split/goldbach_split_dataset.csv` — one row per even N, all 58 features
- `results_split/goldbach_split_report.json` — held-out metrics and top feature importances
- `results_split/feature_importance_all.csv` — full ranked feature importance table
- `results_split/holdout_predictions.csv` — test-set predictions

---

### `remainder_compression_ml.py` — Egyptian-fraction 3-term compression gate

**Question**: For the generalized numerator overflow (k > 3 slots), which (k, n) pairs can be compressed to exactly 3 unit fractions via the restricted gate?

**Gate definition**: For each pair (k, n), search m ≤ m_limit such that:

```
k/n = 1/(n·m) + 1/b + 1/c
```

This uses the divisor identity: let A = k·m − 1, B = n·m. Then:

```
(A·b − B)(A·c − B) = B²
```

A 3-term solution exists iff B² has a factorization consistent with positive integer b, c. The gate is intentionally restricted (first denominator fixed to n·m) to give a clean, reproducible obstruction structure comparable across k values.

For each (k, n) with k ∈ {4,5,6,7} and n ≤ N_max, it trains:
- **Classifier**: `solved_within_gate` — binary, was a solution found?
- **Regressor**: `log_first_m` — magnitude of the smallest successful m

**Run:**
```
python remainder_compression_ml.py --n-max 5000 --k-values 4 5 6 7 --m-limit 128 --outdir results_remainder
```

**Outputs:**
- `results_remainder/remainder_dataset.csv` — one row per (k, n) pair
- `results_remainder/remainder_report.json` — classifier and regressor metrics
- `results_remainder/feature_importance_classifier.csv` — feature importances for the classifier

---

## Repository Structure

```
esc_ml_scripts/
├── esc_goldbach_split_ml.py       # Goldbach / ESC channel split experiment
├── remainder_compression_ml.py    # Egyptian-fraction compression gate experiment
├── erdos_compression.pdf          # Background paper on ESC compression
├── results_split/                 # Outputs from esc_goldbach_split_ml.py
│   ├── goldbach_split_dataset.csv
│   ├── goldbach_split_report.json
│   ├── feature_importance_all.csv
│   └── holdout_predictions.csv
└── results_remainder/             # Outputs from remainder_compression_ml.py
```

---

## Dependencies

```
numpy
pandas
scikit-learn
```

Install with:
```
pip install numpy pandas scikit-learn
```

---

## Interpretation Caveat

These are **diagnostic tools, not proof engines**. A positive result (ESC features improve held-out prediction) means the ESC channel leaks extra information about the Goldbach structure — it is a signal worth studying further. It is not evidence of a theoretical connection without additional analysis.
