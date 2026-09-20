import networkx as nx
import numpy as np
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional

class TopologyType(str, Enum):
    ER_RANDOM = "ER_RANDOM"
    WS_SMALL_WORLD = "WS_SMALL_WORLD"
    BA_SCALE_FREE = "BA_SCALE_FREE"
    SBM_COMMUNITY = "SBM_COMMUNITY"

class NetworkBuilder:
    """
    Xây dựng và quản lý cấu trúc đồ thị mạng phức hợp (Complex Networks)
    theo chuẩn nghiên cứu khoa học: ER, WS, BA, SBM.
    """

    @staticmethod
    def generate_graph(
        topology: TopologyType,
        num_nodes: int = 30,
        seed: Optional[int] = 42,
        **kwargs
    ) -> nx.Graph:
        """
        Khởi tạo đồ thị NetworkX theo cấu trúc topo được chọn.
        """
        if topology == TopologyType.ER_RANDOM:
            # Erdős–Rényi: p mặc định để đồ thị liên thông xấp xỉ
            p = kwargs.get("p", max(0.12, 2.5 * np.log(num_nodes) / num_nodes))
            G = nx.erdos_renyi_graph(n=num_nodes, p=p, seed=seed)

        elif topology == TopologyType.WS_SMALL_WORLD:
            # Watts–Strogatz: k láng giềng gần nhất, p xác suất nối tắt
            k = kwargs.get("k", max(4, int(num_nodes * 0.15)))
            if k % 2 != 0:
                k += 1
            k = min(k, num_nodes - 1)
            p = kwargs.get("rewiring_prob", 0.15)
            G = nx.watts_strogatz_graph(n=num_nodes, k=k, p=p, seed=seed)

        elif topology == TopologyType.BA_SCALE_FREE:
            # Barabási–Albert: m liên kết mới mỗi khi thêm nút
            m = kwargs.get("m", max(2, int(num_nodes * 0.08)))
            m = min(m, num_nodes - 1)
            G = nx.barabasi_albert_graph(n=num_nodes, m=m, seed=seed)

        elif topology == TopologyType.SBM_COMMUNITY:
            # Stochastic Block Model: Tạo 2 hoặc 3 buồng vang (Echo Chambers)
            num_communities = kwargs.get("num_communities", 2)
            sizes = [num_nodes // num_communities] * num_communities
            # Phần dư cộng vào cộng đồng cuối
            sizes[-1] += num_nodes - sum(sizes)

            p_in = kwargs.get("p_in", 0.45)   # Liên kết nội cụm cao (Homophily)
            p_out = kwargs.get("p_out", 0.05) # Liên kết liên cụm thấp

            probs = [[p_in if i == j else p_out for j in range(num_communities)] for i in range(num_communities)]
            G = nx.stochastic_block_model(sizes, probs, seed=seed)

        else:
            raise ValueError(f"Topology không hợp lệ: {topology}")

        # Đảm bảo đồ thị là vô hướng và không chứa self-loops
        G = nx.Graph(G)
        G.remove_edges_from(nx.selfloop_edges(G))

        # Nếu đồ thị bị phân mảnh thành nhiều thành phần liên thông, nối các thành phần lại
        if not nx.is_connected(G) and len(G) > 1:
            components = list(nx.connected_components(G))
            for i in range(len(components) - 1):
                u = next(iter(components[i]))
                v = next(iter(components[i + 1]))
                G.add_edge(u, v)

        return G

    @staticmethod
    def compute_topological_metrics(G: nx.Graph) -> Dict[str, Any]:
        """
        Tính toán toàn bộ các thước đo topo mạng phục vụ phân tích NCKH.
        """
        n = G.number_of_nodes()
        m = G.number_of_edges()

        degrees = [d for _, d in G.degree()]
        avg_degree = float(np.mean(degrees)) if degrees else 0.0

        # Degree Centrality
        deg_centrality = nx.degree_centrality(G)
        
        # Betweenness Centrality
        bet_centrality = nx.betweenness_centrality(G)

        # Closeness Centrality
        close_centrality = nx.closeness_centrality(G)

        # Clustering Coefficient
        clustering = nx.clustering(G)
        avg_clustering = float(nx.average_clustering(G)) if n > 0 else 0.0

        # Characteristic Path Length
        if nx.is_connected(G) and n > 1:
            avg_path_length = float(nx.average_shortest_path_length(G))
            diameter = int(nx.diameter(G))
        else:
            avg_path_length = 0.0
            diameter = 0

        # Lưu lại metrics vào từng node
        for node in G.nodes():
            G.nodes[node]["degree_centrality"] = round(deg_centrality.get(node, 0.0), 4)
            G.nodes[node]["betweenness_centrality"] = round(bet_centrality.get(node, 0.0), 4)
            G.nodes[node]["closeness_centrality"] = round(close_centrality.get(node, 0.0), 4)
            G.nodes[node]["clustering"] = round(clustering.get(node, 0.0), 4)

        return {
            "num_nodes": n,
            "num_edges": m,
            "average_degree": round(avg_degree, 3),
            "average_clustering": round(avg_clustering, 4),
            "average_path_length": round(avg_path_length, 4),
            "diameter": diameter,
        }

    @staticmethod
    def export_for_visualization(G: nx.Graph, seed: Optional[int] = 42) -> Dict[str, Any]:
        """
        Xuất đồ thị sang tọa độ và thuộc tính định dạng Vis.js/PyVis cho giao diện web.
        """
        # Tính toán tọa độ 2D bằng thuật toán spring_layout
        pos = nx.spring_layout(G, seed=seed, k=0.35, iterations=50)

        nodes = []
        for node_id in G.nodes():
            data = G.nodes[node_id]
            x, y = pos[node_id]
            nodes.append({
                "id": node_id,
                "label": f"Agent {node_id}",
                "x": float(x * 600),
                "y": float(y * 450),
                "degree": G.degree(node_id),
                "degree_centrality": data.get("degree_centrality", 0.0),
                "betweenness": data.get("betweenness_centrality", 0.0),
                "closeness": data.get("closeness_centrality", 0.0),
                "persona": data.get("persona", "NEUTRAL_OBSERVER"),
                "model_type": data.get("model_type", "OLLAMA"),
                "model_name": data.get("model_name", "llama3:8b"),
                "belief_score": data.get("belief_score", 0.0),
                "state": data.get("state", "UNINFORMED"),
            })

        edges = []
        for idx, (u, v) in enumerate(G.edges()):
            edges.append({
                "id": f"e_{u}_{v}",
                "from": u,
                "to": v,
                "weight": 1.0
            })

        return {
            "nodes": nodes,
            "edges": edges,
        }
