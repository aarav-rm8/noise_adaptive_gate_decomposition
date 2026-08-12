"""
selector_validation.py — Core Selector Logic + Noisy Simulation Validation
QIntern 2026, Project 19. Tapasi + Luke, Core Selector task.

Two stages:
  1. SELECTOR: score every (decomposition, placement) pair in Shruti's
     CATALOGUE using Luke's C1 cost function (noise_cost.py), pick the best
     placement per decomposition, rank decompositions by their best C1.
  2. VALIDATION: rebuild each decomposition's best-placement circuit for all
     8 computational-basis inputs, run each under an Aer noise model built
     from the SAME backend calibration Luke's C1 reads from, and measure the
     empirical success rate. Then compute Spearman rank correlation (rho)
     between predicted ranking (C1, lower=better) and empirical ranking
     (success rate, higher=better) to check the selector actually predicts
     hardware performance.

KNOWN GAPS — flag to Luke/Aarav before trusting numbers:

  (a) D8_Jones has verify="skip" in verify.py: it's a relative-phase
      Toffoli*, not exact CCX, so "correct output" isn't defined the same
      way as the other nine decompositions. It's scored by the selector
      (Stage 1) but EXCLUDED from noisy validation (Stage 2) until we get a
      measurement-correction definition for it.

  (b) D6_Selinger (7q/4 ancilla) and D8_Jones (4q/1 ancilla) break the
      "readout is a constant offset across candidates, cannot change
      ranking" assumption that noise_cost.py's C0 relies on to justify
      excluding measurement error. Once these enter a head-to-head C1
      comparison against 3-qubit candidates, that assumption no longer
      holds. Flagged, not fixed here — needs a decision from Luke on
      whether to add a per-ancilla-count readout penalty to C1.

  (c) FRAGILE: the bit-ordering translation between Qiskit's little-endian
      statevector/counts strings and `data_qubits` indices (see
      `_ideal_output_bits` and the measurement loop in
      `empirical_success_rate`) has NOT been tested against a running
      Qiskit install. Before trusting any Spearman number, sanity-check
      this against verify.py's own basis_state_sim / measurement_sim
      results on D1/D2 (where the answer is already known to be "PASS").

Run:
    uv run selector_validation.py
Needs: qiskit, qiskit_ibm_runtime, qiskit-aer, scipy, numpy
"""

from __future__ import annotations

import math
import random
import statistics

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeTorino
from scipy.stats import spearmanr

from catalogue import CATALOGUE
from layouts import generate_layouts
from noise_cost import extract_calibration, score

SEED_TRANSPILER = 7
OPT_LEVEL = 1
SHOTS = 4096
MAX_LAYOUTS_PER_SIZE = 25  # cap search cost per layout width; random-sampled


# --------------------------------------------------------------------------- #
# Stage 1 — Selector: score every (decomposition, placement), pick the best   #
# --------------------------------------------------------------------------- #

def best_placement_per_decomposition(backend, calib):
    """One row per decomposition: its best (min-C1) placement, plus every
    candidate row for auditing. Skips a decomposition entirely only if every
    placement it was tried on came back with inf C1 (stale calibration)."""
    random.seed(0)
    layout_cache: dict[int, list[tuple]] = {}
    best_rows, all_rows = [], []

    for item in CATALOGUE:
        k = item["layout_type"]
        if k not in layout_cache:
            layouts = generate_layouts(backend.coupling_map, k)
            if len(layouts) > MAX_LAYOUTS_PER_SIZE:
                layouts = random.sample(layouts, MAX_LAYOUTS_PER_SIZE)
            layout_cache[k] = layouts
        placements = layout_cache[k]

        qc = item["builder"]()
        rows = []
        for pl in placements:
            try:
                tqc = transpile(
                    qc, backend,
                    initial_layout=list(pl),
                    optimization_level=OPT_LEVEL,
                    seed_transpiler=SEED_TRANSPILER,
                    scheduling_method="asap",
                )
            except Exception as e:
                continue  # placement infeasible for this width/topology
            s = score(tqc, calib)
            rows.append({"name": item["name"], "item": item, "placement": pl, **s})

        finite = [r for r in rows if not math.isinf(r["c1"])]
        if not finite:
            print(f"[WARN] {item['name']}: all placements had inf C1 (stale calibration) — skipped")
            continue

        finite.sort(key=lambda r: r["c1"])
        best_rows.append(finite[0])
        all_rows.extend(rows)

    return best_rows, all_rows


# --------------------------------------------------------------------------- #
# Stage 2 — Noisy validation: empirical success rate on the best placement    #
# --------------------------------------------------------------------------- #

def _ideal_output_bits(bits: int, logical_ccx: tuple[int, int, int]) -> str:
    """Dominant Qiskit-ordered bitstring for CCX(*logical_ccx) applied to
    computational-basis input `bits` on a 3-qubit reference — same
    convention verify.py's measurement_sim uses."""
    ref = QuantumCircuit(3)
    if bits & 1:
        ref.x(0)
    if bits & 2:
        ref.x(1)
    if bits & 4:
        ref.x(2)
    ref.ccx(*logical_ccx)
    probs = Statevector.from_instruction(ref).probabilities_dict()
    return max(probs, key=probs.get)  # e.g. '101', Qiskit little-endian (qubit0 = rightmost char)


