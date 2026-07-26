"""
score_results.py
================
Demo: run the C0/C1 cost functions end-to-end.

Part A (exact mode, the real validation path):
    Build two standard Toffoli decompositions, transpile them onto specific
    physical qubit triples of FakeTorino (Heron, real calibration snapshot),
    and score the scheduled circuits with C0 and C1.

Part B (JSON mode, integration with Shruti's pipeline):
    Read her results.json (GenericBackendV2 heavy-hex(3), 19 qubits) and
    compute approximate C0 per (decomposition, layout) using that same
    generic backend's calibration, since her layouts index ITS qubits.

Usage:  python score_results.py
"""

import json
import warnings

from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit_ibm_runtime.fake_provider import FakeTorino

from cost_function import extract_calibration, score_circuit, score_json_entry

warnings.filterwarnings("once")


# ---------------------------------------------------------------- Part A ---


def toffoli_standard() -> QuantumCircuit:
    """Canonical 6-CNOT Toffoli (Nielsen & Chuang Fig. 4.9)."""
    qc = QuantumCircuit(3, name="ccx_standard")
    qc.ccx(0, 1, 2)
    return qc


def toffoli_margolus() -> QuantumCircuit:
    """Margolus relative-phase Toffoli: 3 CNOTs, correct up to phase."""
    qc = QuantumCircuit(3, name="ccx_margolus")
    qc.rccx(0, 1, 2)
    return qc


def part_a():
    print("=" * 72)
    print("PART A -- exact scoring on FakeTorino (Heron calibration snapshot)")
    print("=" * 72)

    backend = FakeTorino()
    cal = extract_calibration(backend)

    # Two candidate physical triples (must be connected paths on Torino's map).
    cmap = CouplingMap(backend.coupling_map)
    edges = set(map(tuple, cmap.get_edges()))

    def connected_triple(a, b, c):
        return ((a, b) in edges or (b, a) in edges) and (
            (b, c) in edges or (c, b) in edges
        )

    # pick two arbitrary-but-valid triples to show placement dependence
    triples = []
    for a, b in sorted(edges):
        for b2, c in sorted(edges):
            if b2 == b and c != a and connected_triple(a, b, c):
                triples.append((a, b, c))
        if len(triples) >= 40:
            break
    placements = [triples[0], triples[len(triples) // 2]]

    print(
        f"\n{'decomposition':<16} {'placement':<16} "
        f"{'C0':>10} {'C1':>10} {'idle':>10} {'2Q':>4} {'1Q':>4}"
    )
    print("-" * 72)

    for build in (toffoli_standard, toffoli_margolus):
        for placement in placements:
            qc = build()
            tqc = transpile(
                qc,
                backend=backend,
                initial_layout=list(placement),
                optimization_level=1,
                seed_transpiler=42,
            )
            s = score_circuit(tqc, backend=backend, cal=cal)
            print(
                f"{qc.name:<16} {str(placement):<16} "
                f"{s['C0']:>10.5f} {s['C1']:>10.5f} "
                f"{s['idle_penalty']:>10.2e} {s['n_2q']:>4} {s['n_1q']:>4}"
            )

    print("\nNote: same decomposition, different placement -> different cost;")
    print("      relative-phase Margolus is cheaper but only valid when the")
    print("      phase doesn't matter downstream (flag in catalogue schema).")


# ---------------------------------------------------------------- Part B ---


def part_b():
    print("\n" + "=" * 72)
    print("PART B -- approximate C0 over Shruti's results.json")
    print("=" * 72)

    # Reconstruct her backend so the layout indices refer to the same qubits.
    # (GenericBackendV2 synthesises calibration values; seed pins them.)
    coupling_map = CouplingMap.from_heavy_hex(3)
    backend = GenericBackendV2(
        num_qubits=19,
        basis_gates=["cz", "rz", "sx", "x"],
        coupling_map=coupling_map,
        seed=42,
    )
    cal = extract_calibration(backend)

    with open("results.json") as f:
        results = json.load(f)

    print(
        f"\n{'decomposition':<18} {'best layout':<16} {'best C0':>10} "
        f"{'median C0':>11} {'worst C0':>10}"
    )
    print("-" * 72)

    summary = []
    for name, entries in results.items():
        scored = []
        for e in entries:
            try:
                s = score_json_entry(e, cal)
                scored.append((s["C0_approx"], e["layout"]))
            except KeyError:
                continue  # layout uses an edge absent from this coupling map
        if not scored:
            continue
        scored.sort()
        best_c0, best_layout = scored[0]
        med = scored[len(scored) // 2][0]
        worst = scored[-1][0]
        summary.append((best_c0, name, best_layout, med, worst))

    for best_c0, name, layout, med, worst in sorted(summary):
        print(
            f"{name:<18} {str(layout):<16} {best_c0:>10.5f} {med:>11.5f} {worst:>10.5f}"
        )

    print("\nCaveats (raise at check-in):")
    print(" * cz_pairs has no per-edge multiplicity -> uniform split approximation.")
    print(" * GenericBackendV2 calibration is synthetic -> rankings are plumbing")
    print("   proof, not physics. Swap in FakeTorino + re-transpile for real data.")
    print(" * No timing info in JSON -> C1 requires the exact-mode path (Part A).")


if __name__ == "__main__":
    part_a()
    part_b()
