from IPython.display import Image, display
def draw_graph(graph, save_path="graph.png"):
    png_data = graph.get_graph().draw_mermaid_png()

    # save to disk
    with open(save_path, "wb") as f:
        f.write(png_data)

    # still display in notebook
    display(Image(png_data))
    print(f"✅ Saved: {save_path}")

from workflow import build_graph
    
app = build_graph()
draw_graph(app, save_path="workflow.png")