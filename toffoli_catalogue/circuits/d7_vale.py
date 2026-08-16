"""
D7 - Rotation-Based Relative-Phase Toffoli (Vale et al., 2023)
Source: Vale et al., arXiv:2302.06504, Fig. 4
Exact: No (relative phase, up to diagonal gate)
Ancilla: None | CNOT count: 3
Gate library: {Ry(theta), CNOT}
"""
from qiskit import QuantumCircuit
from math import pi

def build() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="D7_Vale")
    q0, q1, q2 = 0, 1, 2
    qc.ry(-pi/4, q2)
    qc.cx(q0, q2)
    qc.ry(-pi/4, q2)
    qc.cx(q1, q2)
    qc.ry(pi/4, q2)
    qc.cx(q0, q2)
    qc.ry(pi/4, q2)
    return qc
