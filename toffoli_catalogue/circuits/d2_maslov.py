"""
D2 - Relative-Phase Toffoli (Margolus / Maslov 2015)
Source: Maslov arXiv:1508.03273, Fig 3 (Qiskit RCCXGate)
Exact: No (relative phase) | Ancilla: None | CNOT count: 3
"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import RCCXGate

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D2_Maslov")
    qc.append(RCCXGate(), [0, 1, 2])
    return qc.decompose()
