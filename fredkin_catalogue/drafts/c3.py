from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D1
# Source: textbook decomposition but control swapped (paper 1, fig f)
# --------------------------------------------------

qc = QuantumCircuit(3, 3)

# Circuit
# Circuit

qc.s(1)

qc.cx(2, 1)

qc.sdg(1)

qc.sx(2)

qc.t(2)

qc.ccx(0, 1, 2)

qc.t(2)

qc.cx(1, 2)

qc.t(1)

qc.tdg(2)

qc.ccx(0, 1, 2)

qc.cx(0, 1)

qc.t(2)

qc.t(0)

qc.tdg(1)

qc.h(2)

qc.cx(0, 1)

qc.cx(2, 1)
# --------------------------------------------------
# Draw Original Circuit
# --------------------------------------------------

print("=" * 50)
print("Original Circuit")
print("=" * 50)

print(qc.draw())

# --------------------------------------------------
# Reference Fredkin
# --------------------------------------------------

reference = QuantumCircuit(3)
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