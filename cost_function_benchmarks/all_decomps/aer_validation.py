"""
aer_validation.py — does the predicted cost actually rank placements correctly?

QIntern 2026, Project 19. Validation harness for the C0/C1 cost functions
defined in noise_cost.py (formulation note, Devlin, 8 Jul 2026).

WHAT THIS TESTS
---------------
C0 and C1 are *additive* surrogates: C0 sums -ln(1-eps_g) over gates and C1
adds a linearised idle-decoherence term. Neither is the true infidelity of the
composed channel. This harness computes that true infidelity exactly, by
simulating the noisy circuit as a superoperator and comparing it to the ideal
target unitary, then measures how well the surrogates rank candidates:

    Spearman rho( predicted cost , observed infidelity )

reported separately for C0 and C1, pooled and within each decomposition.

WHAT THIS DOES *NOT* TEST
-------------------------
The Aer noise model is built from the same FakeTorino calibration snapshot that
feeds the cost function, so this cannot tell us whether that snapshot resembles
the real device. It is a test of the AGGREGATION MODEL (additivity in
log-fidelity, linearised idle penalty), not of the input data. It is a
necessary condition for the transpiler pass to work, not a sufficient one.
Hardware runs are the only way to test the input data. Say this out loud in the
write-up rather than letting a reader assume more than the experiment supports.

METHOD
------
1. Transpile candidate onto a physical triple with scheduling_method='asap'
   (identical settings to run_first_numbers.py, so rows are comparable).
2. Score with noise_cost.score  ->  C0, C1, counts, depth.
3. Localise: project the 133-qubit scheduled circuit down to just its active
   physical qubits, and replace every explicit Delay on an active qubit with a
   thermal_relaxation_error(T1, T2, tau) channel. Delays on inactive qubits are
   dropped. This is what makes the idle term visible to the simulator at all --
   NoiseModel.from_backend does not attach any error to 'delay'.
4. Build a noise model over those k qubits by remapping the device gate errors
   for exactly those qubits/edges (public helper: basic_device_gate_errors).
5. Simulate with AerSimulator(method='superop') and compute
   observed_infidelity = 1 - process_fidelity(SuperOp, target unitary).
6. Correlate.

SELF-CHECK
----------
Every candidate is first simulated noiselessly. If its process fidelity against
the declared target is not ~1, the localisation or the layout permutation is
wrong and the row is rejected rather than silently reported. This catches the
whole class of endianness / routing-permutation bugs that has bitten this
project before.

Run:  python aer_validation.py [--placements 20] [--out aer_validation.csv]
"""

from __future__ import annotations


import argparse
import csv
import itertools
import math
import random
import statistics
from dataclasses import dataclass

import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CCXGate, CSwapGate, PermutationGate, RCCXGate
from qiskit.quantum_info import Choi, Operator, SuperOp, process_fidelity
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error
from qiskit_aer.noise.device import basic_device_gate_errors
from qiskit_ibm_runtime.fake_provider import FakeTorino

from noise_cost import Calibration, extract_calibration, score

# Transpile settings — must match run_first_numbers.py exactly.
SEED_TRANSPILER = 7
OPT_LEVEL = 1
PLACEMENT_SEED = 0

# Anything at or below this counts as "the localisation reproduced the target".
IDEAL_FIDELITY_TOL = 1e-9

# Composing dozens of thermal-relaxation channels leaves a trace-preservation
# residual of order 1e-8. That is ~6 orders below the smallest infidelity we
# report, so it is numerical, not physical -- but it is checked rather than
# silenced, because a LARGE TP violation would mean the channel is malformed
# and every fidelity built on it would be meaningless.
TP_TOL = 1e-6

_NOISELESS = {"rz", "barrier", "delay"}
_SIM_GATES = ("cz", "sx", "x", "id", "rz")


# --------------------------------------------------------------------------- #
# Candidates                                                                  #
# --------------------------------------------------------------------------- #


