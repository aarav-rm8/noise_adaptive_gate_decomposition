"""
D6 - Ancilla-Assisted T-Depth-1 Toffoli (Selinger, 2013)
Source: Selinger, Phys. Rev. A 87, 042302 (2013), Fig. 1
Exact: Yes (verified by basis-state simulation) | Ancilla: 4 | CNOT count: 16
Data qubits: 0 (x), 1 (y), 2 (z)
Ancilla qubits: 3 (a1), 4 (a2), 5 (a3), 6 (a4)
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(7, name="D6_Selinger")

    x, y, z = 0, 1, 2
    a1, a2, a3, a4 = 3, 4, 5, 6

    qc.h(z)

    # Stage 1: compute ancilla parities
    qc.cx(y, a3)
    qc.cx(x, a1)
    qc.cx(y, a2)
    qc.cx(z, a3)
    qc.cx(a1, a4)
    qc.cx(x, a2)
    qc.cx(z, a4)
    qc.cx(a3, a1)

    # T layer (T-depth 1)
    qc.t(x);   qc.t(y);   qc.t(z);   qc.t(a1)
    qc.tdg(a2); qc.tdg(a3); qc.tdg(a4)

    # Stage 3: uncompute ancillas
    qc.cx(a3, a1)
    qc.cx(z, a4)
    qc.cx(x, a2)
    qc.cx(a1, a4)
    qc.cx(z, a3)
    qc.cx(y, a2)
    qc.cx(x, a1)
    qc.cx(y, a3)

    qc.h(z)
    return qc
