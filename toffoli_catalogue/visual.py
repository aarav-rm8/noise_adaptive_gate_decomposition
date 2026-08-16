import json
import os
import matplotlib.pyplot as plt

# -------------------------
# Load summary
# -------------------------
with open("summary.json", "r") as f:
    summary = json.load(f)

os.makedirs("plots", exist_ok=True)

# Sort decompositions numerically (D1, D2, ..., D10)
names = sorted(summary.keys(), key=lambda x: int(x.split("_")[0][1:]))

min_cz = [summary[n]["min_cz"] for n in names]
avg_cz = [summary[n]["avg_cz"] for n in names]
min_depth = [summary[n]["min_depth"] for n in names]
avg_depth = [summary[n]["avg_depth"] for n in names]


def save_bar(values, ylabel, title, filename):
    plt.figure(figsize=(10, 5))
    bars = plt.bar(names, values)

    plt.title(title)
    plt.xlabel("Decomposition")
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")

    # write value above each bar
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{value:.2f}" if isinstance(value, float) else str(value),
            ha="center",
            va="bottom",
            fontsize=8
        )

    plt.tight_layout()
    plt.savefig(os.path.join("plots", filename), dpi=300)
    plt.close()


save_bar(
    min_cz,
    "Minimum CZ Count",
    "Minimum CZ Count per Decomposition",
    "min_cz.png",
)

save_bar(
    avg_cz,
    "Average CZ Count",
    "Average CZ Count per Decomposition",
    "avg_cz.png",
)

save_bar(
    min_depth,
    "Minimum Circuit Depth",
    "Minimum Depth per Decomposition",
    "min_depth.png",
)

save_bar(
    avg_depth,
    "Average Circuit Depth",
    "Average Depth per Decomposition",
    "avg_depth.png",
)

print("Saved plots to ./plots/")
print("  - min_cz.png")
print("  - avg_cz.png")
print("  - min_depth.png")
print("  - avg_depth.png")