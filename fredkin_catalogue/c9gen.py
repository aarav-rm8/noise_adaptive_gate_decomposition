import numpy as np
from bqskit import compile as bqcompile
from bqskit.qis import UnitaryMatrix
from bqskit.compiler import MachineModel
from bqskit.ir.gates import CZGate, SXGate, RZGate, XGate

from qiskit import QuantumCircuit
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D9
# Source: BQSKit numerical synthesis, native Heron gate set
# --------------------------------------------------

reference = QuantumCircuit(3)
reference.append(CSwapGate(), [1, 0, 2])

target_matrix = Operator(reference).data
target = UnitaryMatrix(target_matrix)

heron_model = MachineModel(num_qudits=3, gate_set={CZGate(), SXGate(), RZGate(), XGate()})
bq_circuit = bqcompile(target, model=heron_model)
bq_circuit.save("c9_temp.qasm")
qc = QuantumCircuit.from_qasm_file("c9_temp.qasm")

print("=" * 50)
print("Original Circuit")
print("=" * 50)
print(qc.draw())

print("\nEquivalent to Fredkin?")
print(Operator(qc).equiv(Operator(reference)))

print("\nDepth:", qc.depth())
print("\nGate Counts:")
print(qc.count_ops())