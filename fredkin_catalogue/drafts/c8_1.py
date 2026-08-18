from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Generated from BQiskit compiler c8.py
# --------------------------------------------------

qc = QuantumCircuit(3, 3)

# Circuit
# Circuit
from qiskit import QuantumCircuit

qc = QuantumCircuit(3)

qc.u(3.4793970476615175, 5.509895397562807, 6.298377707368365, 0)
qc.u(3.1415926535909997, 4.671338083684936, 5.508453240073427, 1)
qc.u(5.945380912842515, 2.3440862390743153, -3.12640025608338, 2)

qc.cx(0, 2)

qc.u(0.7853981629151543, 1.5707963294835228, -3.141592653589793, 0)
qc.u(1.5707963293552587, -2.5603621445213776e-09, 2.3561944901661764, 2)

qc.cx(0, 2)

qc.u(1.5707963263619205, -0.7853981630881579, -3.141592653589793, 0)
qc.u(1.5707963267948966, -3.154661420978755e-09, 4.712388980437886, 2)

qc.cx(1, 2)

qc.u(1.5707963267945984, -9.763523323158552e-12, -3.141592653589793, 1)
qc.u(0.7853981638457352, -3.141592651519787, 3.141592650662363, 2)

qc.cx(0, 2)

qc.u(1.5707963247440822, 4.712388977080889, 0.0, 0)
qc.u(1.2518628333555617, 2.4108211632180683, 1.2342743136996281, 2)

qc.cx(0, 1)

qc.u(0.7853981620320777, 4.51934045742064e-11, -3.141592653589793, 0)
qc.u(1.51907933380405, 1.5707963267872003, -1.5707963267944989, 1)

qc.cx(0, 2)

qc.u(1.5707963255452166, -0.7975064214581595, -3.141592653589793, 0)
qc.u(1.7832748934429665, 0.7005385620861779, 4.467319896091265, 2)

qc.cx(0, 1)

qc.u(2.8037882621976618, -0.015192403101768961, 0.0, 0)
qc.u(1.5707963267961969, 3.141592653589793, 1.04585229365739e-11, 1)

print(qc.draw("text"))
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