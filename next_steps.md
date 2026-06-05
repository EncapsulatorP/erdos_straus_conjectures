# Next Steps

Ordered by priority. Items marked **[theory]** require mathematical analysis; **[compute]** require running or extending scripts.

---

## Immediate

### 1. Run the remainder compression experiment **[compute]**

The `results_remainder/` directory is empty. Run the gate experiment to get the baseline solve rates before drawing any cross-k conclusions:

```
python remainder_compression_ml.py --n-max 5000 --k-values 4 5 6 7 --m-limit 128 --outdir results_remainder
```

Analyze:
- Solve rate by k: does gate solvability decrease monotonically as k increases?
- For unsolved cases, does the hard-residue class (n mod 840 ∈ {1,121,169,289,361,529}) dominate failures?
- Compare feature importances for classifier vs. regressor to see whether the same arithmetic properties govern *whether* and *how hard* the gate is.

### 2. Ablation: which ESC features drive the Goldbach improvement? **[compute]**

Model B uses 10 ESC features. Run a subset ablation:
- B1: additive + `esc_first_m_mean` only
- B2: additive + density features (`esc_density_mean`, `esc_density_std`) only
- B3: additive + hard-residue rate (`esc_pair_hard_any_rate`) only

This distinguishes whether the gain comes from the *scale* of the first solution (first_m), the *density* of solutions, or the *obstruction structure* (hard residues). The answer shapes whether to pursue deeper algebraic explanations.

---

## Short Term

### 3. Scale Goldbach experiment to N = 100,000 **[compute]**

The current run covers N ≤ 20,000. The ESC signal might strengthen (or collapse) at larger scales. Specifically:
- `esc_first_m_mean` dominance: does it persist or decay as N grows?
- Large-modulus features (N mod 840) had negative importance at N ≤ 20,000 but may become useful once the residue classes are better sampled (period 840 needs ~10× coverage to see structure clearly).

```
python esc_goldbach_split_ml.py --n-max 100000 --esc-m 128 --outdir results_split_100k
```

Note: runtime will increase roughly linearly with N and with esc-m.

### 4. Investigate the first-m distribution over the prime fiber **[theory + compute]**

`esc_first_m_mean` is the top feature. Concretely: for a prime p dividing the Goldbach fiber of N, what determines the smallest m such that the gate 4/p = 1/(p·m) + 1/b + 1/c has a solution?

The divisor identity gives: m must satisfy `(4m−1)² ≡ 1 (mod p)`, which reduces to `4m ≡ 0 or 2 (mod p)`. The first valid m is determined by arithmetic progressions mod p. A closed-form or tight bound on first_m(p) would explain why its mean over the fiber tracks the Goldbach residual.

### 5. Separate hard-residue primes from smooth primes in the fiber **[compute]**

Currently `esc_pair_hard_any_rate` is a binary indicator (any hard prime in the pair). Refine it:
- `esc_hard_prime_count` — count of primes in fiber with p mod 840 ∈ hard set
- `esc_hard_prime_fraction` — fraction of fiber primes that are hard
- Split first_m stats into hard-fiber and smooth-fiber components

This may extract a cleaner signal from the hard-residue obstruction structure.

---

## Medium Term

### 6. Connect gate solvability to Goldbach fiber directly **[theory]**

The cross-domain question: is there a precise statement of the form

> "If the ESC gate 4/p fails within m ≤ M for many primes p in the Goldbach fiber of N, then the Goldbach count of N is below the Hardy–Littlewood prediction"?

The ML results suggest such a correlation exists. Formalize it by:
1. Binning N by Goldbach residual quartile (well above / near / well below HL estimate)
2. Computing ESC gate solve rates for each bin
3. Testing if the conditional distributions differ significantly (KS test or permutation test)

This would convert the ML result into a falsifiable statistical claim.

### 7. Try gradient boosting and compare feature rankings **[compute]**

Random Forest may not capture interactions between ESC and additive features efficiently. Train XGBoost or LightGBM on the same feature set and compare:
- Does the same feature ordering hold?
- Do interaction features (e.g., first_m_mean × ramanujan_c_30) appear in SHAP values?

If rankings are stable across model families, the signal is structural rather than an artifact of the Random Forest induction bias.

### 8. Extend gate to k=4 with variable first denominator **[theory + compute]**

The current gate fixes a = n·m. This is a deliberate restriction for reproducibility. The unrestricted problem (arbitrary a) covers the full ESC conjecture. Study whether:
- The set of n unsolved by the restricted gate is a proper subset of the true ESC hard cases
- The gap between gate-hard and genuinely-hard n narrows as m_limit grows

If the restricted gate already captures all hard cases for n ≤ 5000, it suggests the structure of hard cases is concentrated on the n·m denominator family.

---

## Long Term

### 9. Formal hardness classification mod 840 **[theory]**

The Mordell residues {1, 121, 169, 289, 361, 529} mod 840 are quadratic residues. The theoretical reason they are hard is that for n in these classes, the factorization of B² = (n·m)² avoids the residue classes needed for the gate solution. A complete proof would require:
- Characterizing which factorizations of B² yield valid (b, c) pairs
- Showing that for n ≡ hard_class (mod 840) and all m not divisible by certain primes, no valid factorization exists
- Extending to composite n by Chinese Remainder Theorem

### 10. Cross-conjecture: Goldbach obstruction ↔ ESC obstruction **[theory]**

The ML results hint at a deeper relationship. A theoretical program:
- Define an "additive difficulty" function D_G(N) = |goldbach_count(N) − HL(N)|
- Define a "multiplicative difficulty" function D_E(p) = first_m(p) for primes p
- Study whether E[D_E(p) : p in Goldbach fiber of N] correlates with D_G(N) in a way that can be explained by the distribution of primes in arithmetic progressions (Dirichlet characters / L-functions)

This connects both conjectures to the same underlying structure: the distribution of primes mod q for small q.
