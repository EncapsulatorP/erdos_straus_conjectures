#!/usr/bin/env python3
"""
esc_goldbach_split_ml.py

Machine-learning diagnostic for the proposed split:

    additive Goldbach / Ramanujan channel
        vs.
    multiplicative Erdős–Straus / Egyptian-fraction inversion channel

It builds one row per even N. The target is the actual Goldbach fiber count
# {p <= q : p + q = N}. It compares two models:

    A) additive features only
    B) additive + Erdős–Straus inversion features aggregated over the prime fiber

This is NOT a proof engine. It is a leakage-controlled diagnostic: if B improves
held-out prediction of the residual beyond Hardy-Littlewood/Ramanujan features,
then the Erdős–Straus channel is carrying extra signal worth studying.

Default run:
    python esc_goldbach_split_ml.py --n-max 20000 --es-m 64 --outdir results_split

Outputs:
    results_split/goldbach_split_dataset.csv
    results_split/goldbach_split_report.json
    results_split/feature_importance_all.csv
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


MORDELL_HARD_RESIDUES_840 = {1, 121, 169, 289, 361, 529}
DEFAULT_RAMANUJAN_Q = [3, 4, 5, 7, 8, 11, 13, 16, 30, 210, 840]
DEFAULT_MODS = [3, 4, 5, 7, 8, 11, 13, 16, 30, 210, 840]
TWIN_PRIME_C2_APPROX = 0.6601618158468696


# ----------------------------- number theory utils -----------------------------

def sieve_bool(limit: int) -> np.ndarray:
    """Return boolean array is_prime[0..limit]."""
    if limit < 2:
        return np.zeros(limit + 1, dtype=bool)
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[:2] = False
    is_prime[4::2] = False
    root = int(limit ** 0.5)
    for p in range(3, root + 1, 2):
        if is_prime[p]:
            is_prime[p * p :: 2 * p] = False
    return is_prime


def smallest_prime_factor(limit: int) -> np.ndarray:
    """Smallest prime factor table for 0..limit."""
    spf = np.arange(limit + 1, dtype=np.int64)
    if limit >= 1:
        spf[1] = 1
    for i in range(2, int(limit ** 0.5) + 1):
        if spf[i] == i:
            spf[i * i :: i] = np.minimum(spf[i * i :: i], i)
    return spf


def factorize(n: int, spf: np.ndarray | None = None) -> Dict[int, int]:
    """Prime factorization as {prime: exponent}."""
    if n <= 1:
        return {}
    out: Dict[int, int] = {}
    if spf is not None and n < len(spf):
        while n > 1:
            p = int(spf[n])
            out[p] = out.get(p, 0) + 1
            n //= p
        return out
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def divisors_from_factorization(factors: Dict[int, int]) -> List[int]:
    divs = [1]
    for p, e in factors.items():
        old = divs[:]
        pow_p = 1
        for _ in range(e):
            pow_p *= p
            divs.extend([d * pow_p for d in old])
    return divs


def mobius(n: int) -> int:
    if n == 1:
        return 1
    x = n
    mu = 1
    p = 2
    while p * p <= x:
        if x % p == 0:
            x //= p
            mu *= -1
            if x % p == 0:
                return 0
            while x % p == 0:
                x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        mu *= -1
    return mu


def phi(n: int) -> int:
    if n <= 0:
        return 0
    result = n
    x = n
    p = 2
    while p * p <= x:
        if x % p == 0:
            result -= result // p
            while x % p == 0:
                x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        result -= result // x
    return result


@lru_cache(maxsize=None)
def ramanujan_sum(n: int, q: int) -> int:
    """Integer Ramanujan sum c_q(n)."""
    g = math.gcd(n, q)
    qg = q // g
    phiq = phi(q)
    phiqg = phi(qg)
    if phiqg == 0:
        return 0
    return mobius(qg) * phiq // phiqg


def goldbach_pairs(N: int, is_prime: np.ndarray) -> List[Tuple[int, int]]:
    pairs = []
    for p in range(2, N // 2 + 1):
        q = N - p
        if is_prime[p] and is_prime[q]:
            pairs.append((p, q))
    return pairs


def hl_goldbach_estimate(N: int) -> float:
    """Very small Hardy-Littlewood-style baseline estimate for even N."""
    if N < 4 or N % 2:
        return 0.0
    if N <= 6:
        logn = max(math.log(N), 1.0)
    else:
        logn = math.log(N)
    correction = 1.0
    x = N
    p = 3
    while p * p <= x:
        if x % p == 0:
            correction *= (p - 1) / max(p - 2, 1)
            while x % p == 0:
                x //= p
        p += 2
    if x > 2:
        correction *= (x - 1) / max(x - 2, 1)
    # Count p<=q, so divide the ordered-pair estimate by about 2.
    return max(0.0, TWIN_PRIME_C2_APPROX * correction * N / (logn * logn))


# ----------------------- Erdős–Straus inversion feature gate -------------------

@dataclass(frozen=True)
class ErdosStrausStats:
    first_m: int
    solved_count: int
    checked_m: int
    density: float
    hard_residue_840: int
    min_mod_gap: int


class ErdosStrausInversionCache:
    """Restricted Egyptian inversion gate for k/n = 1/a + 1/b + 1/c with a = n*m.

    For k=4 this is the Erdős–Straus channel. For a fixed m:

        k/n - 1/(n*m) = (k*m - 1)/(n*m) = 1/b + 1/c.

    Let A = k*m - 1 and B = n*m. Then:

        (A*b - B)(A*c - B) = B^2.

    A solution exists for this m if some divisor d | B^2 satisfies
        d + B == 0 mod A and B^2/d + B == 0 mod A.
    """

    def __init__(self, m_limit: int, spf: np.ndarray | None = None, k: int = 4):
        self.m_limit = int(m_limit)
        self.spf = spf
        self.k = int(k)
        self._cache: Dict[int, ErdosStrausStats] = {}

    def stats(self, n: int) -> ErdosStrausStats:
        n = int(n)
        if n in self._cache:
            return self._cache[n]
        solved_count = 0
        first_m = 0
        min_gap = 10**18
        for m in range(1, self.m_limit + 1):
            A = self.k * m - 1
            B = n * m
            # Cheap modular closeness diagnostic, even when no divisor succeeds.
            min_gap = min(min_gap, min(B % A, (-B) % A))
            factors_B = factorize(B, self.spf)
            factors_D = {p: 2 * e for p, e in factors_B.items()}
            D = B * B
            found = False
            for d in divisors_from_factorization(factors_D):
                if (d + B) % A == 0 and (D // d + B) % A == 0:
                    found = True
                    break
            if found:
                solved_count += 1
                if first_m == 0:
                    first_m = m
        hard = int(n % 840 in MORDELL_HARD_RESIDUES_840)
        stats = ErdosStrausStats(
            first_m=first_m,
            solved_count=solved_count,
            checked_m=self.m_limit,
            density=solved_count / max(self.m_limit, 1),
            hard_residue_840=hard,
            min_mod_gap=int(min_gap if min_gap < 10**18 else 0),
        )
        self._cache[n] = stats
        return stats


# ------------------------------- dataset builder -------------------------------

def build_dataset(
    n_max: int,
    es_m: int,
    ramanujan_q: Iterable[int] = DEFAULT_RAMANUJAN_Q,
    mods: Iterable[int] = DEFAULT_MODS,
) -> pd.DataFrame:
    is_prime = sieve_bool(n_max)
    spf = smallest_prime_factor(max(n_max, 2))
    erdos_straus_cache = ErdosStrausInversionCache(m_limit=es_m, spf=spf, k=4)
    rows = []

    for N in range(4, n_max + 1, 2):
        pairs = goldbach_pairs(N, is_prime)
        count = len(pairs)
        hl = hl_goldbach_estimate(N)
        row: Dict[str, float] = {
            "N": N,
            "goldbach_count": count,
            "logN": math.log(N),
            "sqrtN": math.sqrt(N),
            "hl_estimate": hl,
            "log_hl_estimate": math.log1p(hl),
            "target_log_count": math.log1p(count),
            "target_residual": math.log1p(count) - math.log1p(hl),
        }
        for mod in mods:
            row[f"N_mod_{mod}"] = N % mod
            row[f"N_mod_{mod}_scaled"] = (N % mod) / mod
        for q in ramanujan_q:
            row[f"ramanujan_c_{q}"] = ramanujan_sum(N, q)
            row[f"ramanujan_c_{q}_norm"] = ramanujan_sum(N, q) / max(phi(q), 1)

        if count == 0:
            erdos_straus_first = [0]
            erdos_straus_density = [0.0]
            erdos_straus_hard = [0]
            erdos_straus_gap = [0]
            pair_density_product = [0.0]
            pair_hard_any = [0]
        else:
            erdos_straus_first = []
            erdos_straus_density = []
            erdos_straus_hard = []
            erdos_straus_gap = []
            pair_density_product = []
            pair_hard_any = []
            for p, q in pairs:
                sp = erdos_straus_cache.stats(p)
                sq = erdos_straus_cache.stats(q)
                for s in (sp, sq):
                    erdos_straus_first.append(s.first_m if s.first_m else es_m + 1)
                    erdos_straus_density.append(s.density)
                    erdos_straus_hard.append(s.hard_residue_840)
                    erdos_straus_gap.append(s.min_mod_gap)
                pair_density_product.append(sp.density * sq.density)
                pair_hard_any.append(int(sp.hard_residue_840 or sq.hard_residue_840))

        row.update(
            {
                "erdos_straus_first_m_mean": float(np.mean(erdos_straus_first)),
                "erdos_straus_first_m_min": float(np.min(erdos_straus_first)),
                "erdos_straus_first_m_max": float(np.max(erdos_straus_first)),
                "erdos_straus_density_mean": float(np.mean(erdos_straus_density)),
                "erdos_straus_density_std": float(np.std(erdos_straus_density)),
                "erdos_straus_unsolved_rate": float(np.mean([x == es_m + 1 for x in erdos_straus_first])),
                "erdos_straus_hard_residue_rate": float(np.mean(erdos_straus_hard)),
                "erdos_straus_min_mod_gap_mean": float(np.mean(erdos_straus_gap)),
                "erdos_straus_pair_density_product_mean": float(np.mean(pair_density_product)),
                "erdos_straus_pair_hard_any_rate": float(np.mean(pair_hard_any)),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------- modeling -----------------------------------

def evaluate_models(df: pd.DataFrame, outdir: str, target: str = "target_residual") -> Dict[str, object]:
    additive_cols = [
        c
        for c in df.columns
        if c.startswith("N_mod_")
        or c.startswith("ramanujan_")
        or c in ["logN", "sqrtN", "hl_estimate", "log_hl_estimate"]
    ]
    erdos_straus_cols = [c for c in df.columns if c.startswith("erdos_straus_")]
    all_cols = additive_cols + erdos_straus_cols

    # Leakage-controlled chronological split: train on small N, test on larger N.
    df = df.sort_values("N").reset_index(drop=True)
    split = int(0.75 * len(df))
    train = df.iloc[:split].copy()
    test = df.iloc[split:].copy()

    def fit_eval(cols: List[str], name: str):
        model = RandomForestRegressor(
            n_estimators=80,
            min_samples_leaf=3,
            max_features=0.75,
            random_state=42,
            n_jobs=-1,
        )
        X_train = train[cols]
        y_train = train[target]
        X_test = test[cols]
        y_test = test[target]
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        return model, {
            "name": name,
            "n_features": len(cols),
            "mae": float(mean_absolute_error(y_test, pred)),
            "rmse": float(mean_squared_error(y_test, pred) ** 0.5),
            "r2": float(r2_score(y_test, pred)),
        }, pred

    additive_model, additive_metrics, pred_add = fit_eval(additive_cols, "additive_only")
    all_model, all_metrics, pred_all = fit_eval(all_cols, "additive_plus_ErdosStraus")

    # Permutation importance for the all model on a manageable test matrix.
    importance = permutation_importance(
        all_model,
        test[all_cols],
        test[target],
        n_repeats=3,
        random_state=42,
        scoring="neg_mean_absolute_error",
    )
    imp_df = pd.DataFrame(
        {
            "feature": all_cols,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    imp_df.to_csv(os.path.join(outdir, "feature_importance_all.csv"), index=False)

    pred_df = test[["N", "goldbach_count", "hl_estimate", "target_log_count", "target_residual"]].copy()
    pred_df["pred_additive"] = pred_add
    pred_df["pred_additive_plus_ErdosStraus"] = pred_all
    pred_df.to_csv(os.path.join(outdir, "holdout_predictions.csv"), index=False)

    report = {
        "target": target,
        "n_rows": int(len(df)),
        "train_N_range": [int(train.N.min()), int(train.N.max())],
        "test_N_range": [int(test.N.min()), int(test.N.max())],
        "additive_only": additive_metrics,
        "additive_plus_ErdosStraus": all_metrics,
        "delta_rmse_all_minus_additive": float(all_metrics["rmse"] - additive_metrics["rmse"]),
        "delta_mae_all_minus_additive": float(all_metrics["mae"] - additive_metrics["mae"]),
        "interpretation": (
            "Negative deltas mean the Erdős–Straus inversion channel improved held-out prediction. "
            "Positive deltas mean it did not help under this feature/limit/split."
        ),
        "top_features": imp_df.head(25).to_dict(orient="records"),
    }
    with open(os.path.join(outdir, "goldbach_split_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


# ------------------------------------ CLI --------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-max", type=int, default=20000, help="Maximum even N to scan.")
    parser.add_argument("--es-m", type=int, default=64, help="Max m in a=n*m Erdős–Straus inversion gate.")
    parser.add_argument("--outdir", type=str, default="results_split")
    parser.add_argument(
        "--target",
        type=str,
        default="target_residual",
        choices=["target_residual", "target_log_count", "goldbach_count"],
        help="Prediction target. residual is usually best for testing extra signal.",
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = build_dataset(n_max=args.n_max, es_m=args.es_m)
    dataset_path = os.path.join(args.outdir, "goldbach_split_dataset.csv")
    df.to_csv(dataset_path, index=False)
    report = evaluate_models(df, outdir=args.outdir, target=args.target)

    print(json.dumps(report, indent=2))
    print(f"\nWrote: {dataset_path}")
    print(f"Wrote: {os.path.join(args.outdir, 'goldbach_split_report.json')}")
    print(f"Wrote: {os.path.join(args.outdir, 'feature_importance_all.csv')}")


if __name__ == "__main__":
    main()
