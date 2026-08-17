"""
D1 - Standard Exact Toffoli (Barenco et al., 1995)
Source: Qiskit CCXGate (follows Barenco construction)
Exact: Yes | Ancilla: None | CNOT count: 6
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D1_Barenco")
    qc.ccx(0, 1, 2)
    return qc.decompose()
