"""
D9 - Zero-Ancilla T-Depth-3 Toffoli (0AT3)
Source: TODO - verify reference
Exact: Under verification | Ancilla: None | CNOT count: 7 (reconstructed)
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D9_ZeroAncilla")
    q0, q1, q2 = 0, 1, 2
    qc.tdg(q0)
    qc.t(q1)
    qc.h(q2)
    qc.cx(q0, q1)
    qc.cx(q2, q0)
    qc.tdg(q0)
    qc.t(q2)
    qc.cx(q1, q0)
    qc.cx(q1, q2)
    qc.tdg(q0)
    qc.tdg(q1)
    qc.t(q2)
    qc.cx(q2, q0)
    qc.s(q0)
    qc.cx(q1, q2)
    qc.cx(q0, q1)
    qc.h(q2)
    return qc
