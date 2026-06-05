#!/usr/bin/env python3
"""
remainder_compression_ml.py

Machine-learning diagnostic for the "fixed slots / overflowing numerator" question:

    Can k/n be compressed into exactly 3 unit fractions?

The trivial copy code has length k:

    k/n = 1/n + ... + 1/n       (k copies)

With slots=3, k=4 is the first overflow, k=5 the next, etc. This script
studies that overflow/remainder layer with a restricted but very useful
inversion gate:

    k/n = 1/(n*m) + 1/b + 1/c

For each (k,n), it searches m <= m_limit using the divisor identity:

    A = k*m - 1, B = n*m
    (A*b - B)(A*c - B) = B^2

It creates a dataset and trains models for:
    - solved_within_gate: whether the gate found a 3-term compression
    - log_first_m: how large the first successful m is, when found

This is not a complete Egyptian-fraction solver because it restricts the first
denominator to a=n*m. That restriction is intentional: it gives a clean,
repeatable obstruction/remainder gate that can be compared across k.

Default run:
    python remainder_compression_ml.py --n-max 5000 --k-values 4 5 6 7 --m-limit 128 --outdir results_remainder

Outputs:
    results_remainder/remainder_dataset.csv
    results_remainder/remainder_report.json
    results_remainder/feature_importance_classifier.csv
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
    r2_score,
)


MORDELL_HARD_RESIDUES_840 = {1, 121, 169, 289, 361, 529}
DEFAULT_MODS = [3, 4, 5, 7, 8, 11, 13, 16, 30, 210, 840]
DEFAULT_RAMANUJAN_Q = [3, 4, 5, 7, 8, 11, 13, 16, 30, 210, 840]


# ----------------------------- number theory utils -----------------------------

def sieve_bool(limit: int) -> np.ndarray:
    if limit < 2:
        return np.zeros(limit + 1, dtype=bool)
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[:2] = False
    is_prime[4::2] = False
    for p in range(3, int(limit ** 0.5) + 1, 2):
        if is_prime[p]:
            is_prime[p * p :: 2 * p] = False
    return is_prime


def smallest_prime_factor(limit: int) -> np.ndarray:
    spf = np.arange(limit + 1, dtype=np.int64)
    if limit >= 1:
        spf[1] = 1
    for i in range(2, int(limit ** 0.5) + 1):
        if spf[i] == i:
            spf[i * i :: i] = np.minimum(spf[i * i :: i], i)
    return spf


def factorize(n: int, spf: np.ndarray | None = None) -> Dict[int, int]:
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
        base = divs[:]
        pow_p = 1
        for _ in range(e):
            pow_p *= p
            divs.extend([d * pow_p for d in base])
    return divs


def phi_from_factors(n: int, factors: Dict[int, int]) -> int:
    result = n
    for p in factors:
        result -= result // p
    return result


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
    g = math.gcd(n, q)
    qg = q // g
    return mobius(qg) * phi(q) // max(phi(qg), 1)


def divisor_count_from_factors(factors: Dict[int, int]) -> int:
    out = 1
    for e in factors.values():
        out *= e + 1
    return out


def omega_from_factors(factors: Dict[int, int]) -> int:
    return len(factors)


def big_omega_from_factors(factors: Dict[int, int]) -> int:
    return sum(factors.values())


# ----------------------------- inversion gate ---------------------------------

@dataclass(frozen=True)
class GateResult:
    solved: int
    first_m: int
    solved_count: int
    m_limit: int
    solution_density: float
    min_mod_gap: int
    example_a: int
    example_b: int
    example_c: int


class CompressionGate:
    """Restricted 3-slot compression gate for k/n."""

    def __init__(self, m_limit: int, spf: np.ndarray | None = None):
        self.m_limit = int(m_limit)
        self.spf = spf
        self.cache: Dict[tuple[int, int], GateResult] = {}

    def solve(self, k: int, n: int) -> GateResult:
        key = (int(k), int(n))
        if key in self.cache:
            return self.cache[key]
        k, n = key
        first_m = 0
        solved_count = 0
        example = (0, 0, 0)
        min_gap = 10**18

        for m in range(1, self.m_limit + 1):
            A = k * m - 1
            B = n * m
            D = B * B
            min_gap = min(min_gap, min(B % A, (-B) % A))
            factors_B = factorize(B, self.spf)
            factors_D = {p: 2 * e for p, e in factors_B.items()}
            found = False
            for d in divisors_from_factorization(factors_D):
                e = D // d
                if (d + B) % A == 0 and (e + B) % A == 0:
                    a = n * m
                    b = (d + B) // A
                    c = (e + B) // A
                    if a > 0 and b > 0 and c > 0:
                        found = True
                        if first_m == 0:
                            first_m = m
                            example = tuple(sorted((a, b, c)))
                        break
            if found:
                solved_count += 1

        result = GateResult(
            solved=int(first_m > 0),
            first_m=first_m,
            solved_count=solved_count,
            m_limit=self.m_limit,
            solution_density=solved_count / max(self.m_limit, 1),
            min_mod_gap=int(min_gap if min_gap < 10**18 else 0),
            example_a=example[0],
            example_b=example[1],
            example_c=example[2],
        )
        self.cache[key] = result
        return result


# ------------------------------- dataset builder -------------------------------

def build_dataset(
    n_max: int,
    k_values: Sequence[int],
    m_limit: int,
    slots: int,
    primes_only: bool,
    mods: Iterable[int] = DEFAULT_MODS,
    ramanujan_q: Iterable[int] = DEFAULT_RAMANUJAN_Q,
) -> pd.DataFrame:
    is_prime = sieve_bool(n_max)
    spf = smallest_prime_factor(max(n_max * max(k_values + [1]), 2))
    gate = CompressionGate(m_limit=m_limit, spf=spf)
    rows = []

    for k in k_values:
        for n in range(2, n_max + 1):
            if primes_only and not is_prime[n]:
                continue
            factors = factorize(n, spf)
            phin = phi_from_factors(n, factors)
            result = gate.solve(k, n)
            overflow = k - slots
            row: Dict[str, float | int] = {
                "k": k,
                "n": n,
                "slots": slots,
                "overflow": overflow,
                "positive_overflow": int(overflow > 0),
                "overflow_ratio": overflow / max(slots, 1),
                "is_prime_n": int(is_prime[n]),
                "gcd_k_n": math.gcd(k, n),
                "log_n": math.log(n),
                "sqrt_n": math.sqrt(n),
                "phi_over_n": phin / n,
                "omega_n": omega_from_factors(factors),
                "big_omega_n": big_omega_from_factors(factors),
                "tau_n": divisor_count_from_factors(factors),
                "mordell_hard_residue_840": int(n % 840 in MORDELL_HARD_RESIDUES_840),
                "square_class_mod_840": (n * n) % 840,
                "solved_within_gate": result.solved,
                "first_m": result.first_m if result.first_m else m_limit + 1,
                "log_first_m_censored": math.log1p(result.first_m if result.first_m else m_limit + 1),
                "solution_density": result.solution_density,
                "solved_count_m": result.solved_count,
                "min_mod_gap": result.min_mod_gap,
                "example_a": result.example_a,
                "example_b": result.example_b,
                "example_c": result.example_c,
            }
            for mod in mods:
                row[f"n_mod_{mod}"] = n % mod
                row[f"n_mod_{mod}_scaled"] = (n % mod) / mod
                row[f"k_mod_{mod}"] = k % mod
            for q in ramanujan_q:
                row[f"ramanujan_c_{q}"] = ramanujan_sum(n, q)
                row[f"ramanujan_c_{q}_norm"] = ramanujan_sum(n, q) / max(phi(q), 1)
            rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------- modeling -----------------------------------

def model_dataset(df: pd.DataFrame, outdir: str) -> Dict[str, object]:
    ignore_cols = {
        "solved_within_gate",
        "first_m",
        "log_first_m_censored",
        "solution_density",
        "solved_count_m",
        "example_a",
        "example_b",
        "example_c",
    }
    feature_cols = [c for c in df.columns if c not in ignore_cols]

    # Split by n to reduce leakage from neighboring k rows.
    unique_n = np.array(sorted(df["n"].unique()))
    split_n = unique_n[int(0.75 * len(unique_n))]
    train = df[df["n"] <= split_n].copy()
    test = df[df["n"] > split_n].copy()

    X_train = train[feature_cols]
    X_test = test[feature_cols]
    y_train = train["solved_within_gate"]
    y_test = test["solved_within_gate"]

    clf = RandomForestClassifier(
        n_estimators=100,
        min_samples_leaf=3,
        max_features=0.75,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    # Metrics robust to degenerate classes.
    clf_metrics: Dict[str, float | None] = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
    }
    if len(set(y_test)) > 1:
        clf_metrics["roc_auc"] = float(roc_auc_score(y_test, proba))
        clf_metrics["average_precision"] = float(average_precision_score(y_test, proba))
    else:
        clf_metrics["roc_auc"] = None
        clf_metrics["average_precision"] = None

    imp = permutation_importance(
        clf,
        X_test,
        y_test,
        n_repeats=3,
        random_state=42,
        scoring="balanced_accuracy",
    )
    imp_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance_mean": imp.importances_mean,
            "importance_std": imp.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    imp_df.to_csv(os.path.join(outdir, "feature_importance_classifier.csv"), index=False)

    pred_df = test[["k", "n", "overflow", "solved_within_gate", "first_m", "solution_density", "example_a", "example_b", "example_c"]].copy()
    pred_df["pred_solved_probability"] = proba
    pred_df.to_csv(os.path.join(outdir, "holdout_predictions.csv"), index=False)

    reg_metrics = None
    found_train = train[train["solved_within_gate"] == 1].copy()
    found_test = test[test["solved_within_gate"] == 1].copy()
    if len(found_train) >= 50 and len(found_test) >= 10:
        reg = RandomForestRegressor(
            n_estimators=80,
            min_samples_leaf=3,
            max_features=0.75,
            random_state=43,
            n_jobs=-1,
        )
        reg.fit(found_train[feature_cols], found_train["log_first_m_censored"])
        rpred = reg.predict(found_test[feature_cols])
        y = found_test["log_first_m_censored"]
        reg_metrics = {
            "mae": float(mean_absolute_error(y, rpred)),
            "rmse": float(mean_squared_error(y, rpred) ** 0.5),
            "r2": float(r2_score(y, rpred)),
            "note": "Regression is only over rows solved within the gate.",
        }

    summary_by_k = (
        df.groupby("k")
        .agg(
            rows=("n", "count"),
            solved_rate=("solved_within_gate", "mean"),
            mean_first_m=("first_m", "mean"),
            median_first_m=("first_m", "median"),
            mean_density=("solution_density", "mean"),
            hard_residue_rate=("mordell_hard_residue_840", "mean"),
        )
        .reset_index()
        .to_dict(orient="records")
    )

    report = {
        "n_rows": int(len(df)),
        "train_n_max": int(split_n),
        "test_n_min": int(test["n"].min()) if len(test) else None,
        "feature_count": len(feature_cols),
        "classifier": clf_metrics,
        "regressor_log_first_m": reg_metrics,
        "summary_by_k": summary_by_k,
        "top_classifier_features": imp_df.head(25).to_dict(orient="records"),
        "interpretation": (
            "solved_within_gate=0 means no solution was found under the restricted a=n*m gate up to m_limit; "
            "it is a computational obstruction/censoring label, not a proof of nonexistence."
        ),
    }
    with open(os.path.join(outdir, "remainder_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


# ------------------------------------ CLI --------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-max", type=int, default=5000)
    parser.add_argument("--k-values", type=int, nargs="+", default=[4, 5, 6, 7])
    parser.add_argument("--slots", type=int, default=3)
    parser.add_argument("--m-limit", type=int, default=128)
    parser.add_argument("--primes-only", action="store_true", help="Restrict n to primes, useful for ESC-style reductions.")
    parser.add_argument("--outdir", type=str, default="results_remainder")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = build_dataset(
        n_max=args.n_max,
        k_values=args.k_values,
        m_limit=args.m_limit,
        slots=args.slots,
        primes_only=args.primes_only,
    )
    dataset_path = os.path.join(args.outdir, "remainder_dataset.csv")
    df.to_csv(dataset_path, index=False)
    report = model_dataset(df, args.outdir)

    print(json.dumps(report, indent=2))
    print(f"\nWrote: {dataset_path}")
    print(f"Wrote: {os.path.join(args.outdir, 'remainder_report.json')}")
    print(f"Wrote: {os.path.join(args.outdir, 'feature_importance_classifier.csv')}")


if __name__ == "__main__":
    main()
