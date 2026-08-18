"""
transpile_all.py
----------------
Transpiles all 10 Fredkin decompositions to IBM Heron native basis {CZ, RZ, SX, X}
using a heavy-hex backend (approximation of FakeTorino).

For each decomposition, tries every connected 3-qubit physical placement and
records hardware metrics for each.

Output: results.json

Run from the nan/ directory:
    python transpile_all.py
"""

import json
import sys
import os

from qiskit import transpile
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap

from catalogue import CATALOGUE
from layouts import generate_layouts

# ----------------------------------------------------------------
# Backend: heavy-hex (approximates IBM Heron / FakeTorino, 19 qubits)
# ----------------------------------------------------------------
coupling_map = CouplingMap.from_heavy_hex(3)  # 19 qubits
backend = GenericBackendV2(
    num_qubits=19,
    basis_gates=["cz", "rz", "sx", "x"],
    coupling_map=coupling_map,
)

# Pre-generate all connected layouts by size
ALL_LAYOUTS = {
    3: generate_layouts(coupling_map, 3),
    4: generate_layouts(coupling_map, 4),
    7: generate_layouts(coupling_map, 7),
}


def transpile_and_measure(qc, layout):
    tqc = transpile(qc, backend=backend, initial_layout=list(layout), optimization_level=3)
    ops = tqc.count_ops()
    cz_pairs = set()
    for inst in tqc.data:
        if inst.operation.name == "cz":
            pair = tuple(sorted([tqc.find_bit(b).index for b in inst.qubits]))
            cz_pairs.add(pair)
    return {
        "layout":   list(layout),
        "cz":       ops.get("cz", 0),
        "sx":       ops.get("sx", 0),
        "rz":       ops.get("rz", 0),
        "x":        ops.get("x",  0),
        "depth":    tqc.depth(),
        "cz_pairs": sorted([list(p) for p in cz_pairs]),
    }


def run():
    all_results = {}

    for item in CATALOGUE:
        label        = item["name"]
        builder      = item["builder"]
        layout_type  = item["layout_type"]

        print(f"\n{'='*60}")
        print(label)
        print(f"{'='*60}")

        qc = builder()
        placements = ALL_LAYOUTS[layout_type]
        print(f"  Trying {len(placements)} layouts...")

        results_for_decomp = []

        for layout in placements:
            try:
                m = transpile_and_measure(qc, layout)
                results_for_decomp.append(m)
                print(
                    f"  layout {list(layout)}: "
                    f"CZ={m['cz']} SX={m['sx']} depth={m['depth']}"
                )
            except Exception as e:
                print(f"  layout {list(layout)}: FAILED -- {e}")

        all_results[label] = results_for_decomp

    out_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    run()