def _success_rate(item, backend, placement, shots, sim):
    """Shared core: rebuilds the decomposition for all 8 basis inputs,
    transpiles each with the SAME placement/settings used for C1 scoring,
    runs on `sim`, returns mean success probability across inputs.

    Root-cause fix (see module docstring, gap c): input prep, the
    decomposition, AND measurement are all built as ONE logical circuit and
    transpiled together. Candidate placements like (87,88,89) are often a
    linear chain, but CCX needs pairwise interaction between all 3 qubits,
    so the router inserts SWAPs mid-circuit. Measuring fixed physical qubits
    AFTER transpiling (the old, buggy approach) reads the wrong logical
    qubit once a SWAP has moved it elsewhere -- confirmed via the zero-noise
    control below, which produced a clean cyclic permutation of results
    (1.0/0.5/0.25 success rates instead of 1.0 everywhere). Measuring the
    logical qubits before transpiling lets the router carry the
    measurements along with everything else, tracking each qubit through
    any SWAPs automatically.
    """
    if item["verify"] == "skip":
        return None

    logical_ccx = item.get("logical_ccx", (0, 1, 2))
    data_qubits = item["data_qubits"] if item["data_qubits"] is not None else [0, 1, 2]

    per_input_success = []
    for bits in range(8):
        ideal_bits = _ideal_output_bits(bits, logical_ccx)
        # ideal_bits is over 3 logical qubits; pull out the data-qubit chars.
        # Qiskit string is little-endian (index 0 = rightmost char).
        ideal_data = "".join(ideal_bits[::-1][dq] for dq in data_qubits)[::-1]

        test = QuantumCircuit(item["num_qubits"], len(data_qubits))
        if bits & 1:
            test.x(0)
        if bits & 2:
            test.x(1)
        if bits & 4:
            test.x(2)
        test.compose(item["builder"](), inplace=True)
        for i, dq in enumerate(data_qubits):
            test.measure(dq, i)

        tqc = transpile(
            test, backend,
            initial_layout=list(placement),
            optimization_level=OPT_LEVEL,
            seed_transpiler=SEED_TRANSPILER,
            scheduling_method="asap",
        )

        counts = sim.run(tqc, shots=shots).result().get_counts()
        per_input_success.append(counts.get(ideal_data, 0) / shots)

    return statistics.mean(per_input_success)


def zero_noise_success_rate(item, backend, placement, shots=SHOTS):
    """NO noise model -- a permanent sanity control. Every non-skipped
    decomposition should score ~1.0 here; anything meaningfully below that
    means a circuit-construction or routing bug, not real physics, and the
    noisy numbers below should not be trusted until this returns ~1.0 for
    every row."""
    return _success_rate(item, backend, placement, shots, sim=AerSimulator())


def empirical_success_rate(item, backend, placement, shots=SHOTS):
    """Same as zero_noise_success_rate but under an Aer noise model built
    from `backend`'s calibration -- the real validation number. Returns
    None for verify=="skip" (see module docstring, gap a)."""
    noise_model = NoiseModel.from_backend(backend)
    sim = AerSimulator(noise_model=noise_model)
    return _success_rate(item, backend, placement, shots, sim=sim)


# --------------------------------------------------------------------------- #
# Main — tie both stages together, report Spearman correlation                #
# --------------------------------------------------------------------------- #

def main():
    backend = FakeTorino()
    calib = extract_calibration(backend)
    print(f"backend: {calib.backend_name}\n")

    best_rows, _all_rows = best_placement_per_decomposition(backend, calib)
    best_rows.sort(key=lambda r: r["c1"])

    print("=" * 70)
    print("SELECTOR RANKING (best placement per decomposition, by C1)")
    print("=" * 70)
    for r in best_rows:
        print(f"  {r['name']:22s}  C1={r['c1']:.5f}  placement={r['placement']}")

    print("\n" + "=" * 70)
    print("ZERO-NOISE CONTROL (should be ~1.0 for every non-skipped row)")
    print("=" * 70)
    control_ok = True
    for r in best_rows:
        zr = zero_noise_success_rate(r["item"], backend, r["placement"])
        if zr is None:
            continue
        flag = "" if zr > 0.99 else "  <-- BUG: circuit/routing issue, not noise"
        if zr <= 0.99:
            control_ok = False
        print(f"  {r['name']:22s}  zero_noise_success={zr:.4f}{flag}")

    if not control_ok:
        print(
            "\n[!] At least one decomposition failed the zero-noise control.\n"
            "    Fix the circuit construction / measurement mapping for the\n"
            "    flagged row(s) before trusting anything below this point.\n"
        )

    print("\n" + "=" * 70)
    print("NOISY VALIDATION (empirical success rate on that placement)")
    print("=" * 70)
    validated = []
    for r in best_rows:
        rate = empirical_success_rate(r["item"], backend, r["placement"])
        if rate is None:
            print(f"  {r['name']:22s}  SKIPPED (verify=skip, gap a — no ground truth defined)")
            continue
        validated.append({"name": r["name"], "c1": r["c1"], "success": rate})
        print(f"  {r['name']:22s}  C1={r['c1']:.5f}  success_rate={rate:.4f}")

    if len(validated) >= 3:
        c1_vals = [v["c1"] for v in validated]
        succ_vals = [v["success"] for v in validated]
        rho, pval = spearmanr(c1_vals, succ_vals)
        print("\n" + "=" * 70)
        print(f"Spearman rho(C1, success_rate) = {rho:.4f}   (p = {pval:.4f})")
        print("Expect rho << 0: lower predicted cost should mean higher success.")
        print("=" * 70)
    else:
        print("\n[not enough validated decompositions for a meaningful Spearman rho]")


if __name__ == "__main__":
    main()