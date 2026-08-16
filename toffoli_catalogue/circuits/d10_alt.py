"""
D10 - Alternative Exact Clifford+T Toffoli
Source: TODO - verify reference
Exact: Yes | Ancilla: None | CNOT count: 7 (reconstructed)
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D10_Alt")
    q0, q1, q2 = 0, 1, 2
    qc.h(q2)
    qc.t(q0)
    qc.t(q1)
    qc.t(q2)
    qc.cx(q1, q0)
    qc.cx(q2, q1)
    qc.cx(q0, q2)
    qc.tdg(q1)
    qc.cx(q0, q1)
    qc.tdg(q0)
    qc.tdg(q1)
    qc.t(q2)
    qc.cx(q2, q1)
    qc.cx(q0, q2)
    qc.cx(q1, q0)
    qc.h(q2)
    return qc
