"""Export the compiled graph's Mermaid diagram as PNG."""
from agentbrief.graph import graph

png_data = graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(png_data)

print("✅ Schéma généré : graph.png")
