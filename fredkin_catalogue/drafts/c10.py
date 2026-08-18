from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator

# --------------------------------------------------
# Decomposition ID: D1
# Source: paper 3, V gate spam (V2 = x)
# --------------------------------------------------

qc = QuantumCircuit(3, 3)

from qiskit import QuantumCircuit

qc = QuantumCircuit(3)

qc.u(1.9166571165247197, 1.8330875883089326, 4.082130319284095, 0)
qc.u(2.5138615327851703e-13, 7.526113420309917, 1.834250789981115, 1)
qc.u(3.5724508137510265, 4.088647682298549, 3.412316938343392, 2)

qc.cx(0, 2)

qc.u(1.5707963267906497, -2.3561944901924443, -3.141592653589793, 0)
qc.u(0.7853981633961814, -5.517808432387028e-13, 3.141592653590574, 2)

qc.cx(1, 2)

qc.u(1.605153646058932e-13, -1.109624471564843, -1.1102230246251565e-16, 1)
qc.u(2.3561944901914624, 1.8436830670740138e-12, 2.6073615981759965e-12, 2)

qc.cx(0, 2)

qc.u(1.570796326790555, 4.712388980385308, 0.0, 0)
qc.u(2.3561944901930105, 1.9964030428809565e-12, 3.1415926535926166, 2)

qc.cx(1, 2)

qc.u(1.570796326795717, 3.173246251927742e-13, 0.0, 1)
qc.u(1.5707963267950074, 0.7853981633962477, 4.7123889803845795, 2)

qc.cx(0, 1)

qc.u(0.7853981633973544, -0.6237412981420045, -3.141592653589793, 0)
qc.u(1.5707963267945872, -3.141592653589793, -3.3861802251067274e-13, 1)

qc.cx(0, 2)

qc.u(0.4308581601591201, -0.27072428470356624, 0.0, 0)
qc.u(1.5707963267929184, 3.1415926535882877, 0.6506018989081686, 2)

qc.cx(1, 2)

qc.u(3.1415926535895795, -2.752952594943943, 3.1415926535897936, 1)
qc.u(1.1598989175814847, 3.195177247021193, -0.13348199662481797, 2)

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