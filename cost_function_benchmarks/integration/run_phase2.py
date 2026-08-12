"""run_phase2.py — Phase 2: run the FULL pipeline once per exact candidate
decomposition, keep whichever gives lowest realized C1. Does NOT patch an
already-routed circuit (that approach was tried and found architecturally
broken: Sabre's router doesn't preserve block-local qubit adjacency after
a gate finishes, so post-routing feasibility checks always fail). This
instead lets full layout+routing run independently per candidate and
compares the finished results -- verified correct on a real MQT Bench
circuit (Grover, size 4): winner (D5_Nielsen_Chuang) matches default's
dominant measurement outcome exactly.
"""
from qiskit import transpile
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeTorino
from noise_cost import extract_calibration, score
from noise_adaptive_decomposition import _CANDIDATES, NATIVE_BASIS, _reorder_to_role_order

backend = FakeTorino()   # swap for real backend when ready
cal = extract_calibration(backend)

# --- real MQT Bench circuit ---
from mqt.bench import get_benchmark, BenchmarkLevel
qc = get_benchmark(benchmark="grover", level=BenchmarkLevel.ALG, circuit_size=4).decompose(reps=1)
# -------------------------------


def substitute_specific(qc, item):
    native = transpile(item["builder"](), basis_gates=NATIVE_BASIS, optimization_level=1)
    logical_ccx = item.get("logical_ccx", (0, 1, 2))
    reordered = _reorder_to_role_order(native, logical_ccx)  # CRITICAL: fixes
    # permuted decompositions like D4 (logical_ccx != (0,1,2)) -- omitting
    # this silently substitutes the WRONG logical gate.
    dag = circuit_to_dag(qc)
    for node in list(dag.op_nodes()):
        if node.op.name != "ccx":
            continue
        sub_dag = circuit_to_dag(reordered)
        dag.substitute_node_with_dag(node, sub_dag, wires=list(sub_dag.qubits))
    return dag_to_circuit(dag)


pm_kwargs = dict(optimization_level=1, backend=backend, seed_transpiler=7)

results = []
for item in _CANDIDATES:  # exact-only, ancilla-free -- D1,D3,D4,D5,D9,D10
    qc_sub = substitute_specific(qc, item)
    out = generate_preset_pass_manager(**pm_kwargs).run(qc_sub)
    sched = transpile(out, backend, scheduling_method="asap", optimization_level=0)
    c1 = score(sched, cal)["c1"]
    results.append((item["name"], c1, out))
    print(f"{item['name']:20s} C1={c1:.5f}  depth={out.depth()}")

results.sort(key=lambda r: r[1])
winner_name, winner_c1, winner_circuit = results[0]

out_default = generate_preset_pass_manager(**pm_kwargs).run(qc)
od_sched = transpile(out_default, backend, scheduling_method="asap", optimization_level=0)
default_c1 = score(od_sched, cal)["c1"]

print(f"\nBest: {winner_name}  C1={winner_c1:.5f}")
print(f"Default C1: {default_c1:.5f}")
print(f"Improvement: {(default_c1 - winner_c1) / default_c1 * 100:.1f}%")