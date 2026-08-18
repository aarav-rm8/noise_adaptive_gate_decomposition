"""
D2 - Fredkin via CCX with H-T Sandwich (Cruz, Murta et al)
Source: Textbook decomposition, control on q0, targets q1/q2
Exact: Yes | Ancilla: None | Uses: CX, CCX, T, Tdg, S, H
q0 = control, q1/q2 = targets
"""
from qiskit import QuantumCircuit


def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D2_Paper1_FigE")

    qc.cx(2, 1)
    qc.h(2)
    qc.cx(1, 2)
    qc.tdg(2)
    qc.ccx(0, 1, 2)
    qc.t(2)
    qc.cx(1, 2)
    qc.tdg(1)
    qc.tdg(2)
    qc.ccx(0, 1, 2)
    qc.t(2)
    qc.cx(0, 1)
    qc.h(2)
    qc.tdg(1)
    qc.cx(0, 1)
    qc.s(1)
    qc.t(0)
    qc.cx(2, 1)

    return qc