@dataclass
class Candidate:
    """One catalogue entry: how to build it, and what it is *supposed* to do.

    `target` is the per-entry correctness reference. This is the metadata point
    from the catalogue discussion: a relative-phase Toffoli is not incorrect,
    it just has a different target unitary, and validating it against CCX would
    wrongly rank it as terrible. Every entry declares its own reference.
    """

    label: str
    circuit: QuantumCircuit
    target: Operator
    relative_phase: bool


def build_candidates() -> list[Candidate]:
    def wrap(gate, name):
        qc = QuantumCircuit(gate.num_qubits, name=name)
        qc.append(gate, range(gate.num_qubits))
        return qc

    return [
        Candidate(
            "D1 Barenco (exact)",
            wrap(CCXGate(), "D1"),
            Operator(CCXGate()),
            False,
        ),
        Candidate(
            "D2 Margolus (rel-phase)",
            wrap(RCCXGate(), "D2"),
            Operator(RCCXGate()),
            True,
        ),
        Candidate(
            "Fredkin (exact)",
            wrap(CSwapGate(), "CSWAP"),
            Operator(CSwapGate()),
            False,
        ),
    ]


def linear_triples(coupling_map):
    """All i-j-k with (i,j) and (j,k) edges, i < k. Same as run_first_numbers."""
    adj: dict[int, set[int]] = {}
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


# --------------------------------------------------------------------------- #
# Localisation: 133 physical qubits -> the k that actually do anything         #
# --------------------------------------------------------------------------- #


def active_qubits(tqc: QuantumCircuit) -> list[int]:
    active = set()
    for inst in tqc.data:
        if inst.operation.name not in _NOISELESS:
            for b in inst.qubits:
                active.add(tqc.find_bit(b).index)
    return sorted(active)


def _delay_seconds(inst, dt: float) -> float:
    dur, unit = inst.operation.duration, inst.operation.unit
    if unit == "dt":
        return dur * dt
    return {"s": 1.0, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}[unit] * dur


def localise(
    tqc: QuantumCircuit,
    cal: Calibration,
    phys_order: list[int],
    include_idle: bool = True,
) -> QuantumCircuit:
    """Rewrite `tqc` onto len(phys_order) qubits, local index i <-> phys_order[i].

    Gates keep their names so the local noise model can attach errors to them.

    With include_idle=True every explicit Delay on an active qubit becomes a
    thermal_relaxation_error(T1, T2, tau) channel: the simulator has no other
    way to see idle decoherence, and this is the exact channel whose
    linearisation gives the C1 idle term, which is the thing being tested.

    With include_idle=False delays are dropped, giving the unitary the circuit
    is *supposed* to implement. That version is the self-check reference --
    including the relaxation channels there would make even a perfectly
    localised circuit look wrong by ~1e-2.
    """
    index = {p: i for i, p in enumerate(phys_order)}
    small = QuantumCircuit(len(phys_order), name=f"{tqc.name}_local")

    for inst in tqc.data:
        name = inst.operation.name
        phys = [tqc.find_bit(b).index for b in inst.qubits]
        if any(p not in index for p in phys):
            # Instruction on an inactive wire. Only delays and barriers should
            # ever land here; a real gate would mean active_qubits() is wrong.
            if name not in ("delay", "barrier"):
                raise RuntimeError(f"{name}{tuple(phys)} outside the active set")
            continue
        local = [index[p] for p in phys]

        if name == "barrier":
            continue
        if name == "delay":
            if not include_idle:
                continue
            q = phys[0]
            tau = _delay_seconds(inst, cal.dt)
            t1, t2 = cal.t1.get(q), cal.t2.get(q)
            if tau <= 0 or not t1 or not t2:
                continue
            # Aer requires T2 <= 2*T1 for a valid relaxation channel.
            err = thermal_relaxation_error(t1, min(t2, 2 * t1), tau)
            small.append(err.to_instruction(), local)
            continue
        small.append(inst.operation, local)

    return small


