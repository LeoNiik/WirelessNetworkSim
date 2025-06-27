import os
import matplotlib.pyplot as plt
import networkx as nx


def _ensure_dir(filepath):
    """Crea la cartella se non esiste."""
    folder = os.path.dirname(filepath)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


def visualize_network_matplotlib(network, filename=None, title=None):
    """
    Disegna la rete con matplotlib + networkx.
    - network: oggetto SensorNetwork
    - filename: percorso file per salvare (png); se None mostra a schermo
    - title: titolo opzionale
    """
    # Costruisci il grafo
    G = nx.Graph()
    # Usa node.node_id anziché node.id
    for node in network.nodes:
        G.add_node(node.node_id, pos=(node.x, node.y))
    for a, b, delay in network.get_all_links():
        G.add_edge(a, b, weight=delay)

    pos = nx.get_node_attributes(G, 'pos')
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_size=300, node_color='lightblue')
    # Etichette dei pesi
    labels = nx.get_edge_attributes(G, 'weight')
    labels = {edge: f"{w:.2f}" for edge, w in labels.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=8)

    if title:
        plt.title(title)

    if filename:
        _ensure_dir(filename)
        plt.savefig(filename, dpi=150)
        plt.close()
    else:
        plt.show()


# Alias per uniformità
visualize_network = visualize_network_matplotlib


def visualize_adjacency_list(network, filename=None, title=None):
    """
    Genera la rappresentazione in lista di adiacenza.
    - network: oggetto SensorNetwork
    - filename: se fornito, salva la lista in un .txt
    - title: titolo opzionale
    """
    # Costruisci dizionario dei vicini
    adj = {node.node_id: {} for node in network.nodes}
    for a, b, delay in network.get_all_links():
        adj[a][b] = delay
        adj[b][a] = delay

    lines = []
    if title:
        lines.append(title)
        lines.append('-' * len(title))

    for node_id in sorted(adj):
        neigh = adj[node_id]
        parts = [f"{nbr}({d:.2f})" for nbr, d in sorted(neigh.items())]
        lines.append(f"[{node_id}]: " + ", ".join(parts))

    text = "\n".join(lines)

    if filename:
        # salva su file di testo
        txt_path = filename if filename.endswith('.txt') else filename + '.txt'
        _ensure_dir(txt_path)
        with open(txt_path, 'w') as f:
            f.write(text)
    else:
        print(text)
