"""
D1 - Textbook Fredkin via Toffoli (Standard)
Source: Textbook definition — Fredkin gate expressed as CX + CCX + CX
Exact: Yes | Ancilla: None | CNOT count: 3 (+ 5 from CCX decomp)
q0 = control, q1/q2 = targets
"""
from qiskit import QuantumCircuit


def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D1_Textbook")

    qc.cx(2, 1)
    qc.ccx(0, 1, 2)
    qc.cx(2, 1)

    return qc
