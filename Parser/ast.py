# /Parser/ast.py
from graphviz import Digraph

class Node:
    def __init__(self, type, children=None, leaf=None):
        self.type = type
        self.children = children if children else []
        self.leaf = leaf

    def __str__(self):
        return f"Node(type={self.type}, leaf={self.leaf})"

    def get_tree_string(self, level=0):
        """
        Generate a textual representation of the tree using indentation.
        """
        indent = "  " * level
        result = f"{indent}{self.type}" + (f" : {self.leaf}" if self.leaf else "") + "\n"

        for child in self.children:
            if isinstance(child, Node):
                result += child.get_tree_string(level + 1)
            else:
                result += f"{indent}  {child}\n"

        return result

    def draw_tree(self, output_file="tree"):
        """
        Draw the tree graphically and save it as an image file.
        """
        graph = Digraph(format="png")
        graph.attr(dpi="300")
        graph.attr(rankdir="TB")
        graph.attr("node", shape="ellipse", style="filled", color="lightblue", fontname="Helvetica", fontsize="12")
        graph.attr("edge", color="gray", arrowsize="0.7")

        def add_nodes_edges(node, graph, counter=[0]):
            current_id = f"node{counter[0]}"
            counter[0] += 1

            label = f"{node.type}"
            if node.leaf is not None:
                label += f"\\n({node.leaf})"

            graph.node(current_id, label, color="deepskyblue", fontcolor="black", fontsize="10")

            for child in node.children:
                if isinstance(child, Node):
                    child_id = add_nodes_edges(child, graph, counter)
                    graph.edge(current_id, child_id, color="darkgreen")
                else:
                    leaf_id = f"leaf{counter[0]}"
                    counter[0] += 1
                    graph.node(leaf_id, str(child), shape="box", style="filled", color="lightyellow", fontcolor="black")
                    graph.edge(current_id, leaf_id, color="darkgreen")

            return current_id

        add_nodes_edges(self, graph)
        graph.render(output_file, view=True)