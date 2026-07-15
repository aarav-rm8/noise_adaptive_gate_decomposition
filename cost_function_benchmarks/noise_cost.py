"""
noise_cost.py — Noise-aware cost functions C0 / C1 for decomposition selection.

QIntern 2026, Project 19. Direct implementation of the formulation note
(Devlin, check-in 8 Jul 2026):

    C0(D) = sum_g  -ln(1 - eps_g)                       (Eq. 3, additive gate errors)
    C1(D) = C0(D) + sum_q [ tau_q/(6 T1_q) + tau_q/(3 T2_q) ]   (Eq. 6, + idle decoherence)

Conventions (note §3, §6):
  * All internal computation in SECONDS (Qiskit convention; the IBM UI shows ns).
  * RZ is a virtual frame rotation: error 0, duration 0 -> contributes nothing.
  * Readout/measure excluded: constant offset across candidates, cannot change ranking.
  * Stale calibration (eps >= 1, IBM's "undefined" sentinel) -> cost = inf, logged,
    so the edge/qubit is never selected. Deliberate policy, not an accident.
  * Single-qubit physical gates (sx, x, id) share one RB value per qubit; we look up
    per (gate, qubit) from the Target, which encodes exactly that.

Usage:
    from qiskit_ibm_runtime.fake_provider import FakeTorino
    from noise_cost import extract_calibration, score

    backend = FakeTorino()
    calib   = extract_calibration(backend)
    tqc     = transpile(qc, backend, initial_layout=[12, 13, 14],
                        optimization_level=1, seed_transpiler=7,
                        scheduling_method="asap")   # scheduling needed for C1
    result  = score(tqc, calib)   # dict: c0, idle_penalty, c1, cz_count, ...

If fractional decompositions (RZZ, RX) enter the catalogue, load the backend with
use_fractional_gates=True so their calibration is exposed (note §6).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

log = logging.getLogger("noise_cost")

# Gates that never contribute to C0
_FREE = {"rz", "barrier"}  # rz virtual; barrier non-physical
_EXCLUDED = {"measure", "reset"}  # readout excluded by policy (note §6)
_IDLE = {"delay"}  # handled by the C1 idle term, not C0


# --------------------------------------------------------------------------- #
# Calibration extraction (the old Group-B data contract, now self-contained)  #
# --------------------------------------------------------------------------- #


@dataclass
class Calibration:
    """Per-(gate, qubits) error/duration plus per-qubit T1/T2, all in seconds."""

    gate_error: dict = field(default_factory=dict)  # (name, (q,...)) -> eps
    gate_duration: dict = field(default_factory=dict)  # (name, (q,...)) -> seconds
    t1: dict = field(default_factory=dict)  # q -> seconds
    t2: dict = field(default_factory=dict)  # q -> seconds
    dt: float = 1.0  # seconds per dt sample
    backend_name: str = ""


def extract_calibration(backend) -> Calibration:
    """Pull everything the cost function needs from a BackendV2 (real or fake).

    Data contract (note §3): per-edge {CZ error, duration}, per-qubit
    {SX/X error, duration, T1, T2}, plus dt for delay-unit conversion.
    """
    target = backend.target
    cal = Calibration(dt=target.dt, backend_name=getattr(backend, "name", ""))

    for name in target.operation_names:
        try:
            props_map = target[name]
        except Exception:
            continue
        if not props_map:
            continue
        for qubits, props in props_map.items():
            if qubits is None or props is None:
                continue
            key = (name, tuple(qubits))
            cal.gate_error[key] = getattr(props, "error", None)
            cal.gate_duration[key] = getattr(props, "duration", None)

    for q, qp in enumerate(target.qubit_properties or []):
        if qp is None:
            continue
        cal.t1[q] = qp.t1
        cal.t2[q] = qp.t2

    return cal


# --------------------------------------------------------------------------- #
# C0 — additive gate-error model (note §4)                                     #
# --------------------------------------------------------------------------- #


def _lookup_error(cal: Calibration, name: str, qubits: tuple):
    eps = cal.gate_error.get((name, qubits))
    if eps is None and len(qubits) == 2:  # tolerate either edge order
        eps = cal.gate_error.get((name, (qubits[1], qubits[0])))
    return eps


def c0(circuit, cal: Calibration) -> float:
    """C0 = sum over physical gates of -ln(1 - eps_g), eps looked up per edge/qubit.

    `circuit` must already be transpiled to the backend (native basis, physical
    qubit indices). Works on scheduled or unscheduled circuits.
    """
    total = 0.0
    for inst in circuit.data:
        name = inst.operation.name
        if name in _FREE or name in _EXCLUDED or name in _IDLE:
            continue
        qubits = tuple(circuit.find_bit(b).index for b in inst.qubits)
        eps = _lookup_error(cal, name, qubits)
        if eps is None:
            log.warning(
                "no calibration for %s%s -> cost inf (unusable placement)", name, qubits
            )
            return math.inf
        if eps >= 1.0:  # stale-calibration sentinel (note §6)
            log.warning("stale calibration (eps=1) for %s%s -> cost inf", name, qubits)
            return math.inf
        total += -math.log1p(-eps)  # -ln(1 - eps), numerically stable
    return total


# --------------------------------------------------------------------------- #
# C1 — C0 + idle decoherence (note §5)                                         #
# --------------------------------------------------------------------------- #


def idle_penalty(tau: float, t1: float, t2: float) -> float:
    """Linearised -ln F_idle(tau) = tau/(6 T1) + tau/(3 T2)  (Eq. 5)."""
    return tau / (6.0 * t1) + tau / (3.0 * t2)


def c1(scheduled_circuit, cal: Calibration) -> dict:
    """Return {'c0', 'idle_penalty', 'c1'} for an ASAP/ALAP-scheduled circuit.

    Idle time tau_q = total explicit Delay on qubit q, converted dt -> seconds.
    Only qubits hosting at least one physical gate are counted: transpiled
    circuits are padded to full device width, and the ~130 untouched wires
    must not contribute. Leading/trailing delays on active qubits ARE counted:
    a qubit holding an input or output state of the block decoheres while it
    waits, which is exactly what the idle term models.
    """
    base = c0(scheduled_circuit, cal)

    active = set()
    for inst in scheduled_circuit.data:
        if inst.operation.name not in (_IDLE | _FREE | _EXCLUDED):
            for b in inst.qubits:
                active.add(scheduled_circuit.find_bit(b).index)

    pen = 0.0
    for inst in scheduled_circuit.data:
        if inst.operation.name != "delay":
            continue
        q = scheduled_circuit.find_bit(inst.qubits[0]).index
        if q not in active:
            continue
        dur, unit = inst.operation.duration, inst.operation.unit
        tau = dur * cal.dt if unit == "dt" else float(dur)  # note §6: seconds
        if cal.t1.get(q) and cal.t2.get(q):
            pen += idle_penalty(tau, cal.t1[q], cal.t2[q])
        else:
            log.warning("missing T1/T2 for qubit %d; its idle time is uncosted", q)

    return {"c0": base, "idle_penalty": pen, "c1": base + pen}


# --------------------------------------------------------------------------- #
# One-stop scorer: fills a whole catalogue row                                 #
# --------------------------------------------------------------------------- #


def score(transpiled_circuit, cal: Calibration) -> dict:
    """Everything a catalogue table wants for one (decomposition, placement) pair.

    Returns: c0, idle_penalty, c1, cz/sx/x/rz counts, depth (delays excluded),
    active physical qubits, makespan in seconds (if scheduled).
    """
    counts = {}
    active = set()
    for inst in transpiled_circuit.data:
        name = inst.operation.name
        counts[name] = counts.get(name, 0) + 1
        if name not in (_IDLE | _FREE | _EXCLUDED):
            for b in inst.qubits:
                active.add(transpiled_circuit.find_bit(b).index)

    parts = c1(transpiled_circuit, cal)

    try:
        depth = transpiled_circuit.depth(
            lambda inst: inst.operation.name not in ("delay", "barrier")
        )
    except TypeError:  # older qiskit: no filter arg
        depth = transpiled_circuit.depth()

    try:
        makespan = (
            transpiled_circuit.duration * cal.dt
            if transpiled_circuit.duration is not None
            else None
        )
    except Exception:
        makespan = None

    return {
        "c0": parts["c0"],
        "idle_penalty": parts["idle_penalty"],
        "c1": parts["c1"],
        "cz_count": counts.get("cz", 0),
        "sx_count": counts.get("sx", 0),
        "x_count": counts.get("x", 0),
        "rz_count": counts.get("rz", 0),
        "depth": depth,
        "active_qubits": tuple(sorted(active)),
        "makespan_s": makespan,
    }
