"""
D4 - Fredkin Alternate Decomposition (Cruz, Murta et al)
Source: CCX-free, uses SX and phase rotations
Exact: Yes | Ancilla: None | Uses: CX, T, Tdg, S, Sdg, SX, H, Z
q0 = control, q1/q2 = targets
"""
from qiskit import QuantumCircuit


def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D4_Paper1_FigB")

    qc.x(1)
    qc.sdg(2)
    qc.t(0)
    qc.s(1)
    qc.sx(2)
    qc.cx(2, 1)
    qc.s(1)
    qc.h(2)
    qc.s(2)
    qc.t(2)
    qc.h(2)
    qc.cx(2, 1)
    qc.s(1)
    qc.sdg(2)
    qc.sx(1)
    qc.sx(2)
    qc.cx(0, 1)
    qc.t(2)
    qc.cx(1, 2)
    qc.tdg(1)
    qc.tdg(2)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.tdg(1)
    qc.t(2)

    # Continued from second Composer page
    qc.z(1)
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)

    return qc
