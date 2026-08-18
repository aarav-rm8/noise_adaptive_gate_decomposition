"""
D7 - Fredkin via V-gate Decomposition (Yu, Yang et al)
Source: uses CSX (controlled-√X) and CSXdg as V-gate building blocks (V² = X)
Exact: Yes | Ancilla: None | Uses: CX, CSX, CSXdg
q0 = control, q1/q2 = targets
"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import SXdgGate


def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D7_Paper3_Vgate")

    qc.cx(2, 1)
    qc.csx(1, 2)
    qc.csx(0, 2)
    qc.cx(0, 1)
    qc.append(SXdgGate().control(), [1, 2])
    qc.cx(2, 1)
    qc.cx(0, 1)

    return qc
