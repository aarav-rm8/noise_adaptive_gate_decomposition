import numpy as np
import networkx as nx
from bqskit import compile as bqcompile
from bqskit.qis import UnitaryMatrix
from bqskit.compiler import MachineModel

from qiskit import QuantumCircuit
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D10
# Source: BQSKit numerical synthesis, all-to-all connectivity
# --------------------------------------------------

reference = QuantumCircuit(3)
reference.append(CSwapGate(), [1, 0, 2])

target_matrix = Operator(reference).data
target = UnitaryMatrix(target_matrix)

all_to_all_model = MachineModel(3, coupling_graph=list(nx.complete_graph(3).edges))
bq_circuit = bqcompile(target, model=all_to_all_model)
bq_circuit.save("c10_temp.qasm")
qc = QuantumCircuit.from_qasm_file("c10_temp.qasm")

print("=" * 50)
print("Original Circuit")
print("=" * 50)
print(qc.draw())

print("\nEquivalent to Fredkin?")
print(Operator(qc).equiv(Operator(reference)))

print("\nDepth:", qc.depth())
print("\nGate Counts:")
print(qc.count_ops())