def local_noise_model(device_errors, phys_order: list[int]) -> NoiseModel:
    """Remap the device gate errors for exactly these qubits onto 0..k-1."""
    index = {p: i for i, p in enumerate(phys_order)}
    nm = NoiseModel(basis_gates=list(_SIM_GATES))
    for name, qubits, error in device_errors:
        if name not in _SIM_GATES:
            continue
        if any(q not in index for q in qubits):
            continue
        nm.add_quantum_error(error, name, [index[q] for q in qubits], warnings=False)
    return nm


# --------------------------------------------------------------------------- #
# Observed infidelity                                                         #
# --------------------------------------------------------------------------- #


def _fidelity(chan: SuperOp, target: Operator) -> float:
    """process_fidelity, with the trace-preservation residual checked explicitly.

    Qiskit logs a warning for any TP violation, however small, and composing
    many relaxation channels always produces one at the 1e-8 level. Asserting a
    bound and then disabling the check is honest; blanket-suppressing the
    logger would also hide a genuinely malformed channel.
    """
    residual = float(np.max(np.abs(_tp_residual(chan))))
    if residual > TP_TOL:
        raise RuntimeError(
            f"channel is not trace-preserving to {TP_TOL:g} (residual {residual:.2e})"
        )
    return process_fidelity(chan, target=target, require_tp=False)


def _tp_residual(chan: SuperOp) -> np.ndarray:
    """Eigenvalues of Tr_out[Choi] - I. Same convention as Qiskit's own check
    (quantum_info.operators.measures._tp_condition) so the numbers are directly
    comparable to the warning it would have emitted."""
    choi = Choi(chan).data
    dims = tuple(np.sqrt(choi.shape).astype(int))
    tr_choi = np.trace(np.reshape(choi, dims + dims), axis1=1, axis2=3)
    return np.linalg.eigvalsh(tr_choi - np.eye(len(tr_choi)))


def _superop(circ: QuantumCircuit, noise_model=None) -> SuperOp:
    qc = circ.copy()
    qc.save_superop()
    sim = AerSimulator(method="superop", noise_model=noise_model)
    return SuperOp(sim.run(qc).result().data()["superop"])


def routing_permutation(tqc: QuantumCircuit, phys_order: list[int]) -> list[int]:
    """Local wire holding each virtual qubit at the END of the circuit.

    FINDING (worth raising with the group): with optimization_level=1 the
    transpiler elides the routing SWAP into a layout permutation, so for CCX and
    RCCX the scheduled circuit does NOT implement the target gate on the qubits
    it was laid out on -- initial_index_layout != final_index_layout. The cost
    is unaffected (a relabelling is free), but any TransformationPass that
    substitutes a decomposition into a larger circuit MUST propagate this
    permutation or the surrounding circuit is silently wrong. CSWAP happens to
    come back with the identity permutation, which is exactly why a
    Toffoli-only test would not have caught it.
    """
    index = {p: i for i, p in enumerate(phys_order)}
    final = tqc.layout.final_index_layout(filter_ancillas=True)
    return [index[final[i]] for i in range(len(final))]


