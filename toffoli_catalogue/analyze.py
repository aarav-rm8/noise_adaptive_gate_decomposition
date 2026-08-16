"""
analyze.py
----------
Loads results.json and prints a clean summary table.
Checks that each CZ pair used is a real edge on the backend.

Run after transpile_all.py.
"""

import json
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap

# same backend as transpile_all.py
coupling_map = CouplingMap.from_heavy_hex(3)
backend = GenericBackendV2(
    num_qubits=19,
    basis_gates=["cz", "rz", "sx", "x"],
    coupling_map=coupling_map,
)
VALID_EDGES = set(
    tuple(sorted(e)) for e in coupling_map.get_edges()
)


def check_compatibility(cz_pairs: list) -> bool:
    for pair in cz_pairs:
        if tuple(pair) not in VALID_EDGES:
            return False
    return True


def run():
    with open("results.json") as f:
        results = json.load(f)

    print(f"\n{'Decomp':<15} {'Layout':<22} {'CZ':<5} {'SX':<5} "
          f"{'Depth':<8} {'HW Compatible'}")
    print("-" * 70)

    for label, entries in results.items():
        for m in entries:
            compat = check_compatibility(m["cz_pairs"])
            layout_str = str(m["layout"])
            status = "YES" if compat else "NO (check pairs)"
            print(
                f"{label:<15} {layout_str:<22} {m['cz']:<5} {m['sx']:<5} "
                f"{m['depth']:<8} {status}"
            )


if __name__ == "__main__":
    run()


import json
import statistics

with open("results.json", "r") as f:
    results = json.load(f)

summary = {}

print("\n" + "=" * 95)
print("SUMMARY")
print("=" * 95)

print(
    f"{'Decomposition':<22}"
    f"{'Layouts':>8}"
    f"{'Min CZ':>8}"
    f"{'Avg CZ':>10}"
    f"{'Min SX':>8}"
    f"{'Avg SX':>10}"
    f"{'Min Depth':>12}"
    f"{'Avg Depth':>12}"
)

print("-" * 95)

for name, entries in results.items():

    czs = [e["cz"] for e in entries]
    sxs = [e["sx"] for e in entries]
    depths = [e["depth"] for e in entries]

    summary[name] = {
        "layouts": len(entries),
        "min_cz": min(czs),
        "avg_cz": round(statistics.mean(czs), 2),
        "min_sx": min(sxs),
        "avg_sx": round(statistics.mean(sxs), 2),
        "min_depth": min(depths),
        "avg_depth": round(statistics.mean(depths), 2),
    }

    print(
        f"{name:<22}"
        f"{len(entries):>8}"
        f"{min(czs):>8}"
        f"{statistics.mean(czs):>10.2f}"
        f"{min(sxs):>8}"
        f"{statistics.mean(sxs):>10.2f}"
        f"{min(depths):>12}"
        f"{statistics.mean(depths):>12.2f}"
    )

with open("summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\nSummary written to summary.json")

print("\nBEST RESULTS")
print("-" * 40)

best_cz = min(summary.items(), key=lambda x: x[1]["min_cz"])
best_depth = min(summary.items(), key=lambda x: x[1]["min_depth"])
best_sx = min(summary.items(), key=lambda x: x[1]["min_sx"])

print(f"Lowest CZ      : {best_cz[0]} ({best_cz[1]['min_cz']})")
print(f"Lowest Depth   : {best_depth[0]} ({best_depth[1]['min_depth']})")
print(f"Lowest SX      : {best_sx[0]} ({best_sx[1]['min_sx']})")