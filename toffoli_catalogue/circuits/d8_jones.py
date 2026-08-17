"""
D8 - Jones Toffoli* (Jones, 2013)
Source: Jones, Phys. Rev. A 87, 022328 (2013), Fig. 1(a)
Exact: No (implements Toffoli*, not exact CCX)
Ancilla: 1 clean ancilla qubit | CNOT count: 6
Data qubits: 0 (x), 1 (y), 2 (z) | Ancilla: 3 (a)
Verification: basis-state simulation only (not unitary equiv)
"""
from qiskit import QuantumCircuit

def build() -> QuantumCircuit:
    qc = QuantumCircuit(4, name="D8_Jones")
    x, y, z, a = 0, 1, 2, 3
    qc.h(z)
    qc.cx(x, a)
    qc.cx(z, y)
    qc.cx(z, x)
    qc.cx(y, a)
    qc.tdg(x)
    qc.tdg(y)
    qc.t(z)
    qc.t(a)
    qc.cx(y, a)
    qc.cx(z, y)
    qc.cx(z, x)
    qc.cx(x, a)
    qc.h(z)
    return qc
