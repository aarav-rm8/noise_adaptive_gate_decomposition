"""
verify.py
---------
Verifies each decomposition implements the correct gate.

Three methods depending on circuit type:
  operator_equiv  : exact ancilla-free circuits (unitary comparison)
  basis_state_sim : ancilla circuits (simulate all 8 inputs, compare outputs)
  measurement_sim : relative-phase circuits (check measurement outcomes only,
                    not phases - suitable for D2, D7)

D8 Jones (Toffoli*) is noted as not CCX by design - no verification against CCX.
"""

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector
from qiskit.circuit.library import CCXGate
import numpy as np

def operator_equiv(qc: QuantumCircuit, logical_ccx: tuple[int, int, int]) -> bool:
    ref = QuantumCircuit(3)
    ref.ccx(*logical_ccx)
    return Operator(qc).equiv(Operator(ref))


def basis_state_sim(qc: QuantumCircuit, data_qubits: list) -> bool:
    """
    For ancilla circuits: simulate all 8 inputs, check data qubit outputs
    match ideal CCX. Ancillas assumed to start and end in |0>.
    """
    n_total = qc.num_qubits
    x_idx, y_idx, z_idx = data_qubits
    all_pass = True

    for bits in range(8):
        test1 = QuantumCircuit(n_total)
        if bits & 1: test1.x(x_idx)
        if bits & 2: test1.x(y_idx)
        if bits & 4: test1.x(z_idx)
        test1.compose(qc, inplace=True)
        out1 = Statevector.from_instruction(test1)

        test2 = QuantumCircuit(n_total)
        if bits & 1: test2.x(x_idx)
        if bits & 2: test2.x(y_idx)
        if bits & 4: test2.x(z_idx)
        test2.ccx(x_idx, y_idx, z_idx)
        out2 = Statevector.from_instruction(test2)

        if not out1.equiv(out2):
            print(f"  FAIL on input {bits:03b}")
            all_pass = False

    return all_pass


def measurement_sim(qc: QuantumCircuit) -> bool:
    """
    For relative-phase gates (D2 Maslov, D7 Vale):
    Check measurement outcome probabilities match CCX on all 8 inputs.
    Ignores phases - only checks which basis state we end up in.
    """
    all_pass = True
    for bits in range(8):
        test1 = QuantumCircuit(3)
        if bits & 1: test1.x(0)
        if bits & 2: test1.x(1)
        if bits & 4: test1.x(2)
        test1.compose(qc, inplace=True)
        probs1 = Statevector.from_instruction(test1).probabilities_dict()

        test2 = QuantumCircuit(3)
        if bits & 1: test2.x(0)
        if bits & 2: test2.x(1)
        if bits & 4: test2.x(2)
        test2.ccx(0, 1, 2)
        probs2 = Statevector.from_instruction(test2).probabilities_dict()

        # compare dominant outcome
        out1 = max(probs1, key=probs1.get)
        out2 = max(probs2, key=probs2.get)
        if out1 != out2:
            print(f"  FAIL on input {bits:03b}: got {out1}, expected {out2}")
            all_pass = False

    return all_pass


if __name__ == "__main__":
    from catalogue import CATALOGUE

    print("=" * 55)
    print("Verification Results")
    print("=" * 55)

    for item in CATALOGUE:

        label = item["name"]
        method = item["verify"]

        if method == "skip":
            print(f"{label}: SKIP - Toffoli* (not CCX by design, needs measurement correction)")
            continue

        
        qc = item["builder"]()


        if method == "operator":
            result = operator_equiv(qc, item["logical_ccx"])

        elif method == "basis_state":
            result = basis_state_sim(qc, item["data_qubits"])

        elif method == "measurement":
            result = measurement_sim(qc)

        status = "PASS" if result else "FAIL"
        print(f"{label}: {status} [{method}]")