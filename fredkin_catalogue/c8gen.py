import numpy as np
from bqskit import compile as bqcompile
from bqskit.qis import UnitaryMatrix

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D8
# Source: BQSKit numerical synthesis, no constraints
# --------------------------------------------------

# Reference Fredkin FIRST — everything else derives from this
reference = QuantumCircuit(3)
reference.append(CSwapGate(), [1, 0, 2])

# Get the exact target matrix from the reference itself (no hand errors possible)
target_matrix = Operator(reference).data
target = UnitaryMatrix(target_matrix)

# Synthesize
bq_circuit = bqcompile(target)
bq_circuit.save("c8_temp.qasm")
qc = QuantumCircuit.from_qasm_file("c8_temp.qasm")

# --------------------------------------------------
# Draw Original Circuit
# --------------------------------------------------
print("=" * 50)
print("Original Circuit")
print("=" * 50)
print(qc.draw())

# --------------------------------------------------
# Verify
# --------------------------------------------------
print("\nEquivalent to Fredkin?")
print(Operator(qc).equiv(Operator(reference)))

print("\nDepth:", qc.depth())
print("\nGate Counts:")
print(qc.count_ops())

# --------------------------------------------------
# Transpile to Heron basis
# --------------------------------------------------
native = transpile(qc, basis_gates=["rz", "sx", "x", "cz"], optimization_level=3)

print("\nNative Circuit\n")
print(native.draw())
print("\nDepth:", native.depth())
print("\nGate Counts:")
print(native.count_ops())
print("\nEquivalent after transpilation?")
print(Operator(native).equiv(Operator(reference)))