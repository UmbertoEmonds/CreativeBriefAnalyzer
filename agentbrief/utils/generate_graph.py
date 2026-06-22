"""
Utility script to generate a PNG representation of the LangGraph graph.

Exports the compiled graph's Mermaid diagram as a PNG image saved to
the current working directory.
"""
from agentbrief.graph import graph

png_data = graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(png_data)

print("✅ Schéma généré : graph.png")