def observed_infidelity(
    tqc: QuantumCircuit,
    cal: Calibration,
    device_errors,
    target: Operator,
) -> tuple[float, float, list[int], list[int]]:
    """Return (noisy_infidelity, ideal_infidelity_selfcheck, phys_order, perm).

    The self-check is the noiseless, delay-free run: if its infidelity is not
    ~0, the localisation or the routing permutation is wrong and the caller
    must reject the row rather than report noise that isn't noise.
    """
    active = active_qubits(tqc)
    initial = list(tqc.layout.initial_index_layout(filter_ancillas=True))
    if any(q not in active for q in initial):
        raise NotImplementedError("a laid-out qubit carries no gates")
    # Local index i <-> virtual qubit i at the input, by construction.
    phys_order = initial + [q for q in active if q not in initial]
    k = len(phys_order)
    if k > len(initial):
        raise NotImplementedError(
            "ancilla-using entries (D6 Selinger, D8 Jones) need a "
            "subspace-restricted fidelity; not handled in this pass"
        )

    perm = routing_permutation(tqc, phys_order)
    unpermute = SuperOp(Operator(PermutationGate(perm)))

    nm = local_noise_model(device_errors, phys_order)
    ideal = unpermute @ _superop(localise(tqc, cal, phys_order, include_idle=False))
    noisy = unpermute @ _superop(localise(tqc, cal, phys_order, include_idle=True), nm)

    ideal_inf = 1.0 - _fidelity(ideal, target)
    noisy_inf = 1.0 - _fidelity(noisy, target)
    return noisy_inf, ideal_inf, phys_order, perm


def average_gate_infidelity(process_infidelity: float, n_qubits: int) -> float:
    """Convert process infidelity to AVERAGE GATE infidelity.

    Necessary for an honest absolute comparison: the calibrated eps values that
    feed C0 are average gate errors (randomised benchmarking), so the surrogate
    predicts average-gate infidelity, while process_fidelity measures process
    infidelity. They differ by a dimensional factor, d/(d+1) with d = 2**n:

        1 - F_avg = [d / (d + 1)] * (1 - F_pro)

    Skipping this makes C0 look ~12% more pessimistic than it is. It does not
    affect any RANKING (it is a positive constant), only the calibration claim.
    """
    d = 2**n_qubits
    return process_infidelity * d / (d + 1)


# --------------------------------------------------------------------------- #
# Correlation reporting                                                       #
# --------------------------------------------------------------------------- #


def spearman(x, y):
    from scipy.stats import kendalltau, spearmanr

    rho, p = spearmanr(x, y)
    tau, pt = kendalltau(x, y)
    return rho, p, tau, pt


