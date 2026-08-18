"""
D6 - Fredkin via CCX with S-H Framing (Saha, Khanna et al)
Source: standard Fredkin decomposition using CCX with phase corrections
Exact: Yes | Ancilla: None | Uses: CX, CCX, T, Tdg, S, Sdg, H
q0 = control, q1/q2 = targets
"""
from qiskit import QuantumCircuit


def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D6_Paper2")

    qc.sdg(1)
    qc.cx(2, 1)
    qc.s(1)
    qc.s(2)
    qc.h(2)
    qc.tdg(2)
    qc.ccx(0, 1, 2)
    qc.t(2)
    qc.cx(1, 2)
    qc.tdg(2)
    qc.ccx(0, 1, 2)
    qc.cx(0, 1)
    qc.tdg(1)
    qc.cx(0, 1)
    qc.t(2)
    qc.t(0)
    qc.t(1)
    qc.h(2)
    qc.cx(2, 1)

    return qc
