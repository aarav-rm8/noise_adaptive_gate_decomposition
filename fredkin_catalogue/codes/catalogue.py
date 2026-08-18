"""
Central catalogue of all Fredkin gate decompositions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "circuits"))

from circuits import (
    d1, d2, d3, d4, d5,
    d6, d7, d8, d9, d10,
)

CATALOGUE = [
    {
        "name": "D1_Textbook",
        "builder": d1.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Standard textbook",
        "year": None,
        "exact": True,
        "notes": "CX + CCX + CX",
    },
    {
        "name": "D2_Cruz_FigE",
        "builder": d2.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Cruz, Murta et al.",
        "exact": True,
        "notes": "CCX with H-T sandwich (Fig. e)",
    },
    {
        "name": "D3_Cruz_FigF",
        "builder": d3.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Cruz, Murta et al.",
        "exact": True,
        "notes": "CCX with control swapped (Fig. f)",
    },
    {
        "name": "D4_Cruz_FigB",
        "builder": d4.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Cruz, Murta et al.",
        "exact": True,
        "notes": "CCX-free, SX + phase rotations (Fig. b)",
    },
    {
        "name": "D5_Cruz_FigC",
        "builder": d5.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Cruz, Murta et al.",
        "exact": True,
        "notes": "Control in centre q1 (Fig. c)",
    },
    {
        "name": "D6_Saha",
        "builder": d6.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Saha, Khanna et al.",
        "exact": True,
        "notes": "CCX with S-H framing",
    },
    {
        "name": "D7_Yu_Vgate",
        "builder": d7.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "Yu, Yang et al.",
        "exact": True,
        "notes": "V-gate decomposition using CSX / CSXdg",
    },
    {
        "name": "D8_BQiskit_Free",
        "builder": d8.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "BQiskit (no restrictions)",
        "exact": True,
        "notes": "Numerically synthesised — U + CX, any topology",
    },
    {
        "name": "D9_BQiskit_Native",
        "builder": d9.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "BQiskit (native gates only)",
        "exact": True,
        "notes": "Numerically synthesised — Rz + SX + CZ only",
    },
    {
        "name": "D10_BQiskit_NonLNN",
        "builder": d10.build,
        "num_qubits": 3,
        "layout_type": 3,
        "ancillas": 0,
        "paper": "BQiskit (non-LNN, any gates)",
        "exact": True,
        "notes": "Numerically synthesised — U + CX, non-LNN topology",
    },
]