def report(rows):
    finite = [r for r in rows if math.isfinite(r["C1"]) and r["ok"]]
    stale = [r for r in rows if not math.isfinite(r["C1"]) and r["ok"]]

    print("\n" + "=" * 74)
    print("VALIDATION — Spearman rho(predicted cost, observed infidelity)")
    print("=" * 74)
    print(
        f"{len(finite)} finite rows scored; {len(stale)} rows excluded by the "
        f"stale-calibration policy; {sum(1 for r in rows if not r['ok'])} "
        f"rejected by the ideal-fidelity self-check."
    )

    def block(title, subset):
        if len(subset) < 4:
            print(f"\n{title}: too few rows ({len(subset)})")
            return None
        obs = [r["observed_infidelity"] for r in subset]
        r0 = spearman([r["C0"] for r in subset], obs)
        r1 = spearman([r["C1"] for r in subset], obs)
        print(f"\n{title}  (n = {len(subset)})")
        print(f"  C0:  rho = {r0[0]:+.4f}  (p = {r0[1]:.2e})   tau = {r0[2]:+.4f}")
        print(f"  C1:  rho = {r1[0]:+.4f}  (p = {r1[1]:.2e})   tau = {r1[2]:+.4f}")
        print(f"  idle term changes rho by {r1[0] - r0[0]:+.4f}")
        return r0[0], r1[0]

    block("POOLED (decomposition x placement — what the pass selects over)", finite)

    for label in dict.fromkeys(r["decomposition"] for r in finite):
        block(
            f"WITHIN {label} (placement discrimination only)",
            [r for r in finite if r["decomposition"] == label],
        )

    # --- decision quality: does argmin of the surrogate find a good candidate?
    print("\n" + "-" * 74)
    print("DECISION QUALITY (what the transpiler pass would actually pick)")
    print("-" * 74)
    for key in ("C0", "C1"):
        pick = min(finite, key=lambda r: r[key])
        best = min(finite, key=lambda r: r["observed_infidelity"])
        regret = pick["observed_infidelity"] / best["observed_infidelity"]
        print(
            f"  argmin {key}: {pick['decomposition']} @ {pick['placement']}  "
            f"observed {pick['observed_infidelity']:.5f}   "
            f"(true best {best['observed_infidelity']:.5f} @ "
            f"{best['placement']}, regret {regret:.3f}x)"
        )
    worst = max(finite, key=lambda r: r["observed_infidelity"])
    print(
        f"  for scale: worst finite candidate observed "
        f"{worst['observed_infidelity']:.5f} "
        f"({worst['observed_infidelity'] / min(r['observed_infidelity'] for r in finite):.1f}x "
        f"the best)"
    )

    # --- absolute calibration: is the cost a usable predicted infidelity?
    print("\n" + "-" * 74)
    print("ABSOLUTE CALIBRATION  (1 - exp(-C)) / observed average-gate infidelity")
    print("-" * 74)
    print("  rho only tests ranking. If the cost is ever read as a predicted")
    print("  fidelity, the conversion factor also has to be stable:")
    for key in ("C0", "C1"):
        ratios = [
            (1 - math.exp(-r[key])) / r["observed_avg_infidelity"] for r in finite
        ]
        lo, hi = min(ratios), max(ratios)
        print(
            f"  {key}:  median {statistics.median(ratios):.3f}   "
            f"range {lo:.3f}-{hi:.3f}   spread {hi - lo:.3f}"
        )
    print(
        "  A factor below 1 means the surrogate is optimistic (it under-predicts\n"
        "  error). The SPREAD is what matters: a tight spread means a single\n"
        "  scalar correction turns the cost into a calibrated fidelity estimate."
    )

    # --- where does the surrogate misrank, and does it matter?
    print("\n" + "-" * 74)
    print("DISCORDANT PAIRS  (surrogate ranks two candidates the wrong way round)")
    print("-" * 74)
    for label in dict.fromkeys(r["decomposition"] for r in finite):
        sub = [r for r in finite if r["decomposition"] == label]
        pairs = [
            (a, b)
            for a, b in itertools.combinations(sub, 2)
            if (a["C1"] - b["C1"])
            * (a["observed_infidelity"] - b["observed_infidelity"])
            < 0
        ]
        total = len(sub) * (len(sub) - 1) // 2
        print(f"  {label:26s} {len(pairs):3d} / {total} pairs")
        for a, b in pairs:
            print(
                f"      {a['placement']:>12s} vs {b['placement']:<12s} "
                f"dC1 = {abs(a['C1'] - b['C1']):.2e}   "
                f"d_observed = {abs(a['observed_infidelity'] - b['observed_infidelity']):.2e}"
            )
    print(
        "  Read the dC1 column: if every inversion happens between candidates the\n"
        "  surrogate considers near-tied, the misrankings cost nothing in practice."
    )

    # --- does the stale-calibration policy discard genuinely bad placements?
    if stale:
        s_obs = [r["observed_infidelity"] for r in stale]
        print(
            f"\n  stale-calibration rows (cost = inf): observed infidelity "
            f"median {statistics.median(s_obs):.5f} vs "
            f"{statistics.median([r['observed_infidelity'] for r in finite]):.5f} "
            f"for finite rows — the policy is discarding bad placements, "
            f"not arbitrary ones."
        )


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--placements", type=int, default=20)
    ap.add_argument("--out", default="aer_validation.csv")
    args = ap.parse_args()

    backend = FakeTorino()
    cal = extract_calibration(backend)
    print(f"backend: {cal.backend_name}   dt = {cal.dt * 1e9:.0f} ns")
    print("building device error model ...", flush=True)
    device_errors = basic_device_gate_errors(target=backend.target)

    triples = linear_triples(backend.coupling_map)
    random.seed(PLACEMENT_SEED)
    placements = random.sample(triples, args.placements)
    print(
        f"{len(triples)} connected linear triples; sampling {args.placements} "
        f"(seed {PLACEMENT_SEED}, same set as run_first_numbers.py)\n"
    )

    rows = []
    for cand in build_candidates():
        print(f"-- {cand.label}", flush=True)
        for pl in placements:
            tqc = transpile(
                cand.circuit,
                backend,
                initial_layout=list(pl),
                optimization_level=OPT_LEVEL,
                seed_transpiler=SEED_TRANSPILER,
                scheduling_method="asap",
            )
            s = score(tqc, cal)
            try:
                obs, ideal_inf, phys, perm = observed_infidelity(
                    tqc, cal, device_errors, cand.target
                )
                ok = abs(ideal_inf) < IDEAL_FIDELITY_TOL
            except NotImplementedError as e:
                print(f"   skip {pl}: {e}")
                continue
            if not ok:
                print(
                    f"   REJECT {pl}: noiseless localisation gives infidelity "
                    f"{ideal_inf:.2e} — layout/permutation bug, not noise"
                )
            rows.append(
                {
                    "decomposition": cand.label,
                    "relative_phase": cand.relative_phase,
                    "placement": "-".join(map(str, pl)),
                    "active": "-".join(map(str, phys)),
                    "routing_perm": "".join(map(str, perm)),
                    "cz": s["cz_count"],
                    "sx": s["sx_count"],
                    "x": s["x_count"],
                    "rz": s["rz_count"],
                    "depth": s["depth"],
                    "makespan_s": s["makespan_s"],
                    "C0": s["c0"],
                    "idle": s["idle_penalty"],
                    "C1": s["c1"],
                    "observed_infidelity": obs,
                    "observed_avg_infidelity": average_gate_infidelity(
                        obs, cand.circuit.num_qubits
                    ),
                    "ideal_infidelity": ideal_inf,
                    "ok": ok,
                }
            )

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 8) if isinstance(v, float) else v)
                        for k, v in r.items()})
    print(f"\nwrote {args.out}  ({len(rows)} rows)")

    report(rows)
    plot(rows)


