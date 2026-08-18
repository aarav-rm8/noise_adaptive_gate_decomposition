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
from qiskit import QuantumCircuit

qc = QuantumCircuit(3)

qc.rz(-0.5231069014454306, 0)
qc.rz(-1.4838151099640227, 1)
qc.rz(0.7182845428822082, 2)

qc.sx(0)
qc.sx(1)
qc.sx(2)

qc.rz(-1.5700597387705795, 0)
qc.rz(-3.1415926535894307, 1)
qc.rz(-0.7191501398661053, 2)

qc.sx(0)
qc.sx(1)
qc.sx(2)

qc.rz(-2.7958989133079104, 0)
qc.rz(-1.269981126317063, 1)
qc.rz(1.7190010880246938, 2)

qc.cz(0, 2)

qc.rz(-1.1623963788937104, 0)
qc.rz(1.8360142568718922, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.063936878450237, 0)
qc.rz(-2.67369560134728, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.1893622499743293, 0)
qc.rz(0.5437868289956231, 2)

qc.cz(0, 2)

qc.rz(2.035479990660737, 0)
qc.rz(-1.56712442296064, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-0.12985477506430243, 0)
qc.rz(-1.5104794027168573, 2)

qc.sx(0)
qc.sx(2)

qc.rz(0.19117823494969866, 0)
qc.rz(0.7519451406194158, 2)

qc.cz(0, 2)

qc.rz(-2.491571530325853, 0)
qc.rz(2.5349642058299064, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.6432940425514264, 0)
qc.rz(-1.1416536489685551, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-0.24014105432525312, 0)
qc.rz(1.05629603874279, 2)

qc.cz(0, 2)

qc.rz(1.8973515806480297, 0)
qc.rz(2.2865973020974586, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-2.563689091480687, 0)
qc.rz(-1.8423912680055263, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.433817220104939, 0)
qc.rz(2.2388110158983334, 2)

qc.cz(1, 2)

qc.rz(-2.0988911702569393, 1)
qc.rz(-2.242789687040222, 2)

qc.sx(1)
qc.sx(2)

qc.rz(-3.14159265358977, 1)
qc.rz(-0.785398163398721, 2)

qc.sx(1)
qc.sx(2)

qc.rz(-2.675703378503659, 1)
qc.rz(2.4524910768508814, 2)

qc.cz(0, 2)

qc.rz(0.5961179132570238, 0)
qc.rz(-2.452491076859301, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.5707963269332383, 0)
qc.rz(-2.3561944901926477, 2)

qc.sx(0)
qc.sx(2)

qc.rz(0.939780234095517, 0)
qc.rz(0.7824365994903641, 2)

qc.cz(0, 1)

qc.rz(-2.5105765617927847, 0)
qc.rz(-1.2464075560425183, 1)

qc.sx(0)
qc.sx(1)

qc.rz(-0.7853981633949996, 0)
qc.rz(-3.1415926535897505, 1)

qc.sx(0)
qc.sx(1)

qc.rz(0.5943173421560259, 0)
qc.rz(2.0809539050951944, 1)

qc.cz(0, 2)

qc.rz(2.5472753105510373, 0)
qc.rz(-0.6578511539566945, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.5707963268582885, 0)
qc.rz(-2.3263330047548045, 2)

qc.sx(0)
qc.sx(2)

qc.rz(-1.733340705682533, 0)
qc.rz(-0.8960527119118105, 2)

qc.cz(0, 1)

qc.rz(-3.110206542202592, 0)
qc.rz(0.02690977833382524, 1)

qc.sx(0)
qc.sx(1)

qc.rz(-2.377863483997321, 0)
qc.rz(-3.1415926535894094, 1)

qc.sx(0)
qc.sx(1)

qc.rz(2.4261910617895595, 0)
qc.rz(1.16914751385411, 1)

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
reference.append(CSwapGate(), [1, 0, 2])

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