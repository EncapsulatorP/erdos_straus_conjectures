# Egyptian Compression Length — ESC / Sierpiński / Goldbach Diagnostic

**Folder:** `focus_shima`
**Status:** working note. Definitions are settled; the conjectures are open; the Goldbach link is diagnostic, not a proof bridge.

---

## 1. Core object: the unit-fraction length

 Define the set of values reachable with exactly `t` positive unit fractions:

$
\mathcal{E}_t \;=\; \left\{\, \sum_{i=1}^{t}\frac{1}{a_i} \;:\; a_i \in \mathbb{Z}_{>0} \,\right\}
$

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

---

## 4. The unary basis / repunit reading (why repetitions keep returning)

Unit fractions are a **unary basis**. The dumb default representation of $k/n$ is literally $k$ repetitions of $1/n$ — the repunit-style "uncompressed code." Erdős–Straus is the claim that the unary block

$$
\underbrace{1\,1\,1\,1}_{k=4} \;\longrightarrow\; \frac1a + \frac1b + \frac1c
$$

can always be compressed into **three reciprocal atoms**. The repetition layer keeps reappearing because the original problem is *built from* unary atoms; you are trying to escape the layer the object is made of.

It does not vanish under inversion — it changes costume. Clearing denominators in $\frac{k}{n} = \frac1a + \frac1b + \frac1c$ gives

$$
k\,abc \;=\; n\,(ab + ac + bc).
$$

The right side is a symmetric pile of pairwise products $ab + ac + bc$ — the hidden repetition/product channel. The unary structure is preserved on the multiplicative side.

**Design principle for any compression we adopt:** the shorthand must preserve this difficulty. $k/n \in \mathcal{E}_t$ and $L_{\mathrm{UF}}(k/n) \le t$ both do. A private shorthand like "$k/n = t/(n_*)$" should be avoided in formal text — it reads as an ordinary fraction rather than "$t$ unit-fraction slots." If a slot operator is wanted, prefer $k/n \Rightarrow_t 1/{*}$, but $\in \mathcal{E}_t$ is cleaner.

---

## 5. The inversion gate (multiplicative obstruction)

Force the first denominator as $a = nt$. Then the remainder is two-term:

$$
\frac{4}{n} - \frac{1}{nt} \;=\; \frac{4t - 1}{nt} \;=\; \frac1b + \frac1c .
$$

Standard divisor inversion of the two-term remainder gives

$$
\big((4t-1)b - nt\big)\big((4t-1)c - nt\big) \;=\; n^2 t^2 .
$$

So a solution is equivalent to finding a divisor pair $r,s \mid n^2 t^2$ with $rs = n^2 t^2$ such that

$$
b = \frac{r + nt}{4t - 1}, \qquad c = \frac{s + nt}{4t - 1}
$$

are both positive integers.

**ESC inversion gate:**

| Layer | Meaning |
|---|---|
| $n$ | number being tested |
| $t$ | first-denominator scale, $a = nt$ |
| $4t - 1$ | inversion modulus |
| $r, s \mid n^2 t^2$ | divisor shell |
| failure | no divisor pair satisfies integrality / congruence condition |

This is a clean **obstruction checker**, multiplicative in character.

---

## 6. Why it is genuinely hard — the arithmetic obstruction

The threshold overflow alone would be easy; the difficulty is arithmetic. It suffices to prove ESC for primes. Mordell reduced the remaining cases to the residues

$$
n \equiv 1,\ 121,\ 169,\ 289,\ 361,\ 529 \pmod{840}, \qquad 840 = 2^3 \cdot 3 \cdot 5 \cdot 7 .
$$

These six are exactly the **squares** of residues coprime to $840$. So the hard fibers carry a **quadratic-residue (square-class) signature** — which is why elementary modular covering systems keep missing them. The obstruction is not a counting overflow; it is a square-class condition mod 840.

This is the load-bearing fact for treating ESC as a diagnostic: the signal it carries is *square-class structure*, orthogonal to additive Hardy–Littlewood residue structure.

---

## 7. Goldbach application — prime-fiber Egyptian obstruction gate

**Caveat first.** At the raw Goldbach level $n = N = p + q$ the gate degenerates, because $N$ is even and even $N$ are trivial:

$$
\frac{4}{N} = \frac{2}{m} = \frac1m + \frac1{m+1} + \frac1{m(m+1)} \qquad (N = 2m).
$$

So ESC gives almost no obstruction on the even sum itself; it is already closed by parity. The nontrivial obstruction space lives on **odd primes / residue classes**.

**Use it on the prime fibers, not on $N$.** For each Goldbach fiber $p + q = N$, compute an obstruction score $O_{\mathrm{ESC}}(\cdot)$ via the divisor-inversion gate, on $p$, $q$, or nearby shifted forms $p \pm 1,\ q \pm 1,\ N - p,\ N - q$. Then compare

$$
\sum_{p + q = N} O_{\mathrm{ESC}}(p)\, O_{\mathrm{ESC}}(q)
$$

against the Hardy–Littlewood / Ramanujan baseline.

**What this tests:** whether reciprocal-divisor (multiplicative, square-class) obstruction adds signal beyond the additive Goldbach residue structure. The honest framing is a **two-channel comparison**, not a proof bridge:

$$
\underbrace{\text{additive Fourier / Ramanujan channel}}_{R(N) = \int_0^1 S(\alpha)^2 e(-N\alpha)\,d\alpha}
\qquad \text{vs.} \qquad
\underbrace{\text{multiplicative Egyptian-fraction inversion channel}}_{\text{ESC divisor gate}}
$$

---

## 8. Verdict table

| Claim | Verdict |
|---|---|
| Use ESC at $N = p + q$ directly | weak / trivial — $N$ even, closed by parity |
| Use ESC on prime fibers $(p, q)$ | good diagnostic |
| Inversion formulas as obstruction gates | clean, usable |
| Prove Goldbach from ESC (or vice versa) | no known bridge |
| Treat as unit-circle closure theorem | too strong — false framing |
| Generalize to $k/n$ | possible, but a family of hard Diophantine problems |

**Honest read:** promising as a classifier / diagnostic (additive vs. multiplicative obstruction spectra), not as a proof path. The pre-registered expectation should be that the multiplicative channel carries square-class signal that is largely orthogonal to — and may or may not beat — the Hardy–Littlewood baseline. A clean negative (no signal beyond baseline) is a publishable result.

---

## Quick reference

$$
\mathcal{E}_t = \Big\{ \textstyle\sum_{i=1}^t 1/a_i : a_i \in \mathbb{Z}_{>0} \Big\}, \qquad
L_{\mathrm{UF}}(x) = \min\{ t : x \in \mathcal{E}_t \}
$$

$$
\textbf{ESC:}\quad L_{\mathrm{UF}}(4/n) \le 3 \ \ \forall\, n \ge 2
\qquad\qquad
\textbf{Threshold:}\quad k \le t \text{ trivial}, \ \ k = t+1 \text{ first hard}
$$