def plot(rows, out_png="aer_validation.png"):
    """Predicted cost vs simulated infidelity, one panel per cost function."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[plot skipped] matplotlib not installed")
        return
    finite = [r for r in rows if math.isfinite(r["C1"]) and r["ok"]]
    labels = list(dict.fromkeys(r["decomposition"] for r in finite))
    colors = {l: c for l, c in zip(labels, ["#0173B2", "#DE8F05", "#029E73", "#CC78BC"])}

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, key in zip(axes, ("C0", "C1")):
        for l in labels:
            sub = [r for r in finite if r["decomposition"] == l]
            ax.scatter(
                [r[key] for r in sub],
                [r["observed_avg_infidelity"] for r in sub],
                s=34,
                color=colors[l],
                label=l,
                alpha=0.85,
                edgecolor="white",
                linewidth=0.5,
            )
        lim = [
            min(min(r[key] for r in finite), min(r["observed_avg_infidelity"] for r in finite)),
            max(max(r[key] for r in finite), max(r["observed_avg_infidelity"] for r in finite)),
        ]
        ax.plot(lim, lim, ls="--", lw=1, color="0.5", label="y = x" if key == "C0" else None)
        rho = spearman([r[key] for r in finite], [r["observed_avg_infidelity"] for r in finite])[0]
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(f"predicted {key}")
        ax.set_title(f"{key}:  Spearman rho = {rho:.4f}", fontweight="bold")
        ax.grid(alpha=0.3, which="both")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("simulated average-gate infidelity (Aer, exact superoperator)")
    axes[0].legend(fontsize=8)
    fig.suptitle(
        f"Cost-function validation on FakeTorino  "
        f"(n = {len(finite)} finite (decomposition, placement) pairs)",
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
