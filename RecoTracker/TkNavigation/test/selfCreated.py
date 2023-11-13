import pygraphviz as pgv

# Create a new graph
G = pgv.AGraph(strict=False, directed=True)
# Save or display the graph with the "dot" layout algorithm


# Define node attributes
node_attrs = {
    'shape': 'ellipse',
    'color': 'black',
    'fillcolor': '#EDEDED',
    'style': 'filled'
}

# Modify node names as needed
node_names = [
    'BPix1', 'BPix2', 'BPix3', 'BPix4', 'FNPix1', 'FNPix2', 'FNPix3', 'FPPix1', 'FPPix2', 'FPPix3', 'TIB1', 'TIB2',
    'TIDN1', 'TIDN2', 'TIDN3', 'TIDP1', 'TIDP2', 'TIDP3'
]

# Add nodes to the graph
for node_name in node_names:
    G.add_node(node_name, **node_attrs)

# Define connections between nodes
# Define a list of all connections
connections = [
    ('BPix1', 'BPix2'), ('BPix1', 'FNPix1'), ('BPix1', 'TIB1'), ('BPix1', 'FPPix1'),
    ('BPix2', 'BPix3'), ('BPix2', 'FNPix1'), ('BPix2', 'TIB1'), ('BPix2', 'FPPix1'),
    ('BPix3', 'BPix4'), ('BPix3', 'FNPix1'), ('BPix3', 'TIB1'), ('BPix3', 'FPPix1'),
    ('BPix4', 'TIB1'), ('BPix4', 'TIB2'), ('BPix4', 'TIDN1'), ('BPix4', 'TIDP1'),
    ('FNPix1', 'FNPix2'), ('FNPix1', 'TIB1'), ('FNPix1', 'TIDN1'), ('FNPix1', 'TIDN2'), ('FNPix1', 'TIDN3'),
    ('FNPix2', 'FNPix3'), ('FNPix2', 'TIB1'), ('FNPix2', 'TIDN1'), ('FNPix2', 'TIDN2'), ('FNPix2', 'TIDN3'),
    ('FNPix3', 'TIB1'), ('FNPix3', 'TIDN1'), ('FNPix3', 'TIDN2'), ('FNPix3', 'TIDN3'),
    ('FPPix1', 'FPPix2'), ('FPPix1', 'TIB1'), ('FPPix1', 'TIDP1'), ('FPPix1', 'TIDP2'), ('FPPix1', 'TIDP3'),
    ('FPPix2', 'FPPix3'), ('FPPix2', 'TIB1'), ('FPPix2', 'TIDP1'), ('FPPix2', 'TIDP2'), ('FPPix2', 'TIDP3'),
    ('FPPix3', 'TIB1'), ('FPPix3', 'TIDP1'), ('FPPix3', 'TIDP2'), ('FPPix3', 'TIDP3'),
    ('TIB1', 'TIB2'), ('TIB1', 'TIDN1'), ('TIB1', 'TIDP1'),
    ('TIB2', 'TIDN1'), ('TIB2', 'TIDP1'), 
    ('TIDN1', 'TIDN2'),
    ('TIDN2', 'TIDN3'),
    ('TIDP1', 'TIDP2'),
    ('TIDP2', 'TIDP3'),
]

# Define a list of direct connections
direct_connections = [
    ('BPix1', 'BPix2'), ('BPix2', 'BPix3'), ('BPix3', 'BPix4'), ('BPix4','TIB1'),
    ('FNPix1', 'FNPix2'), ('FNPix2', 'FNPix3'), ('FNPix3','TIB1'),
    ('FPPix1', 'FPPix2'), ('FPPix2', 'FPPix3'), ('FPPix3', 'TIB1'),
    ('TIB1', 'TIB2'),
    ('TIDN1', 'TIDN2'), ('TIDN2', 'TIDN3'), ('TIB2', 'TIDP1'),
]

# You can use these lists for further processing in your Python code.


# Add nodes and edges to the graph with line styles
for start, end in connections:
    style = 'solid' if (start, end) in direct_connections else 'dashed'
    G.add_edge(start, end, color='black', style=style)
    
# Save or display the graph with the "dot" layout algorithm
G.draw('graph.png', format='png', prog='dot')

