"""
run_first_numbers.py — first end-to-end C0/C1 numbers on FakeTorino.

Scores two Toffoli catalogue entries that can be built straight from the Qiskit
library (they correspond to Shruti's D1 and D2):

    D1  Barenco exact Toffoli   (CCXGate  -> 6-CNOT canonical decomposition)
    D2  Margolus relative-phase (RCCXGate -> 3-CNOT, relative-phase flag = True)

across a sample of connected linear qubit triples, with fixed transpile settings
(optimization_level=1, seed_transpiler=7, scheduling_method='asap' for the idle
term). Costs are per (decomposition, placement) pair — the placement column IS
part of the result, per the integration note.

Run:  python3 run_first_numbers.py
Out:  first_numbers.csv + a console summary + first_numbers.png (needs matplotlib).
"""

import csv
import math
import random
import statistics

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CCXGate, RCCXGate
from qiskit_ibm_runtime.fake_provider import FakeTorino

from noise_cost import extract_calibration, score

SEED_TRANSPILER = 7
OPT_LEVEL = 1
N_PLACEMENTS = 20


def linear_triples(coupling_map):
    """All i-j-k with (i,j) and (j,k) edges, i < k to deduplicate reversals."""
    adj = {}
    for a, b in coupling_map.get_edges():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    triples = []
    for j, nbrs in adj.items():
        ns = sorted(nbrs)
        for i in ns:
            for k in ns:
                if i < k:
                    triples.append((i, j, k))
    return triples


def build_candidates():
    d1 = QuantumCircuit(3, name="D1_barenco_exact")
    d1.append(CCXGate(), [0, 1, 2])
    d2 = QuantumCircuit(3, name="D2_margolus_relphase")
    d2.append(RCCXGate(), [0, 1, 2])
    return [("D1 Barenco (exact)", d1, False), ("D2 Margolus (rel-phase)", d2, True)]


