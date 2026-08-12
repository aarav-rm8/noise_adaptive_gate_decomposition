# Noise-Adaptive Integration

**Author:** Tapasi Patra  
**QIntern 2026 — Project 19**

## What this does
Integrates noise-adaptive CCX decomposition selection into Qiskit's real transpiler pipeline. Selects the lowest-cost exact decomposition from the catalogue and substitutes it before layout/routing, producing a correctly transpiled native-gate circuit that is cheaper than the default pipeline.

## Key result
**~8.6% lower realized C1** than Qiskit's default decomposition on a Grover benchmark circuit (FakeTorino). Winner: D5_Nielsen_Chuang. Correctness verified — matches default pipeline's dominant measurement outcome exactly.

## Files

### `noise_adaptive_decomposition.py`
Core library. Contains:
- `best_decomposition_by_device_average()` — picks the single best exact candidate using device-average calibration (safe pre-layout)
- `substitute_ccx_pre_layout()` — substitutes that candidate into every CCX in a circuit before transpilation

### `run_phase1.py`
Pre-layout substitution using device-average cost. Safe, correct, neutral baseline (same decomposition as Qiskit default on this device — establishes the substitution pipeline).

### `run_phase2.py`
Runs the full pipeline independently per exact candidate, compares realized C1 across all runs, keeps the best. Achieves the real 8.6% improvement. Costs ~6x transpile time vs default — fine for benchmarking, worth optimising for production use.

## Dependencies
These files must be present in the parent `cost_function_benchmarks/` folder:
- `noise_cost.py` (Luke's cost function — uses `extract_calibration`, `score`)
- `catalogue.py` (Shruti's decomposition catalogue)
- `circuits/` folder with all 10 decomposition files (Shruti's)

## How to run
```bash
uv add mqt.bench qiskit-aer
uv run run_phase1.py   # Phase 1: safe baseline
uv run run_phase2.py   # Phase 2: best candidate, real improvement
```

## Design notes
- Only **exact** decompositions used (verify="operator") — D2/D7 (relative-phase) excluded because they silently break algorithms where CCX output feeds further coherent operations. Confirmed on a real Grover circuit.
- D6/D8 (ancilla-based) excluded from scope for this first integration pass.
- Phase 2 works by running the full pipeline per candidate rather than patching a routed circuit — Qiskit's router can't handle 3-qubit gates directly, so post-routing substitution is architecturally infeasible. This is a known limitation, flagged for future work.
- Tested on FakeTorino throughout, per team guidance to stay off real hardware during development.
