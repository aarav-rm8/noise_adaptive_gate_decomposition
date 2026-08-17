"""
transpile_all.py
----------------
Transpiles all 10 decompositions to IBM Heron native basis {CZ, RZ, SX, X}
using a heavy-hex backend (approximation of FakeTorino).

For each decomposition, tries multiple physical qubit placements and records
hardware metrics for each.

Output: results.json

NOTE: On your machine, replace GenericBackendV2 with FakeTorino for accurate results:
    from qiskit_ibm_runtime.fake_provider import FakeTorino
    backend = FakeTorino()
"""

import json
from qiskit import transpile
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap

# from circuits import (
#     d1_barenco, d2_maslov, d3_amy, d4_cruz_linear,
#     d5_nielsen_chuang, d6_selinger, d7_vale,
#     d8_jones, d9_zero_ancilla, d10_alt
# )
from layouts import generate_layouts
# ----------------------------------------------------------------
# Backend: heavy-hex (approximates IBM Heron / FakeTorino)
# ----------------------------------------------------------------
coupling_map = CouplingMap.from_heavy_hex(3)  # 19 qubits
backend = GenericBackendV2(
    num_qubits=19,
    basis_gates=["cz", "rz", "sx", "x"],
    coupling_map=coupling_map,
)

# ----------------------------------------------------------------
# (label, builder, num_data_qubits)
# num_data_qubits used to pick placements
# ----------------------------------------------------------------
# DECOMPOSITIONS = [
#     ("D1_Barenco",        d1_barenco.build,        3),
#     ("D2_Maslov",         d2_maslov.build,         3),
#     ("D3_Amy",            d3_amy.build,            3),
#     ("D4_Cruz_Linear",    d4_cruz_linear.build,    3),
#     ("D5_Nielsen_Chuang", d5_nielsen_chuang.build, 3),
#     ("D6_Selinger",       d6_selinger.build,       7),
#     ("D7_Vale",           d7_vale.build,           3),
#     ("D8_Jones",          d8_jones.build,          4),
#     ("D9_Zero_Ancilla",   d9_zero_ancilla.build,   3),
#     ("D10_Alt",           d10_alt.build,           3),
# ]



from catalogue import CATALOGUE
from layouts import generate_layouts

ALL_LAYOUTS = {
    3: generate_layouts(coupling_map, 3),
    4: generate_layouts(coupling_map, 4),
    7: generate_layouts(coupling_map, 7),
}
# PLACEMENTS = {
#     3: [[0,13,1], [1,14,2], [3,15,4], [4,16,5]],
#     4: [[0,13,1,14]],
#     7: [[0,13,1,14,2,15,3]],
# }

def transpile_and_measure(qc, layout):
    tqc = transpile(qc, backend=backend, initial_layout=layout, optimization_level=3)
    ops = tqc.count_ops()
    cz_pairs = set()
    for inst in tqc.data:
        if inst.operation.name == "cz":
            pair = tuple(sorted([tqc.find_bit(b).index for b in inst.qubits]))
            cz_pairs.add(pair)
    return {
        "layout":   layout,
        "cz":       ops.get("cz", 0),
        "sx":       ops.get("sx", 0),
        "rz":       ops.get("rz", 0),
        "x":        ops.get("x",  0),
        "depth":    tqc.depth(),
        "cz_pairs": sorted(cz_pairs),
    }


def run():
    all_results = {}

    for item in CATALOGUE:

        label = item["name"]
        builder = item["builder"]
        layout_type = item["layout_type"]

        print(f"\n{'='*60}")
        print(label)
        print(f"{'='*60}")

        qc = builder()
        # placements = PLACEMENTS[layout_type]
        placements = ALL_LAYOUTS[layout_type]

        results_for_decomp = []
        print(len(placements)) #new

        for layout in placements:
            try:
                m = transpile_and_measure(qc, layout)
                results_for_decomp.append(m)

                print(
                    f"  layout {layout}: "
                    f"CZ={m['cz']} "
                    f"SX={m['sx']} "
                    f"depth={m['depth']}"
                )

            except Exception as e:
                print(f"  layout {layout}: FAILED -- {e}")

        all_results[label] = results_for_decomp

    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("\nResults saved to results.json")

if __name__ == "__main__":
    run()
