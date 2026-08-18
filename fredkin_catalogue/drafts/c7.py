from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D1
# Source: paper 3, V gate spam (V2 = x)
# --------------------------------------------------

qc = QuantumCircuit(3, 3)

# Circuit
# Circuit

qc.cx(2, 1)

qc.csx(1, 2)

qc.csx(0, 2)

qc.cx(0, 1)

# Placeholder replaced with Controlled-SX†
from qiskit.circuit.library import SXdgGate
qc.append(SXdgGate().control(), [1, 2])

qc.cx(2, 1)

qc.cx(0, 1)

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