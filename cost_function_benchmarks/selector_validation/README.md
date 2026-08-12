# Selector Validation

**Author:** Tapasi Patra  
**QIntern 2026 — Project 19**

## What this does
Scores all 10 Toffoli decompositions from the catalogue using Luke's C1 cost function, picks the best placement per decomposition, runs noisy simulation validation under a FakeTorino Aer noise model, and computes **Spearman rank correlation (ρ)** between predicted C1 ranking and empirical success rate.

## Key result
ρ = −0.8954, p = 0.0011 — lower predicted C1 genuinely corresponds to higher real success rate. Strong, statistically significant.

## Dependencies
These files must be present in the parent `cost_function_benchmarks/` folder before running:
- `noise_cost.py` (Luke's cost function)
- `catalogue.py` (Shruti's decomposition catalogue)
- `layouts.py` (Shruti's layout generator)
- `circuits/` folder with all 10 decomposition files (Shruti's)

## How to run
```bash
uv add scipy qiskit-aer
uv run selector_validation.py
```

## Output
- Selector ranking table (best placement per decomposition, by C1)
- Zero-noise control (sanity check — should be ~1.0 for all rows)
- Noisy validation success rates
- Spearman ρ and p-value

## Notes
- Tested on FakeTorino (real IBM Heron calibration snapshot)
- D8_Jones excluded from validation — no correctness definition yet (verify="skip")
- D6_Selinger and D8_Jones use ancillas which breaks C1's constant-readout assumption — flagged as a known limitation
