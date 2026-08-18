"""
visual.py
---------
Reads summary.json and generates four bar charts into nan/plots/:
  - min_cz.png
  - avg_cz.png
  - min_depth.png
  - avg_depth.png

Run after analyze.py:
    python visual.py
"""

import json
import os
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)

with open(os.path.join(HERE, "summary.json"), "r") as f:
    summary = json.load(f)

plots_dir = os.path.join(HERE, "plots")
os.makedirs(plots_dir, exist_ok=True)

# Sort decompositions numerically by their D-number (D1, D2, ..., D10)
names = sorted(summary.keys(), key=lambda x: int(x.split("_")[0][1:]))

min_cz    = [summary[n]["min_cz"]    for n in names]
avg_cz    = [summary[n]["avg_cz"]    for n in names]
min_depth = [summary[n]["min_depth"] for n in names]
avg_depth = [summary[n]["avg_depth"] for n in names]

# Short x-axis labels (D1 .. D10) to keep the plot clean
short_names = [n.split("_")[0] for n in names]


def save_bar(values, ylabel, title, filename):
    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(short_names, values, color="#4C72B0", edgecolor="white", linewidth=0.6)

    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel("Decomposition", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(axis="x", rotation=0)

    # Value labels above each bar
    for bar, value in zip(bars, values):
        label = f"{value:.2f}" if isinstance(value, float) else str(value)
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,
            label,
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_ylim(0, max(values) * 1.15)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = os.path.join(plots_dir, filename)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  Saved {out}")


save_bar(min_cz,    "Minimum CZ Count",    "Minimum CZ Count per Decomposition",    "min_cz.png")
save_bar(avg_cz,    "Average CZ Count",    "Average CZ Count per Decomposition",    "avg_cz.png")
save_bar(min_depth, "Minimum Circuit Depth", "Minimum Depth per Decomposition",     "min_depth.png")
save_bar(avg_depth, "Average Circuit Depth", "Average Depth per Decomposition",     "avg_depth.png")

print("\nAll plots saved to", plots_dir)
