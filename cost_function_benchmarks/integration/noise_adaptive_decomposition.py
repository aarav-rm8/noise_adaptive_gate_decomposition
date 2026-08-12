"""
noise_adaptive_decomposition.py — device-average, PRE-LAYOUT CCX decomposition
selection. Replaces noise_adaptive_pass.py's post-routing TransformationPass
approach (see module docstring below for why).

QIntern 2026, Project 19. Tapasi.

WHY THIS REPLACES THE POST-ROUTING TransformationPass VERSION:

Testing noise_adaptive_pass.py against a real MQT Bench circuit (Grover,
circuit_size=4) produced IDENTICAL output between the default pipeline and
the custom one -- the pass found zero CCX nodes to replace. Root cause,
confirmed directly from Qiskit's own error message when trying to force
'ccx' to survive into routing:

    "Gates with 3 or more qubits (ccx) in `basis_gates` or `backend` are
     incompatible with a custom `coupling_map`."

Routing algorithms (Sabre etc.) only reason about PAIRWISE qubit
interactions. Qiskit's `init` stage therefore decomposes any 3+-qubit gate
into 2-qubit gates BEFORE layout/routing ever runs -- unconditionally, not
as an optional choice. By the time a TransformationPass in the `translation`
stage sees the DAG, every `ccx` node is already gone.

This matches the ORIGINAL PROJECT PROPOSAL's own design decision: "Noise
model: gate error rates ... with device-average costs as the primary
starting point." Device-average costs are exactly what's usable BEFORE
physical qubits are assigned -- which is the only point in the pipeline
where a `ccx` node still exists.

NEW DESIGN: score all 8 ancilla-free candidates using DEVICE-AVERAGE gate
error rates (no specific qubits needed yet), pick the single best one
ONCE per circuit, and substitute it into every CCX in the circuit BEFORE
calling transpile(). The resulting circuit is now ordinary 2-qubit gates,
which Sabre routes exactly as it would the default Barenco decomposition --
no feasibility/connectivity logic needed on our side at all, since routing
handles that the same way it always does.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict

from qiskit import QuantumCircuit, transpile
from qiskit.converters import circuit_to_dag, dag_to_circuit

from catalogue import CATALOGUE
from noise_cost import Calibration

NATIVE_BASIS = ["cz", "sx", "rz", "x"]

# SAFETY-CRITICAL: only fully exact decompositions (verify=="operator") are
# eligible for general-purpose substitution. Relative-phase decompositions
# (D2_Maslov, D7_Vale, verify=="measurement") are ONLY guaranteed correct if
# their output is measured immediately -- they may differ from true CCX by a
# phase that vanishes on measurement but does NOT vanish if the CCX's output
# feeds into further coherent operations (e.g. inside a larger algorithm's
# oracle/diffusion structure). CONFIRMED this matters in practice: naively
# substituting the device-average winner (D2_Maslov) into a real Grover
# circuit produced a scattered, near-uniform output distribution instead of
# the correct dominant peak -- i.e. it silently broke the algorithm.
# D2/D7 could be re-enabled ONLY for circuits where the CCX is provably the
# last operation on its qubits before measurement -- not attempted here.
_CANDIDATES = [item for item in CATALOGUE
               if item["ancillas"] == 0 and item["verify"] == "operator"]


def device_average_errors(cal: Calibration) -> dict:
    """Mean error rate per native gate NAME across the whole device --
    ignores WHICH qubits, since physical qubits aren't assigned yet."""
    by_gate = defaultdict(list)
    for (name, _qubits), eps in cal.gate_error.items():
        if eps is not None and eps < 1.0:
            by_gate[name].append(eps)
    return {name: statistics.mean(vals) for name, vals in by_gate.items()}


def _candidate_avg_cost(item, avg_errors: dict) -> float:
    """C0 using DEVICE-AVERAGE error per gate type (not per-qubit)."""
    native = transpile(item["builder"](), basis_gates=NATIVE_BASIS, optimization_level=1)
    total = 0.0
    for instr in native.data:
        name = instr.operation.name
        if name in ("rz", "barrier"):
            continue
        eps = avg_errors.get(name)
        if eps is None or eps >= 1.0:
            return math.inf
        total += -math.log1p(-eps)
    return total


def best_decomposition_by_device_average(cal: Calibration):
    """Picks ONE decomposition for the whole circuit, using device-average
    cost. Returns (item, native_circuit_in_role_order)."""
    avg_errors = device_average_errors(cal)
    best_item, best_native, best_cost = None, None, math.inf
    for item in _CANDIDATES:
        cost = _candidate_avg_cost(item, avg_errors)
        if cost < best_cost:
            native = transpile(item["builder"](), basis_gates=NATIVE_BASIS, optimization_level=1)
            logical_ccx = item.get("logical_ccx", (0, 1, 2))
            reordered = _reorder_to_role_order(native, logical_ccx)
            best_item, best_native, best_cost = item, reordered, cost
    return best_item, best_native, best_cost


def _reorder_to_role_order(native_qc, logical_ccx):
    builder_to_role = {logical_ccx[r]: r for r in range(3)}
    new_qc = QuantumCircuit(3, name=native_qc.name)
    for instr in native_qc.data:
        new_qubits = [new_qc.qubits[builder_to_role[native_qc.find_bit(q).index]]
                      for q in instr.qubits]
        new_qc.append(instr.operation, new_qubits, instr.clbits)
    return new_qc


def substitute_ccx_pre_layout(qc: QuantumCircuit, cal: Calibration) -> QuantumCircuit:
    """Replaces every CCX with the single best device-average-cost EXACT
    decomposition, before layout/routing. Wraps each substitution in a
    labeled barrier pair (kept for future Phase 2 work; harmless if unused).
    VERIFIED: preserves correctness (matches default pipeline's dominant
    measurement outcome) on a real MQT Bench Grover circuit."""
    from qiskit.circuit import Barrier
    winner, best_native, best_cost = best_decomposition_by_device_average(cal)
    if winner is None:
        return qc

    dag = circuit_to_dag(qc)
    block_id = 0
    for node in list(dag.op_nodes()):
        if node.op.name != "ccx":
            continue
        n = len(node.qargs)
        sub = QuantumCircuit(n)
        sub.append(Barrier(n, label=f"ccx_{block_id}_open"), range(n))
        sub.compose(best_native, inplace=True)
        sub.append(Barrier(n, label=f"ccx_{block_id}_close"), range(n))
        sub_dag = circuit_to_dag(sub)
        dag.substitute_node_with_dag(node, sub_dag, wires=list(sub_dag.qubits))
        block_id += 1
    return dag_to_circuit(dag)