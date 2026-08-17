"""
D5 - Textbook Exact Toffoli (Nielsen & Chuang)
Source: Nielsen & Chuang, reproduced in Cruz & Murta (2024), Fig. 1(e)
Exact: Yes | Ancilla: None | CNOT count: 6
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D5_Nielsen_Chuang")
    q0, q1, q2 = 0, 1, 2
    qc.h(q2)
    qc.t(q0)
    qc.t(q1)
    qc.t(q2)
    qc.cx(q0, q1)
    qc.cx(q1, q2)
    qc.cx(q0, q1)
    qc.t(q2)
    qc.cx(q1, q2)
    qc.cx(q0, q1)
    qc.tdg(q1)
    qc.tdg(q2)
    qc.cx(q1, q2)
    qc.cx(q0, q1)
    qc.tdg(q2)
    qc.cx(q1, q2)
    qc.h(q2)
    return qc
