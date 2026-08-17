"""
D4 - Linear-Connectivity Exact Toffoli (Cruz & Murta, 2024)
Source: arXiv:2305.18128, Fig. 2(a)

Exact: Yes
Ancilla: None
CNOT count: 8

Implements CCX(0,2,1), where:
    q0 = control
    q1 = target (middle qubit)
    q2 = control

Only adjacent interactions (0,1) and (1,2) are used.
Verified against CCX(0,2,1) using Operator.equiv().
"""

from qiskit import QuantumCircuit


def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D4_Cruz_Linear")

    # controls = q0,q2 ; target = q1 (middle)
    c1, t, c2 = 0, 1, 2

    qc.h(t)
    qc.cx(c1, t);  qc.tdg(c1)
    qc.cx(t, c2);  qc.t(t);    qc.tdg(c2)
    qc.cx(c1, t);  qc.cx(t, c2); qc.tdg(t); qc.t(c2)
    qc.cx(c1, t);  qc.cx(t, c2); qc.t(c2)
    qc.cx(c1, t)
    qc.cx(t, c2)
    qc.h(t);       qc.tdg(c2)

    return qc