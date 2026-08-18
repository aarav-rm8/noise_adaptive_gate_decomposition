import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D1
# Source: paper 2, T-depth 1 Fredkin gate
# --------------------------------------------------

qc = QuantumCircuit(7, name="CSWAP_Tdepth1")

# Qubit Mapping:
# q0: Control qubit
# q1: Target 1
# q2: Target 2
# q3..q6: Ancilla qubits initialized to |0>

# ==========================================
# Pre-processing (Convert CCZ to CSWAP)
# ==========================================
qc.cx(2, 1)
qc.h(2)

# ==========================================
# 1. State Preparation (CNOT Network)
# ==========================================
# Column 1
qc.cx(0, 3)
qc.cx(1, 5)

# Column 2
qc.cx(1, 4)
qc.cx(2, 5)

# Column 3
qc.cx(2, 6)

# Column 4
qc.cx(3, 6)
qc.cx(0, 4)

# Column 5
qc.cx(5, 3)

qc.barrier()  # Visual separator

# ==========================================
# 2. Parallel T / T† Layer (T-depth 1)
# ==========================================
qc.t(0)
qc.t(1)
qc.t(2)
qc.t(3)

qc.tdg(4)
qc.tdg(5)
qc.tdg(6)

qc.barrier()  # Visual separator

# ==========================================
# 3. Uncomputation (Reverse CNOT Network)
# ==========================================
# Column 5 inverted
qc.cx(5, 3)

# Column 4 inverted
qc.cx(0, 4)
qc.cx(3, 6)

# Column 3 inverted
qc.cx(2, 6)

# Column 2 inverted
qc.cx(2, 5)
qc.cx(1, 4)

# Column 1 inverted
qc.cx(1, 5)
qc.cx(0, 3)

# ==========================================
# Post-processing (Convert CCZ to CSWAP)
# ==========================================
qc.h(2)
qc.cx(2, 1)


# --------------------------------------------------
# Draw Original Circuit
# --------------------------------------------------

print("=" * 50)
print("Original Circuit")
print("=" * 50)

print(qc.draw())

# --------------------------------------------------
# Reference Fredkin (7 Qubits to match qc shape)
# --------------------------------------------------

reference = QuantumCircuit(7)
reference.append(CSwapGate(), [0, 1, 2])

# --------------------------------------------------
# Verify
# --------------------------------------------------

print("\nEquivalent to Fredkin?")
print(Operator(qc).equiv(Operator(reference)))

# --------------------------------------------------
# Transpile to Heron basis
# --------------------------------------------------

native = transpile(
    qc,
    basis_gates=["rz", "sx", "x", "cz"],
    optimization_level=3
)

print("\nNative Circuit\n")
print(native.draw())

print("\nDepth:", native.depth())

print("\nGate Counts:")
print(native.count_ops())

print("\nEquivalent after transpilation?")
print(Operator(native).equiv(Operator(reference)))