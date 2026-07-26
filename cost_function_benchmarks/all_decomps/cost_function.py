"""
cost_function.py
================
Noise-aware cost functions C0 and C1 for scoring gate decompositions on
IBM Heron-family backends.

QIntern 2026 -- Project 19, Group A (Luke Devlin)

Definitions (see formulation note, 8 July 2026):

    C0(D) = -sum_g ln(1 - eps_g)
    C1(D) = C0(D) + sum_q [ tau_q / (6 T1(q)) + tau_q / (3 T2(q)) ]

where eps_g is the calibrated error of gate g on its specific physical
qubit(s)/edge, and tau_q is the idle time of qubit q within the scheduled
decomposition (ASAP schedule; tau_q = makespan - busy_q).

All times in SECONDS (Qiskit convention). RZ is virtual: zero error, zero
duration -- it contributes to neither term.

Policies:
  * eps >= 1 (stale calibration sentinel)  -> cost = +inf, with a warning.
  * Readout error deliberately excluded (constant offset across candidates).
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Calibration extraction  (provisional implementation of the Group B contract)
# --------------------------------------------------------------------------


@dataclass
class Calibration:
    """Container matching the Group A <-> Group B data contract."""

    # per-edge, keyed by frozenset({i, j}): {"error": e, "duration": s}
    two_q: dict = field(default_factory=dict)
    # per-qubit: {"error": e, "duration": s, "t1": s, "t2": s}
    one_q: dict = field(default_factory=dict)
    two_q_gate_name: str = "cz"

    def edge(self, i: int, j: int) -> dict:
        try:
            return self.two_q[frozenset((i, j))]
        except KeyError:
            raise KeyError(
                f"No {self.two_q_gate_name} calibration for edge ({i},{j}). "
                "Is this a real coupling-map edge on the target backend?"
            )


def extract_calibration(backend, two_q_gate: str = "cz") -> Calibration:
    """Pull the cost-function inputs out of a BackendV2 target.

    Provisional stand-in for Group B's extraction layer; same schema.
    """
    target = backend.target
    cal = Calibration(two_q_gate_name=two_q_gate)

    # --- two-qubit gate: per-edge error + duration -------------------------
    for qargs, props in target[two_q_gate].items():
        if props is None:
            continue
        key = frozenset(qargs)
        err = props.error if props.error is not None else float("nan")
        dur = props.duration if props.duration is not None else float("nan")
        # keep the worse direction if both are reported
        if key in cal.two_q:
            cal.two_q[key]["error"] = max(cal.two_q[key]["error"], err)
            cal.two_q[key]["duration"] = max(cal.two_q[key]["duration"], dur)
        else:
            cal.two_q[key] = {"error": err, "duration": dur}

    # --- single-qubit: shared RB error (sx), duration, T1, T2 --------------
    for q in range(backend.num_qubits):
        try:
            sx_props = target["sx"][(q,)]
            err = (
                sx_props.error
                if sx_props and sx_props.error is not None
                else float("nan")
            )
            dur = (
                sx_props.duration
                if sx_props and sx_props.duration is not None
                else float("nan")
            )
        except KeyError:
            err, dur = float("nan"), float("nan")
        qp = backend.qubit_properties(q)
        cal.one_q[q] = {
            "error": err,
            "duration": dur,
            "t1": getattr(qp, "t1", None),
            "t2": getattr(qp, "t2", None),
        }
    return cal


# --------------------------------------------------------------------------
# Per-gate penalty
# --------------------------------------------------------------------------


def _gate_penalty(eps: float, label: str) -> float:
    """-ln(1 - eps), with the stale-calibration policy."""
    if math.isnan(eps):
        warnings.warn(f"Missing calibration for {label}; treating as eps=1 (cost=inf).")
        return math.inf
    if eps >= 1.0:
        warnings.warn(
            f"Stale calibration (eps={eps}) for {label}; cost=inf (edge never selected)."
        )
        return math.inf
    if eps < 0:
        raise ValueError(f"Negative error rate for {label}: {eps}")
    return -math.log1p(-eps)


# --------------------------------------------------------------------------
# Exact scoring of a transpiled circuit (preferred path)
# --------------------------------------------------------------------------


def score_circuit(qc, backend=None, cal: Calibration | None = None) -> dict:
    """Score a circuit already transpiled to the backend's native basis and
    laid out on physical qubits.

    Returns {"C0", "C1", "idle_penalty", "makespan_s", "n_2q", "n_1q"}.

    The idle term uses an internal ASAP timeline built from calibrated
    instruction durations: tau_q = makespan - busy_q, summed over the qubits
    the decomposition touches.
    """
    if cal is None:
        if backend is None:
            raise ValueError("Provide either a Calibration or a backend.")
        cal = extract_calibration(backend)

    virtual = {"rz", "barrier", "delay"}  # delay handled via timeline only
    two_q_name = cal.two_q_gate_name

    c0 = 0.0
    n_2q = n_1q = 0

    # physical index of each circuit qubit (post-transpile layout)
    def phys(qubit) -> int:
        return qc.find_bit(qubit).index

    clock: dict[int, float] = {}  # per-qubit running time (s)
    busy: dict[int, float] = {}  # per-qubit accumulated busy time (s)

    for inst in qc.data:
        name = inst.operation.name
        qubits = [phys(q) for q in inst.qubits]
        for q in qubits:
            clock.setdefault(q, 0.0)
            busy.setdefault(q, 0.0)

        if name == "barrier":
            t = max((clock[q] for q in qubits), default=0.0)
            for q in qubits:
                clock[q] = t
            continue

        # --- duration + error lookup ---
        if name == two_q_name:
            e = cal.edge(*qubits)
            eps, dur = e["error"], e["duration"]
            c0 += _gate_penalty(eps, f"{name}{tuple(qubits)}")
            n_2q += 1
        elif name in ("sx", "x", "id"):
            q = qubits[0]
            eps, dur = cal.one_q[q]["error"], cal.one_q[q]["duration"]
            c0 += _gate_penalty(eps, f"{name}({q})")
            n_1q += 1
        elif name == "delay":
            dur = inst.operation.duration
            unit = inst.operation.unit
            dur = {
                "s": dur,
                "ms": dur * 1e-3,
                "us": dur * 1e-6,
                "ns": dur * 1e-9,
                "dt": dur * (backend.dt if backend else 0),
            }[unit]
            eps = 0.0
        elif name in virtual:
            eps, dur = 0.0, 0.0
        else:
            raise ValueError(
                f"Non-native op '{name}' in circuit -- transpile to the "
                f"backend basis before scoring."
            )

        # --- ASAP timeline update ---
        start = max(clock[q] for q in qubits)
        end = start + (dur if not math.isnan(dur) else 0.0)
        for q in qubits:
            clock[q] = end
            if name != "delay":  # delay is idle, not busy
                busy[q] += dur if not math.isnan(dur) else 0.0

    makespan = max(clock.values(), default=0.0)

    idle = 0.0
    for q in clock:
        tau = makespan - busy[q]
        t1, t2 = cal.one_q[q]["t1"], cal.one_q[q]["t2"]
        if t1 is None or t2 is None or not t1 or not t2:
            warnings.warn(f"Missing T1/T2 for qubit {q}; skipping its idle term.")
            continue
        idle += tau / (6.0 * t1) + tau / (3.0 * t2)

    return {
        "C0": c0,
        "C1": c0 + idle,
        "idle_penalty": idle,
        "makespan_s": makespan,
        "n_2q": n_2q,
        "n_1q": n_1q,
    }


# --------------------------------------------------------------------------
# Approximate scoring from Shruti's results.json (no circuit available)
# --------------------------------------------------------------------------


def score_json_entry(entry: dict, cal: Calibration) -> dict:
    """Approximate C0 for one results.json record.

    Limitations (flag to the group):
      * cz_pairs stores the SET of edges used, not per-edge multiplicities;
        we distribute the total CZ count uniformly across the used edges.
      * No timing/schedule information in the JSON -> no C1.
    Upgrade request: record per-edge CZ counts (and ideally QPY-dump the
    transpiled circuits) so the exact scorer can run instead.
    """
    pairs = [tuple(p) for p in entry["cz_pairs"]]
    n_cz, n_sx, n_x = entry["cz"], entry["sx"], entry.get("x", 0)
    layout = entry["layout"]

    c0 = 0.0
    if pairs:
        per_edge = n_cz / len(pairs)  # uniform-multiplicity approximation
        for i, j in pairs:
            c0 += per_edge * _gate_penalty(cal.edge(i, j)["error"], f"cz({i},{j})")

    if layout:
        per_q = (n_sx + n_x) / len(layout)  # uniform 1Q attribution
        for q in layout:
            c0 += per_q * _gate_penalty(cal.one_q[q]["error"], f"sx({q})")

    return {"C0_approx": c0, "layout": layout}
