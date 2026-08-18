import importlib
import io
import contextlib

FILES = [
    "c1",
    "c2",
    "c3",
    "c4",
    "c5",
    "c6",
    "c7",
]


def get(counts, gate):
    return counts.get(gate, 0)


def is_lnn(qc):
    for inst in qc.data:
        if len(inst.qubits) != 2:
            continue

        q0 = qc.find_bit(inst.qubits[0]).index
        q1 = qc.find_bit(inst.qubits[1]).index

        if abs(q0 - q1) != 1:
            return False

    return True


# Open output file
with open("catalogue_summary.txt", "w") as f:

    header = (
        f"{'ID':<5}"
        f"{'Qubits':<8}"
        f"{'Anc':<5}"
        f"{'Depth':<8}"
        f"{'CX':<5}"
        f"{'CZ':<5}"
        f"{'CCX':<6}"
        f"{'T':<5}"
        f"{'Tdg':<6}"
        f"{'H':<5}"
        f"{'S':<5}"
        f"{'Sdg':<6}"
        f"{'2Q':<5}"
        f"{'LNN'}"
    )

    f.write("=" * len(header) + "\n")
    f.write(header + "\n")
    f.write("=" * len(header) + "\n")

    for file in FILES:

        # Suppress all prints while importing
        with contextlib.redirect_stdout(io.StringIO()):
            module = importlib.import_module(file)

        qc = module.qc

        counts = qc.count_ops()

        f.write(f"\nGate histogram for {file}:\n")
        for gate, count in sorted(counts.items()):
            f.write(f"  {gate:<8}: {count}\n")
        f.write("\n")

        cx = get(counts, "cx")
        cz = get(counts, "cz")
        ccx = get(counts, "ccx")
        t = get(counts, "t")
        tdg = get(counts, "tdg")
        h = get(counts, "h")
        s = get(counts, "s")
        sdg = get(counts, "sdg")

        two_qubit = sum(
            1
            for inst in qc.data
            if len(inst.qubits) == 2
        )

        ancilla = qc.num_qubits - 3

        f.write(
            f"{file:<5}"
            f"{qc.num_qubits:<8}"
            f"{ancilla:<5}"
            f"{qc.depth():<8}"
            f"{cx:<5}"
            f"{cz:<5}"
            f"{ccx:<6}"
            f"{t:<5}"
            f"{tdg:<6}"
            f"{h:<5}"
            f"{s:<5}"
            f"{sdg:<6}"
            f"{two_qubit:<5}"
            f"{'Yes' if is_lnn(qc) else 'No'}\n"
        )

print("Summary written to catalogue_summary.txt")