# Reading `aer_validation.png`

Companion to `aer_validation.py`. The figure has four panels, in two columns —
one column per cost function, **C0** (gate errors only) and **C1** (gate errors +
linearised idle-decoherence term). Both columns plot the same 126 candidates, so
the columns are read *against each other*: the difference between them is what the
idle term buys.

All numbers below come from `aer_validation.csv` (run of 30 Jul 2026, FakeTorino,
50 sampled linear triples × 3 decompositions = 150 rows).

---

## What is on each axis

| | x | y |
|---|---|---|
| **Top row** | predicted cost (C0 or C1) | simulated average-gate infidelity |
| **Bottom row** | predicted cost (same as above) | predicted / observed, i.e. `(1 − e^(−C)) / observed` |

The y of the top row is an *exact* superoperator simulation of the noisy circuit
compared against that entry's own target unitary — not another estimate. That is
the reference the cost is being judged against.

Colour **and** marker shape both encode the decomposition (circle / square /
triangle), so the three groups stay separable where they overlap and in greyscale.

---

## Top row — does the cost RANK correctly?

This is the question the transpiler pass actually needs answered: given several
(decomposition, placement) candidates, does picking the lowest cost pick a good
one? Ranking is all that matters here; absolute values are irrelevant.

**How to read it.** Points on the dashed `y = x` line mean predicted = observed.
Points *above* the line mean the surrogate under-predicts the error (it is
optimistic). What matters for ranking is not the distance from the line but
whether the cloud is **monotone** — going right must mean going up.

**What it shows.** Both panels are tight, monotone bands. Pooled Spearman ρ:

- **C0: ρ = +0.9957** (τ = +0.9543)
- **C1: ρ = +0.9993** (τ = +0.9843)

Within each decomposition separately — i.e. placement discrimination alone, the
harder task, with the easy between-decomposition signal removed — C1 holds up:
ρ = 0.9994 (D1), 0.9966 (D2), 0.9985 (Fredkin), against C0's 0.9925 / 0.9919 /
0.9895.

The three groups sit at different places along the band because they have
different gate counts: D2 Margolus uses 6 CZ (depth 28), D1 Barenco 12 CZ
(depth 44), Fredkin 14 CZ (depth 52). The cheapest candidates are all D2 and the
most expensive are all Fredkin, which is the expected ordering and not itself
evidence of anything subtle.

**The limitation of this row:** at ρ ≈ 0.99 both panels look like the same
near-perfect diagonal. The eye cannot separate 0.9957 from 0.9993, and the
systematic offset from the line is compressed by the log scale. That is what the
bottom row is for.

---

## Bottom row — is the cost CALIBRATED?

Ranking is scale-free: a surrogate can rank perfectly while mis-predicting the
magnitude by a systematic factor. This row divides out the diagonal, turning that
factor into the y-axis.

The cost is a sum of `−ln(1 − ε)` terms, so the fidelity it predicts is
`1 − e^(−C)`; the ratio plotted is that over the simulated average-gate
infidelity. Dashed line at 1.0 = perfect calibration. Solid line = the median.
A ratio below 1 means the surrogate is optimistic.

**What it shows — this is the substantive result:**

- **C0's error is not a constant offset, it drifts.** The ratio climbs from ~0.64
  at the cheap end to ~0.89 at the expensive end. Median 0.797, **spread 0.255**.
  A drift with circuit size is the signature of a missing term that accumulates
  with duration — i.e. exactly the idle decoherence C0 omits. **No single scalar
  correction can fix a drift.**
- **C1 largely flattens it.** Ratio sits near 0.87 across the whole range.
  Median 0.872, range 0.807–0.922, **spread 0.115** — less than half of C0's.
  With the trend mostly removed, one scalar (≈ 1/0.87) would turn C1 into a
  usable calibrated infidelity estimate. This is the concrete payoff of the idle
  term, and it is much larger than the +0.0036 change in ρ suggests.
- **The residual ~13% is shared by all three decompositions**, not concentrated
  in one. That points to a systematic surrogate bias (additivity in log-fidelity
  ignores how errors compose) rather than one catalogue entry being modelled
  worse than the others.
- C1 still tilts slightly upward at the top end, so the linearised idle term does
  not fully exhaust the effect.

---

## What the figure does NOT show

Stated explicitly because the plot invites over-reading:

1. **This is not a hardware result.** The Aer noise model is built from the same
   FakeTorino calibration snapshot that feeds the cost function. The figure tests
   the **aggregation model** — additivity in log-fidelity, linearised idle penalty
   — and says nothing about whether that snapshot resembles the real device. It is
   a necessary condition for the pass to work, not a sufficient one.
2. **Three decompositions, one snapshot, one backend.** ρ = 0.9993 is a
   within-sample number. Nothing here establishes that it generalises to the full
   catalogue or to another device.
3. **24 of the 150 rows are not plotted.** They are the stale-calibration rows
   (cost = ∞ by policy), 8 per decomposition, all from the same 8 bad placements
   (58-59-72, 15-19-20, 22-21-34, 67-74-86, 74-86-87, 84-85-86, 95-96-97,
   97-110-116). Their observed infidelity has median 0.984 versus 0.079 for the
   finite rows, so the policy is discarding genuinely bad placements rather than
   arbitrary ones — but they are excluded from every ρ in the figure, which
   therefore describes the surrogate's behaviour *on the rows it is willing to
   score*.
4. **The ancilla-using entries (D6 Selinger, D8 Jones) are absent.** They need a
   subspace-restricted fidelity and are skipped by `observed_infidelity`.

---

## Numbers that are in the text report but not the figure

Run `python aer_validation.py` for the full report. Two blocks worth knowing:

**Decision quality.** Both C0 and C1 pick D2 Margolus @ 31-32-33, which *is* the
true best candidate — regret 1.000×. For scale, the worst finite candidate is
14.5× worse than the best, so there was a real decision to get wrong.

**Discordant pairs.** Out of 861 within-decomposition pairs each: D1 4, D2 16,
Fredkin 7. Every inversion is between candidates C1 considers near-tied (ΔC1 of
order 1e-4 to 3e-3), so the misrankings cost essentially nothing in practice.

---

## Regenerating

Full run — re-simulates everything, rewrites both the CSV and the PNG:

```
python aer_validation.py --placements 50
```

**Note:** `qiskit-aer` is currently *not* in `cost_function_benchmarks/pyproject.toml`,
so this fails at import under `uv run` until that dependency is added. The
committed PNG was last re-rendered from the existing CSV without re-simulating —
`plot()` reads only CSV columns, so the plotted values are the 30 Jul run's.
