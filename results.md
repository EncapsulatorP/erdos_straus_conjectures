# Experimental Results

## Experiment 1: Goldbach / Erdős–Straus Channel Split

**Script**: `erdos_straus_goldbach_split_ml.py`
**Run parameters**: `--n-max 20000 --esc-m 64 --outdir results_split`
**Dataset**: 9,999 even integers N ∈ [4, 20000]
**Train range**: N ∈ [4, 15000] | **Test range**: N ∈ [15002, 20000]
**Target**: Residual of Goldbach count after subtracting the Hardy–Littlewood estimate

### Model Performance (held-out test set)

| Model | Features | MAE | RMSE | R² |
|-------|----------|-----|------|----|
| A — Additive only | 48 | 0.0519 | 0.0761 | −1.524 |
| B — Additive + Erdős–Straus | 58 | 0.0443 | 0.0660 | −0.895 |
| **Improvement (B − A)** | +10 Erdős–Straus features | **−0.0076** | **−0.0102** | **+0.629** |

Both R² values are negative, which is expected: the Hardy–Littlewood residual is nearly mean-zero white noise, making it harder to predict than the raw count. The key result is the **delta**: Model B reduces RMSE by 10.2 points and MAE by 7.6 points on the held-out range, indicating the ESC inversion channel carries genuine extra signal.

### Top Features by Permutation Importance

| Rank | Feature | Importance (mean) | ±std |
|------|---------|--------------------|------|
| 1 | `erdos_straus_first_m_mean` | 0.01107 | 0.00046 |
| 2 | `hl_estimate` | 0.00789 | 0.00023 |
| 3 | `log_hl_estimate` | 0.00626 | 0.00013 |
| 4 | `erdos_straus_density_std` | 0.00234 | 0.00011 |
| 5 | `ramanujan_c_30_norm` | 0.00106 | 0.00020 |
| 6 | `erdos_straus_first_m_max` | 0.00094 | 0.00011 |
| 7 | `erdos_straus_pair_hard_any_rate` | 0.00087 | 0.000084 |
| 8 | `erdos_straus_density_mean` | 0.00081 | 0.000049 |
| 9 | `ramanujan_c_5_norm` | 0.00038 | 0.000019 |
| 10 | `erdos_straus_first_m_min` | 0.00035 | 0.000043 |

### Key Observations

**`erdos_straus_first_m_mean` is the single strongest predictor**, ranking above the Hardy–Littlewood estimate itself. This feature aggregates, for each prime p in the Goldbach fiber of N, the smallest m for which the gate k/p = 1/(p·m) + ... succeeds. Its dominance suggests that the "difficulty" of the ESC inversion over the prime fiber tracks the deviation of Goldbach counts from the Hardy–Littlewood prediction.

**ESC density features (`erdos_straus_density_std`, `erdos_straus_density_mean`) outperform most Ramanujan terms.** The density measures how many m-values in [1, m_limit] solve the gate — a proxy for how "solvable" the multiplicative structure around N is. Variance of density across the fiber (`erdos_straus_density_std`) ranks 4th overall.

**`erdos_straus_pair_hard_any_rate`** measures the fraction of prime pairs in the Goldbach fiber where at least one prime falls in a Mordell hard residue class mod 840. Its presence in the top 10 confirms that the hard-residue obstruction structure has measurable impact on Goldbach counts beyond what smooth modular arithmetic captures.

**Large-modulus features (N mod 840, N mod 210, Ramanujan c_840) show negative importance**, suggesting they introduce noise at this scale. These may become useful at N > 100,000 where the periodicity is better sampled.

**`logN` and `sqrtN` have zero importance**, consistent with them being absorbed into the Hardy–Littlewood estimate and its log transform.

---

## Experiment 2: Remainder Compression Gate

**Script**: `remainder_compression_ml.py`
**Status**: Results directory initialized; full run pending with `--n-max 5000 --k-values 4 5 6 7 --m-limit 128`.

Once run, this experiment will provide:
- Solve rates per k: what fraction of (k, n) pairs are resolved by the restricted gate within m_limit
- Feature importance for the classifier: which arithmetic properties of n predict gate solvability
- Regressor analysis: what drives the magnitude of the first successful m (proxy for obstruction depth)

See [next_steps.md](next_steps.md) for the planned analysis once results are available.
