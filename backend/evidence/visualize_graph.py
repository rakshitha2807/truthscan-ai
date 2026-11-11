
import json
from pathlib import Path

import networkx as nx
import matplotlib.pyplot as plt


# ==========================================
# TRUTHSCAN AI - EVIDENCE GRAPH VISUALIZATION
# ==========================================

project_root = Path(__file__).resolve().parents[2]

report_path = project_root / "reports" / "evidence_report.json"

output_folder = project_root / "reports"

output_folder.mkdir(parents=True, exist_ok=True)

output_path = output_folder / "evidence_graph.png"


# ==========================================
# LOAD JSON REPORT
# ==========================================

if not report_path.exists():
    raise FileNotFoundError(
        "Evidence report not found. Run graph.py first."
    )

with open(report_path, "r", encoding="utf-8") as file:
    report = json.load(file)


graph_data = report["evidence_graph"]

nodes = graph_data["nodes"]
edges = graph_data["edges"]


# ==========================================
# CREATE GRAPH
# ==========================================

G = nx.Graph()

for node in nodes:

    G.add_node(
        node["id"],
        label=node["label"],
        node_type=node["type"]
    )


for edge in edges:

    G.add_edge(
        edge["source"],
        edge["target"]
    )


# ==========================================
# NODE COLORS
# ==========================================

node_colors = []

for node in G.nodes:

    node_type = G.nodes[node]["node_type"]

    if node_type == "document":
        node_colors.append("skyblue")

    elif node_type == "contradiction":
        node_colors.append("tomato")

    else:
        node_colors.append("lightgray")


# ==========================================
# NODE LABELS
# ==========================================

labels = {}

for node in G.nodes:

    labels[node] = G.nodes[node]["label"]


# ==========================================
# DRAW EVIDENCE GRAPH
# ==========================================

plt.figure(figsize=(12, 8))

pos = nx.spring_layout(
    G,
    seed=42,
    k=1.5
)

nx.draw_networkx_nodes(
    G,
    pos,
    node_color=node_colors,
    node_size=3000,
    edgecolors="black"
)

nx.draw_networkx_edges(
    G,
    pos,
    width=2
)

nx.draw_networkx_labels(
    G,
    pos,
    labels=labels,
    font_size=9,
    font_weight="bold"
)


plt.title(
    "TRUTHSCAN AI - EVIDENCE GRAPH",
    fontsize=16,
    fontweight="bold"
)

plt.axis("off")

plt.tight_layout()

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("\n===================================")
print(" EVIDENCE GRAPH GENERATED")
print("===================================")

print("Total nodes:", G.number_of_nodes())

print("Total edges:", G.number_of_edges())

print("Saved location:", output_path)