def main():
    backend = FakeTorino()
    calib = extract_calibration(backend)
    print(f"backend: {calib.backend_name}  |  dt = {calib.dt * 1e9:.0f} ns")

    triples = linear_triples(backend.coupling_map)
    random.seed(0)
    placements = random.sample(triples, N_PLACEMENTS)
    print(
        f"{len(triples)} connected linear triples on the device; "
        f"sampling {N_PLACEMENTS}\n"
    )

    rows = []
    for label, qc, relphase in build_candidates():
        for pl in placements:
            tqc = transpile(
                qc,
                backend,
                initial_layout=list(pl),
                optimization_level=OPT_LEVEL,
                seed_transpiler=SEED_TRANSPILER,
                scheduling_method="asap",
            )
            s = score(tqc, calib)
            rows.append(
                {
                    "decomposition": label,
                    "relative_phase": relphase,
                    "placement": "-".join(map(str, pl)),
                    "cz": s["cz_count"],
                    "sx": s["sx_count"],
                    "x": s["x_count"],
                    "rz": s["rz_count"],
                    "depth": s["depth"],
                    "C0": round(s["c0"], 6),
                    "idle": round(s["idle_penalty"], 6),
                    "C1": round(s["c1"], 6),
                }
            )

    with open("first_numbers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n_stale = len({r["placement"] for r in rows if math.isinf(r["C1"])})
    if n_stale:
        print(
            f"[stale-calibration policy] {n_stale}/{N_PLACEMENTS} placements "
            f"excluded (an edge reports eps=1 in this snapshot) -> cost inf, "
            f"never selected, logged. Working as specified (note S6).\n"
        )

    for label, _, _ in build_candidates():
        sub = sorted(
            (
                r
                for r in rows
                if r["decomposition"] == label and not math.isinf(r["C1"])
            ),
            key=lambda r: r["C1"],
        )
        c1s = [r["C1"] for r in sub]
        best, worst = sub[0], sub[-1]
        print(f"== {label} ==  ({len(sub)} finite placements)")
        print(
            f"  best : C1={best['C1']:.5f}  (C0={best['C0']:.5f}, "
            f"idle={best['idle']:.5f})  placement {best['placement']}  "
            f"cz={best['cz']} depth={best['depth']}"
        )
        print(f"  worst: C1={worst['C1']:.5f}  placement {worst['placement']}")
        print(
            f"  spread worst/best = {worst['C1'] / best['C1']:.2f}x   "
            f"median C1 = {statistics.median(c1s):.5f}\n"
        )

    # head-to-head at each finite placement
    wins = total = 0
    for pl in placements:
        key = "-".join(map(str, pl))
        a = next(
            r
            for r in rows
            if r["placement"] == key and r["decomposition"].startswith("D1")
        )
        b = next(
            r
            for r in rows
            if r["placement"] == key and r["decomposition"].startswith("D2")
        )
        if math.isinf(a["C1"]) or math.isinf(b["C1"]):
            continue
        total += 1
        wins += b["C1"] < a["C1"]
    print(
        f"D2 (rel-phase) beats D1 at {wins}/{total} finite placements "
        f"(expected: rel-phase halves the CZ count; the relative-phase flag "
        f"decides whether it's admissible in context)."
    )
    print("\nwrote first_numbers.csv")
    plot_results()


def plot_results(csv_path="first_numbers.csv", out_png="first_numbers.png"):
    """Plot the CSV: one stacked bar (C0 + idle = C1) per decomposition per
    placement, placements sorted best -> worst. Reads the CSV rather than the
    in-memory rows, so it can also be run standalone on an existing file:

        python3 -c "from run_first_numbers import plot_results; plot_results()"
    """
    import math

    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("[plot skipped] matplotlib not installed  ->  pip install matplotlib")
        return

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("C0", "idle", "C1"):
            r[k] = float(r[k])

    # first-seen order of decompositions; drop placements any candidate scored inf
    decs = list(dict.fromkeys(r["decomposition"] for r in rows))
    by_pl = {}
    for r in rows:
        by_pl.setdefault(r["placement"], {})[r["decomposition"]] = r
    n_stale = sum(any(math.isinf(d[l]["C1"]) for l in decs) for d in by_pl.values())
    finite = {
        p: d for p, d in by_pl.items() if all(not math.isinf(d[l]["C1"]) for l in decs)
    }
    placements = sorted(finite, key=lambda p: min(finite[p][l]["C1"] for l in decs))

    colors = ["#0173B2", "#DE8F05", "#029E73", "#CC78BC"]  # colourblind-safe
    x = np.arange(len(placements))
    width = 0.8 / len(decs)

    fig, ax = plt.subplots(figsize=(12, 5.5))
    for i, label in enumerate(decs):
        pos = x + (i - (len(decs) - 1) / 2) * width
        c0s = [finite[p][label]["C0"] for p in placements]
        idles = [finite[p][label]["idle"] for p in placements]
        c = colors[i % len(colors)]
        ax.bar(pos, c0s, width * 0.92, color=c, label=f"{label} — C0 (gate errors)")
        ax.bar(
            pos,
            idles,
            width * 0.92,
            bottom=c0s,
            color=c,
            alpha=0.45,
            hatch="//",
            edgecolor="white",
            linewidth=0,
            label=f"{label} — idle term",
        )

    best = min(min(finite[p][l]["C1"] for l in decs) for p in placements)
    worst = max(max(finite[p][l]["C1"] for l in decs) for p in placements)
    ax.set_title(
        f"Predicted cost per (decomposition, placement) — "
        f"{worst / best:.1f}x spread across placements",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("placement (physical qubit triple, sorted best \u2192 worst)")
    ax.set_ylabel(r"predicted cost  $-\ln\,\bar F$   (C1 = C0 + idle)")
    ax.set_xticks(x)
    ax.set_xticklabels(placements, rotation=45, ha="right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=9)
    if n_stale:
        fig.text(
            0.99,
            0.01,
            f"{n_stale} placement(s) excluded: stale calibration "
            f"(\u03b5=1) \u2192 cost \u221e, never selected",
            ha="right",
            fontsize=8,
            style="italic",
            color="0.4",
        )

    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"wrote {out_png}")
    if "agg" not in plt.get_backend().lower():  # only pop a window if interactive
        plt.show()


if __name__ == "__main__":
    main()
