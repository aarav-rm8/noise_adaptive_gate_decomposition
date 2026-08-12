"""run_phase1.py — Phase 1: pre-layout, device-average CCX substitution."""
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeTorino
from noise_cost import extract_calibration, score
from noise_adaptive_decomposition import substitute_ccx_pre_layout
from qiskit import transpile

backend = FakeTorino()   # swap for real backend when ready
cal = extract_calibration(backend)

# --- real MQT Bench circuit (Grover, size 4) ---
from mqt.bench import get_benchmark, BenchmarkLevel
qc = get_benchmark(benchmark="grover", level=BenchmarkLevel.ALG, circuit_size=4).decompose(reps=1)
# ------------------------------------------------

qc_sub = substitute_ccx_pre_layout(qc, cal)

pm = generate_preset_pass_manager(optimization_level=1, backend=backend, seed_transpiler=7)
out_default = pm.run(qc)
out_phase1 = pm.run(qc_sub)

print("default ops:", dict(out_default.count_ops()))
print("phase1  ops:", dict(out_phase1.count_ops()))

od = transpile(out_default, backend, scheduling_method="asap", optimization_level=0)
op = transpile(out_phase1, backend, scheduling_method="asap", optimization_level=0)
print("default C1:", score(od, cal)["c1"])
print("phase1  C1:", score(op, cal)["c1"])