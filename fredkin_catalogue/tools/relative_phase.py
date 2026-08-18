import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import CSwapGate
from qiskit.quantum_info import Operator


def check_relative_phase_equivalence(qc, reference, tol=1e-6):
    """
    Checks whether `qc` implements `reference` up to a per-basis-state
    (relative) phase, rather than only a single global phase.

    Returns a dict with:
      - exact_equivalent: True if identical (no phase difference at all)
      - global_phase_equivalent: True if equal up to ONE shared phase
      - relative_phase_equivalent: True if equal up to a DIFFERENT phase
                                    per basis state (the interesting case)
      - phases: the per-basis-state phase angles (radians), if applicable
    """
    U = Operator(qc).data
    V = Operator(reference).data

    # M = U * V^-1. If qc == reference up to per-basis-state phases,
    # M must be a diagonal matrix with unit-modulus entries.
    M = U @ np.conjugate(V.T)

    diag_part = np.diag(np.diag(M))
    off_diagonal_error = np.linalg.norm(M - diag_part)
    is_relative_phase_equiv = off_diagonal_error < tol

    result = {
        "relative_phase_equivalent": is_relative_phase_equiv,
        "off_diagonal_error": off_diagonal_error,
        "exact_equivalent": False,
        "global_phase_equivalent": False,
        "phases_per_basis_state": None,
    }

    if is_relative_phase_equiv:
        diag_entries = np.diag(M)
        phases = np.angle(diag_entries)
        result["phases_per_basis_state"] = phases

        # Global phase = ALL diagonal entries share the same phase
        result["global_phase_equivalent"] = np.allclose(
            diag_entries, diag_entries[0], atol=tol
        )
        # Exact = global phase AND that phase is ~0 (i.e. truly identical)
        result["exact_equivalent"] = (
            result["global_phase_equivalent"]
            and np.isclose(diag_entries[0], 1.0, atol=tol)
        )

    return result


def print_relative_phase_report(qc, reference):
    r = check_relative_phase_equivalence(qc, reference)
    print("Exact equivalent (identical)?      ", r["exact_equivalent"])
    print("Global-phase equivalent?           ", r["global_phase_equivalent"])
    print("Relative-phase equivalent?         ", r["relative_phase_equivalent"])
    print("Off-diagonal error (should be ~0): ", r["off_diagonal_error"])
    if r["phases_per_basis_state"] is not None:
        print("\nPer-basis-state phases (radians):")
        for i, p in enumerate(r["phases_per_basis_state"]):
            print(f"  |{i:03b}>: {p:.4f} rad")
    return r


# --------------------------------------------------
# Standalone usage: paste your circuit here and run
# python relative_phase_checker.py
# --------------------------------------------------
if __name__ == "__main__":

    qc = QuantumCircuit(3, 3)

    # ---- PASTE YOUR CIRCUIT LINES HERE ----
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
    # ----------------------------------------

    reference = QuantumCircuit(3)
    reference.append(CSwapGate(), [1, 0, 2])   # match your convention exactly!

    print("=" * 50)
    print("Circuit")
    print("=" * 50)
    print(qc.draw())

    print("\n" + "=" * 50)
    print("Relative Phase Check")
    print("=" * 50)
    print_relative_phase_report(qc, reference)