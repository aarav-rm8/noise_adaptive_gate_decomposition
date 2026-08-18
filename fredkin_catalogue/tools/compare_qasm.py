from qiskit import QuantumCircuit


def circuits_identical(file1, file2):
    qc1 = QuantumCircuit.from_qasm_file(file1)
    qc2 = QuantumCircuit.from_qasm_file(file2)

    # Same number of qubits/classical bits?
    if qc1.num_qubits != qc2.num_qubits:
        return False

    if qc1.num_clbits != qc2.num_clbits:
        return False

    # Same number of instructions?
    if len(qc1.data) != len(qc2.data):
        return False

    # Compare every instruction
    for i, (inst1, inst2) in enumerate(zip(qc1.data, qc2.data)):

        op1 = inst1.operation
        op2 = inst2.operation

        # Gate name
        if op1.name != op2.name:
            print(f"Difference at instruction {i}:")
            print(f"  Gate: {op1.name} != {op2.name}")
            return False

        # Parameters
        if len(op1.params) != len(op2.params):
            print(f"Difference at instruction {i}: parameter count differs.")
            return False

        for p1, p2 in zip(op1.params, op2.params):
            if abs(float(p1) - float(p2)) > 1e-12:
                print(f"Difference at instruction {i}:")
                print(f"  Parameters: {op1.params} != {op2.params}")
                return False

        # Qubit indices
        q1 = [qc1.find_bit(q).index for q in inst1.qubits]
        q2 = [qc2.find_bit(q).index for q in inst2.qubits]

        if q1 != q2:
            print(f"Difference at instruction {i}:")
            print(f"  Qubits: {q1} != {q2}")
            return False

        # Classical bits
        c1 = [qc1.find_bit(c).index for c in inst1.clbits]
        c2 = [qc2.find_bit(c).index for c in inst2.clbits]

        if c1 != c2:
            print(f"Difference at instruction {i}:")
            print(f"  Classical bits: {c1} != {c2}")
            return False

    return True


if __name__ == "__main__":
    file1 = "circuit1.qasm"
    file2 = "circuit2.qasm"

    if circuits_identical(file1, file2):
        print("The circuits are IDENTICAL.")
    else:
        print("The circuits are DIFFERENT.")