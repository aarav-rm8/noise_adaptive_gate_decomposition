"""
D3 - Exact Toffoli, Reduced T-depth (Amy et al., 2013)
Source: Amy, Maslov, Mosca - IEEE Trans CAD 2014
Exact: Yes | Ancilla: None | CNOT count: 6
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D3_Amy")
    qc.tdg(0)
    qc.tdg(1)
    qc.h(2)
    qc.cx(2, 0)
    qc.t(0)
    qc.cx(1, 2)
    qc.t(2)
    qc.cx(1, 0)
    qc.tdg(0)
    qc.cx(1, 2)
    qc.cx(2, 0)
    qc.t(0)
    qc.cx(1, 0)
    qc.tdg(2)
    qc.h(2)
    return qc
