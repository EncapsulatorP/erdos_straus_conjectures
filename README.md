# Generalized Egyptian-Fraction Compression: ML Diagnostics

This repository centers on the generalized 3-slot Egyptian-fraction compression problem

$$
L_{\mathrm{UF}}(k/n) \le 3,
$$

with Erdős-Straus ($k=4$) treated as the canonical first hard case inside that broader family.
It includes two machine-learning diagnostics: one on generalized compression gates, and one
cross-domain channel comparison against Goldbach structure.

---

## Background

The **Erdős-Straus Conjecture** states that for every integer $n \ge 2$:

```
4/n = 1/a + 1/b + 1/c
```

for some positive integers $a,b,c$. This is the $k=4$ case of the generalized family:

```
k/n = 1/a + 1/b + 1/c,   k ∈ {4, 5, 6, 7, ...}
```

Despite extensive computations, the conjectural layer is open. The hard obstruction is arithmetic (not just slot counting), with classical concentration on Mordell residues modulo $840$.

---

## Mathematical Core (Full)

### 1. Core object: the unit-fraction length

Define the set of values reachable with exactly $t$ positive unit fractions:

```
\mathcal{E}_t \;=\; \left\{\, \sum_{i=1}^{t}\frac{1}{a_i} \;:\; a_i \in \mathbb{Z}_{>0} \,\right\}
```

(no distinctness requirement; repeats allowed). Then define the Egyptian compression length:

$$
\boxed{\,L_{\mathrm{UF}}(x) \;=\; \min\{\, t : x \in \mathcal{E}_t \,\}\,}
$$

Every positive rational has a finite expansion, so $L_{\mathrm{UF}}$ is always defined and finite. The interesting object is therefore not infinity but the bounded-length question $L_{\mathrm{UF}}(x) \le t$.

For completeness:

$$
\mathcal{E}_* \;=\; \bigcup_{t \ge 1}\mathcal{E}_t \qquad (\text{all positive rationals, by finiteness of Egyptian expansions})
$$

### 2. The conjectures, restated in one line each

| Name | Compact form | Status |
|---|---|---|
| Erdős-Straus | $L_{\mathrm{UF}}(4/n) \le 3$ for all $n \ge 2$ | open |
| Sierpiński | $L_{\mathrm{UF}}(5/n) \le 3$ for all $n \ge 2$ | open |
| Schinzel (general) | $L_{\mathrm{UF}}(k/n) \le 3$ for all $n$ large enough (given $k$) | open |
| 3-slot problem | $L_{\mathrm{UF}}(k/n) \le 3$ | family of hard Diophantine cases |

Structural point: the slot count is fixed at $3$; what moves is the numerator $k$.

### 3. Why $k=t+1$ is the threshold of first difficulty

For fixed slot count $t$, any $k \le t$ is trivial by unary repetition:

$$
\frac{k}{n} \;=\; \underbrace{\frac1n + \frac1n + \cdots + \frac1n}_{k\text{ copies}} \;\in\; \mathcal{E}_k \subseteq \mathcal{E}_t \qquad (k \le t).
$$

So at $t=3$, $1/n,2/n,3/n$ are immediate, while $4/n$ is first overflow (first case needing recombination, not copying).

Pattern:
- $t=2$: threshold $k=3$ fails (e.g., $3/7$ has no two-term unit-fraction form).
- $t=3$: threshold $k=4$ is open (Erdős-Straus).

### 4. Unary basis / repunit perspective

The default representation of $k/n$ is a unary block of $k$ copies of $1/n$. Compression asks whether this repetition can be rewritten in fewer reciprocal atoms.

Clearing denominators in

$$
\frac{k}{n} = \frac1a + \frac1b + \frac1c
$$

gives

$$
kabc \;=\; n(ab+ac+bc),
$$

so the repetition reappears as a multiplicative symmetric channel.

### 5. Inversion gate (multiplicative obstruction)

Fix first denominator as $a=nt$. Then

$$
\frac{4}{n} - \frac{1}{nt} \;=\; \frac{4t-1}{nt} \;=\; \frac1b + \frac1c.
$$

Two-term inversion gives

$$
\big((4t-1)b-nt\big)\big((4t-1)c-nt\big) \;=\; n^2t^2.
$$

Hence solutions correspond to divisor pairs $r,s\mid n^2t^2$ with $rs=n^2t^2$ such that

$$
b=\frac{r+nt}{4t-1},\qquad c=\frac{s+nt}{4t-1}
$$

are positive integers.

### 6. Why it is hard: arithmetic obstruction

Classically, hard cases reduce to residue classes

$$
n \equiv 1,121,169,289,361,529 \pmod{840},\qquad 840=2^3\cdot3\cdot5\cdot7.
$$

These are square classes modulo $840$, which explains why simple modular coverage misses the difficult fibers.

### 7. Goldbach diagnostic use

Applying ESC directly at even $N=p+q$ is weak because parity gives trivial closures. The informative test is on prime fibers: compute an inversion obstruction score on $p,q$ (or shifted forms), then compare that multiplicative channel against additive Hardy-Littlewood/Ramanujan baselines.

This repository uses that as a two-channel diagnostic, not as a proof bridge.

### 8. Verdict table

| Claim | Verdict |
|---|---|
| Use ESC at $N=p+q$ directly | weak/trivial (even $N$ parity closure) |
| Use ESC on prime fibers | good diagnostic |
| Inversion formulas as obstruction gates | clean, usable |
| Prove Goldbach from ESC (or vice versa) | no known bridge |
| Generalize to $k/n$ with fixed 3 slots | natural, central direction |

### Quick reference

$$
\mathcal{E}_t=\Big\{\textstyle\sum_{i=1}^{t}1/a_i : a_i\in\mathbb{Z}_{>0}\Big\},\qquad
L_{\mathrm{UF}}(x)=\min\{t:x\in\mathcal{E}_t\}
$$

$$
	extbf{ESC:}\ L_{\mathrm{UF}}(4/n)\le3\ \forall n\ge2
\qquad\qquad
	extbf{General direction:}\ L_{\mathrm{UF}}(k/n)\le3
$$

---

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
