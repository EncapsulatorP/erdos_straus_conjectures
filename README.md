# Erdős–Straus Conjecture: ML Diagnostics

This repository contains two machine-learning diagnostic tools for studying the **Erdős–Straus Conjecture** and its generalization, alongside a cross-domain experiment coupling the conjecture's multiplicative structure to Goldbach's additive structure.

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
## 1. Core object: the unit-fraction length

 Define the set of values reachable with exactly `t` positive unit fractions:

$$
\mathcal{E}_t \;=\; \left\{\, \sum_{i=1}^{t}\frac{1}{a_i} \;:\; a_i \in \mathbb{Z}_{>0} \,\right\}
$$

(no distinctness requirement; repeats allowed). Then define the **Egyptian compression length**:

$$
\boxed{\,L_{\mathrm{UF}}(x) \;=\; \min\{\, t : x \in \mathcal{E}_t \,\}\,}
$$

Every positive rational has a finite expansion, so $L_{\mathrm{UF}}$ is always defined and finite. The interesting object is therefore **not** infinity but the **bounded-length** question $L_{\mathrm{UF}}(x) \le t$.

For completeness:

$$
\mathcal{E}_* \;=\; \bigcup_{t \ge 1}\mathcal{E}_t \qquad (\text{= all positive rationals, by finiteness of Egyptian expansions})
$$

---

## 2. The conjectures, restated in one line each

| Name | Compact form | Status |
|---|---|---|
| Erdős–Straus | $L_{\mathrm{UF}}(4/n) \le 3$ for all $n \ge 2$ | **open** |
| Sierpiński | $L_{\mathrm{UF}}(5/n) \le 3$ for all $n \ge 2$ | **open** |
| Schinzel (general) | $L_{\mathrm{UF}}(k/n) \le 3$ for all $n$ large enough (given $k$) | **open** |
| 3-slot problem | $L_{\mathrm{UF}}(k/n) \le 3$ | family of hard Diophantine cases |

Note the structural point: **the number of slots is fixed at 3.** What moves across these conjectures is the numerator $k$, not the slot count. So $4 = 3 + 1$ is *not* a moving identity $k = t+1$ — Sierpiński keeps $t = 3$ and takes $k = 5$.

---

## 3. Why $k = t+1$ is the threshold of first difficulty

The intuition "$k = t+1$" is correct as the **first hard numerator** for a given slot count $t$, and this is exactly why $4/n$ (at $t=3$) is the canonical case.

Fix $t$ slots. Any numerator $k \le t$ is **trivial**, because the unary default already fits:

$$
\frac{k}{n} \;=\; \underbrace{\frac1n + \frac1n + \cdots + \frac1n}_{k\text{ copies}} \;\in\; \mathcal{E}_k \subseteq \mathcal{E}_t \qquad (k \le t).
$$

So for $t = 3$:

- $1/n,\ 2/n,\ 3/n$ are all trivial. In particular $3/n = 1/n + 1/n + 1/n$ uses exactly the 3 slots with nothing to spare.
- $4/n$ is the **first numerator whose unary default overflows** — it wants 4 slots, only 3 are available. First case requiring genuine recombination, not just copying.

Threshold pattern, and how the outcome depends on $t$:

- $t = 2$: threshold $k = 3$ is already **false** — e.g. $3/7$ has no two-term unit-fraction representation.
- $t = 3$: threshold $k = 4$ is **open** (conjecturally true) — Erdős–Straus.

So $k = t+1$ is the first overflow at every $t$; what changes is whether it holds.


## Scripts

### `esc_goldbach_split_ml.py` — Goldbach / Erdős–Straus channel split diagnostic

**Question**: Does the multiplicative structure of Erdős–Straus inversion carry predictive signal for Goldbach partition counts, beyond what Hardy–Littlewood and Ramanujan additive features already provide?

For each even N in [4, N_max], it:
1. Computes the Goldbach fiber: all prime pairs (p, q) with p + q = N
2. Computes Erdős–Straus inversion statistics over the prime fiber (for each prime p | fiber, runs the gate k/p = 1/(p·m) + ... up to m_limit)
3. Trains two Random Forest regressors on the **residual** (actual count − Hardy–Littlewood estimate):
   - **Model A** — additive-only: Ramanujan sums c_q(N) for q ∈ {3,4,5,7,8,11,13,16,30,210,840}, modular residues, log features
   - **Model B** — additive + Erdős–Straus: Model A features plus Erdős–Straus inversion aggregates (first_m statistics, density, hard-residue rates, min-mod-gap)

Negative Δ(RMSE, MAE) means Model B outperforms Model A — the Erdős–Straus channel is carrying extra signal.

**Run:**
```
python esc_goldbach_split_ml.py --n-max 20000 --es-m 64 --outdir results_split
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
├── esc_goldbach_split_ml.py       # Goldbach / Erdős–Straus channel split experiment
├── remainder_compression_ml.py    # Egyptian-fraction compression gate experiment
├── erdos_compression.pdf          # Background paper on Erdős–Straus compression
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

These are **diagnostic tools, not proof engines**. A positive result (Erdős–Straus features improve held-out prediction) means the Erdős–Straus channel leaks extra information about the Goldbach structure — it is a signal worth studying further. It is not evidence of a theoretical connection without additional analysis.
