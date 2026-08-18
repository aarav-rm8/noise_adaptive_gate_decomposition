import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator


def is_lnn(circuit, line_order=(0, 1, 2)):
    """
    Returns True if every 2-qubit gate in `circuit` only acts on
    physically adjacent qubits in `line_order`.
    Prints any long-range (non-adjacent) gates found.
    """
    adjacent_pairs = {frozenset((line_order[i], line_order[i + 1]))
                       for i in range(len(line_order) - 1)}

    violations = []
    for instr, qargs, _ in circuit.data:
        if len(qargs) == 2:
            idxs = [circuit.find_bit(q).index for q in qargs]
            pair = frozenset(idxs)
            if pair not in adjacent_pairs:
                violations.append((instr.name, idxs))

    if violations:
        print("Non-adjacent (non-LNN) gates found:")
        for name, idxs in violations:
            print(f"  {name} on qubits {idxs}")
        return False

    print("No long-range gates found — circuit is LNN.")
    return True


# --------------------------------------------------
# Standalone usage: paste your circuit here and run
# python lnn_checker.py
# --------------------------------------------------
if __name__ == "__main__":

    qc = QuantumCircuit(3, 3)

    # ---- PASTE YOUR CIRCUIT LINES HERE (same as c1.py, c7.py, etc.) ----
    
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

    
    # ----------------------------------------------------------------

    print("=" * 50)
    print("Circuit")
    print("=" * 50)
    print(qc.draw())

    print("\n" + "=" * 50)
    print("LNN Check")
    print("=" * 50)
    result = is_lnn(qc)
    print("\nIs LNN?", result)
    print("Is non-LNN?", not result)