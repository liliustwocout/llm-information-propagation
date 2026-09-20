import asyncio
import time
from typing import Dict, Any, List, Set, Optional
import networkx as nx

from src.core.network import NetworkBuilder, TopologyType
from src.core.agent import LLMAgent, AgentPersona, AgentState
from src.core.metrics import MetricsCalculator
from src.adapters.router import ModelRouter

class SimulationEngine:
    """
    Lõi điều phối quá trình mô phỏng lan truyền thông tin trong mạng lưới đa tác tử (MAS Diffusion Engine).
    Thực thi theo chu kỳ bước nhảy (hop-by-hop), quản lý hàng đợi thông điệp,
    đo lường biến dạng ngữ nghĩa và phân cực xã hội thời gian thực.
    """

    def __init__(self, router: Optional[ModelRouter] = None):
        self.router = router or ModelRouter()
        self.graph: Optional[nx.Graph] = None
        self.agents: Dict[int, LLMAgent] = {}
        self.config: Dict[str, Any] = {}
        
        # Trạng thái mô phỏng
        self.simulation_id: str = f"SIM_{int(time.time())}"
        self.current_hop: int = 0
        self.max_hops: int = 10
        self.is_running: bool = False
        self.is_finished: bool = False

        # Dữ liệu nguồn và hạt giống
        self.origin_message: str = ""
        self.origin_embedding: List[float] = []
        self.seed_node_id: int = 0

        # Lịch sử và cây lan truyền (Cascade Tracking)
        self.message_queue: List[Dict[str, Any]] = [] # Các tin nhắn đang chuyển giao
        self.informed_nodes: Set[int] = set()
        self.hop_metrics_history: List[Dict[str, Any]] = []
        self.all_traces: List[Dict[str, Any]] = []
        self.progress_callback: Optional[Any] = None

    def initialize_simulation(
        self,
        topology: TopologyType = TopologyType.BA_SCALE_FREE,
        num_nodes: int = 30,
        seed_message: str = "Tổ chức Y tế khuyến nghị người dân nên bổ sung đầy đủ nước và vận động nhẹ mỗi ngày.",
        seed_node_id: Optional[int] = None,
        local_model: str = "qwen2.5:3b",
        fact_checker_ratio: float = 0.1,
        fact_checker_placement: str = "HUB_DEGREE", # "RANDOM", "HUB_DEGREE", "BRIDGE_BETWEENNESS"
        cloud_ratio: float = 0.0,
        temperature: float = 0.7,
        max_hops: int = 10,
        seed: int = 42,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Khởi tạo toàn diện môi trường mô phỏng: sinh đồ thị, gán Persona và tiêm thông điệp gốc.
        """
        self.simulation_id = f"SIM_{int(time.time())}"
        self.current_hop = 0
        self.max_hops = max_hops
        self.is_running = False
        self.is_finished = False
        self.origin_message = seed_message
        self.informed_nodes = set()
        self.hop_metrics_history = []
        self.all_traces = []
        self.message_queue = []

        self.config = {
            "simulation_id": self.simulation_id,
            "topology": topology,
            "num_nodes": num_nodes,
            "seed_message": seed_message,
            "local_model": local_model,
            "fact_checker_ratio": fact_checker_ratio,
            "fact_checker_placement": fact_checker_placement,
            "cloud_ratio": cloud_ratio,
            "temperature": temperature,
            "max_hops": max_hops,
            "seed": seed,
            **kwargs
        }

        # 1. Sinh đồ thị mạng phức hợp
        self.graph = NetworkBuilder.generate_graph(
            topology=topology,
            num_nodes=num_nodes,
            seed=seed,
            **kwargs
        )
        topo_metrics = NetworkBuilder.compute_topological_metrics(self.graph)

        # 2. Xác định các nút Fact-Checker theo chiến lược
        num_fact_checkers = int(num_nodes * fact_checker_ratio)
        fc_nodes = self._select_fact_checkers(num_fact_checkers, fact_checker_placement)

        # 3. Phân bổ Persona và Model Type cho từng Agent
        self.agents = {}
        for node_id in self.graph.nodes():
            # Xác định Persona
            if node_id in fc_nodes:
                persona = AgentPersona.FACT_CHECKER
            else:
                # Phân bổ các Persona còn lại theo tỷ lệ tự nhiên
                rand_val = (hash(f"{seed}_{node_id}") % 100) / 100.0
                if rand_val < 0.35:
                    persona = AgentPersona.GULLIBLE_SPREADER
                elif rand_val < 0.55:
                    persona = AgentPersona.NEUTRAL_OBSERVER
                elif rand_val < 0.75:
                    persona = AgentPersona.DOGMATIC_PARTISAN
                elif rand_val < 0.90:
                    persona = AgentPersona.OPINION_LEADER
                else:
                    persona = AgentPersona.MALICIOUS_SPREADER

            # Xác định Model Type (Ollama vs Cloud)
            is_cloud = (hash(f"cloud_{seed}_{node_id}") % 100) < (cloud_ratio * 100)
            model_type = "CLOUD" if is_cloud else "OLLAMA"
            model_name = "gpt-4o-mini" if is_cloud else local_model

            agent = LLMAgent(
                agent_id=node_id,
                persona=persona,
                model_type=model_type,
                model_name=model_name,
                initial_belief=0.0
            )
            self.agents[node_id] = agent

            # Cập nhật thông tin vào đồ thị NetworkX
            self.graph.nodes[node_id]["persona"] = persona.value
            self.graph.nodes[node_id]["model_type"] = model_type
            self.graph.nodes[node_id]["model_name"] = model_name
            self.graph.nodes[node_id]["belief_score"] = 0.0
            self.graph.nodes[node_id]["state"] = AgentState.UNINFORMED.value

        # 4. Xác định nút hạt giống (Seed Node)
        if seed_node_id is not None and seed_node_id in self.agents:
            self.seed_node_id = seed_node_id
        else:
            # Chọn nút có bậc liên kết cao nhất hoặc nút 0
            degrees = dict(self.graph.degree())
            self.seed_node_id = max(degrees, key=degrees.get) if degrees else 0

        # Kích hoạt nút nguồn
        seed_agent = self.agents[self.seed_node_id]
        seed_agent.state = AgentState.INFECTED_BELIEVER
        seed_agent.belief_score = 1.0
        self.graph.nodes[self.seed_node_id]["state"] = seed_agent.state.value
        self.graph.nodes[self.seed_node_id]["belief_score"] = 1.0
        self.informed_nodes.add(self.seed_node_id)

        # 5. Đưa thông điệp hạt giống tới các láng giềng của nút nguồn ở Hop 1
        neighbors = list(self.graph.neighbors(self.seed_node_id))
        for neighbor in neighbors:
            self.message_queue.append({
                "sender_id": self.seed_node_id,
                "receiver_id": neighbor,
                "message": self.origin_message,
                "hop": 1
            })

        # Tính embedding của thông điệp nguồn
        self.origin_embedding = MetricsCalculator.compute_lightweight_embedding(self.origin_message)

        # Trả về trạng thái ban đầu của đồ thị
        graph_data = NetworkBuilder.export_for_visualization(self.graph, seed=seed)
        return {
            "simulation_id": self.simulation_id,
            "topology_metrics": topo_metrics,
            "graph_data": graph_data,
            "seed_node_id": self.seed_node_id,
            "seed_message": self.origin_message,
            "total_nodes": len(self.agents),
            "pending_messages": len(self.message_queue)
        }

    def _select_fact_checkers(self, count: int, placement: str) -> Set[int]:
        """
        Lựa chọn các nút làm Fact-Checker dựa trên cấu trúc đồ thị.
        """
        if count <= 0:
            return set()
        
        nodes = list(self.graph.nodes())
        if placement == "HUB_DEGREE":
            # Xếp hạng theo bậc liên kết (Degree Centrality)
            sorted_nodes = sorted(nodes, key=lambda n: self.graph.degree(n), reverse=True)
            return set(sorted_nodes[:count])
        elif placement == "BRIDGE_BETWEENNESS":
            # Xếp hạng theo độ trung gian (Betweenness Centrality)
            bet = nx.betweenness_centrality(self.graph)
            sorted_nodes = sorted(nodes, key=lambda n: bet.get(n, 0.0), reverse=True)
            return set(sorted_nodes[:count])
        else: # "RANDOM"
            return set(nodes[:count])

    async def step(self) -> Dict[str, Any]:
        """
        Thực thi 1 bước nhảy (1 Hop) của mô phỏng.
        Xử lý toàn bộ các thông điệp đang chờ trong hàng đợi.
        """
        if self.is_finished or not self.message_queue:
            self.is_finished = True
            return {"finished": True, "message": "Mô phỏng đã hoàn tất hoặc không còn thông điệp lan truyền."}

        hop_start_time = time.time()

        # Đảm bảo embedding nguồn đồng nhất không gian vector với router (nomic-embed-text)
        if not self.origin_embedding or len(self.origin_embedding) == 128:
            try:
                real_embed = await self.router.embed_text(self.origin_message, preferred_type="OLLAMA")
                if real_embed and len(real_embed) > 0:
                    self.origin_embedding = real_embed
            except Exception:
                pass

        self.current_hop += 1
        current_messages = list(self.message_queue)
        self.message_queue = [] # Reset hàng đợi cho bước tiếp theo

        # 1. Phát sự kiện bắt đầu Hop
        if self.progress_callback:
            try:
                await self.progress_callback("HOP_STARTED", {
                    "hop": self.current_hop,
                    "total_messages": len(current_messages),
                    "start_time": hop_start_time
                })
            except Exception:
                pass

        new_transmissions: List[Dict[str, Any]] = []
        hop_drift_scores: List[float] = []
        activated_nodes_this_hop: Set[int] = set()
        agent_latencies: List[float] = []

        # Xử lý tuần tự từng tin nhắn để đảm bảo GPU ổn định và truyền phát tiến độ thời gian thực
        for idx, item in enumerate(current_messages):
            receiver_id = item["receiver_id"]
            agent = self.agents.get(receiver_id)
            if not agent:
                continue

            # Thông báo bắt đầu xử lý tác tử
            if self.progress_callback:
                try:
                    await self.progress_callback("AGENT_PROCESSING_START", {
                        "hop": self.current_hop,
                        "message_index": idx + 1,
                        "total_messages": len(current_messages),
                        "sender_id": item["sender_id"],
                        "agent_id": receiver_id,
                        "persona": agent.persona.value,
                        "model_name": agent.model_name,
                        "model_type": agent.model_type,
                        "incoming_message": item["message"],
                        "elapsed_seconds": round(time.time() - hop_start_time, 2)
                    })
                except Exception:
                    pass

            t0 = time.time()
            try:
                res = await self._process_single_message(agent, item)
                latency = round(time.time() - t0, 2)
                res["inference_duration"] = latency
                agent_latencies.append(latency)
            except Exception as e:
                print(f"Lỗi suy luận tác tử #{receiver_id}: {e}")
                continue

            node_id = res["agent_id"]
            decision = res["decision"]
            outgoing_msg = res["outgoing_message"]
            drift = res["drift_distance"]

            hop_drift_scores.append(drift)
            self.all_traces.append(res)

            if decision in ["FORWARD", "COUNTER"] and outgoing_msg:
                activated_nodes_this_hop.add(node_id)
                self.informed_nodes.add(node_id)

                # Tìm các láng giềng chưa nhận tin ở hop này để lan truyền tiếp
                neighbors = list(self.graph.neighbors(node_id))
                for nbr in neighbors:
                    # Tránh gửi ngược lại người gửi trực tiếp
                    if nbr != res["sender_id"]:
                        new_transmissions.append({
                            "sender_id": node_id,
                            "receiver_id": nbr,
                            "message": outgoing_msg,
                            "hop": self.current_hop + 1
                        })

            # Thông báo hoàn tất xử lý tác tử
            if self.progress_callback:
                try:
                    elapsed = round(time.time() - hop_start_time, 2)
                    progress_pct = round((idx + 1) / len(current_messages) * 100, 1)
                    avg_lat = (elapsed / (idx + 1)) if (idx + 1) > 0 else latency
                    rem_count = len(current_messages) - (idx + 1)
                    eta = round(rem_count * avg_lat, 1)

                    await self.progress_callback("AGENT_PROCESSING_END", {
                        "hop": self.current_hop,
                        "message_index": idx + 1,
                        "total_messages": len(current_messages),
                        "progress_percent": progress_pct,
                        "agent_id": agent.id,
                        "persona": agent.persona.value,
                        "model_name": agent.model_name,
                        "decision": decision,
                        "belief_score": res["belief_score"],
                        "drift_distance": drift,
                        "outgoing_message": outgoing_msg,
                        "reasoning": res.get("reasoning", ""),
                        "inference_duration": latency,
                        "elapsed_seconds": elapsed,
                        "eta_seconds": eta
                    })
                except Exception:
                    pass

        # Cập nhật hàng đợi cho hop tiếp theo (loại bỏ trùng lặp receiver trong cùng 1 vòng)
        unique_next_queue = {}
        for trans in new_transmissions:
            pair = (trans["sender_id"], trans["receiver_id"])
            if pair not in unique_next_queue:
                unique_next_queue[pair] = trans
        self.message_queue = list(unique_next_queue.values())

        # Tính toán các chỉ số thống kê của hop này
        total_nodes = len(self.agents)
        penetration = MetricsCalculator.compute_penetration_rate(total_nodes, len(self.informed_nodes))
        
        all_beliefs = [a.belief_score for a in self.agents.values()]
        polarization = MetricsCalculator.compute_polarization_index(all_beliefs)

        avg_drift = float(sum(hop_drift_scores) / len(hop_drift_scores)) if hop_drift_scores else 0.0
        
        # Hệ số lây nhiễm hiệu dụng R_t
        active_previous = len(current_messages)
        reproduction_rate = MetricsCalculator.compute_effective_reproduction_rate(
            len(activated_nodes_this_hop), active_previous
        )

        hop_duration = round(time.time() - hop_start_time, 2)
        avg_agent_latency = round(sum(agent_latencies) / len(agent_latencies), 2) if agent_latencies else 0.0

        hop_summary = {
            "hop": self.current_hop,
            "active_transmissions": len(current_messages),
            "newly_activated_nodes": list(activated_nodes_this_hop),
            "penetration_rate": penetration,
            "polarization_index": polarization,
            "average_semantic_drift": round(avg_drift, 4),
            "reproduction_rate": reproduction_rate,
            "remaining_queue_size": len(self.message_queue),
            "informed_total": len(self.informed_nodes),
            "hop_duration_seconds": hop_duration,
            "avg_agent_duration": avg_agent_latency
        }
        self.hop_metrics_history.append(hop_summary)

        # Điều kiện dừng
        if self.current_hop >= self.max_hops or not self.message_queue:
            self.is_finished = True

        # Trả về kết quả cập nhật đồ thị và biểu đồ
        return {
            "finished": self.is_finished,
            "hop_summary": hop_summary,
            "traces": [t for t in self.all_traces if t.get("hop") == self.current_hop],
            "updated_nodes": [
                {
                    "id": a.id,
                    "belief_score": a.belief_score,
                    "state": a.state.value,
                    "persona": a.persona.value
                }
                for a in self.agents.values() if a.id in activated_nodes_this_hop
            ]
        }

    async def _process_single_message(self, agent: LLMAgent, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý suy luận của một tác tử đối với một thông điệp đến.
        """
        sender_id = item["sender_id"]
        incoming_msg = item["message"]
        hop = item["hop"]

        # 1. Tạo prompt nhận thức theo Persona
        prompt = agent.build_decision_prompt(
            incoming_message=incoming_msg,
            sender_id=sender_id,
            hop_count=hop
        )

        # 2. Gọi Model qua Router (tự động điều hướng Ollama, Cloud, hoặc Mock)
        raw_output = await self.router.generate_for_agent(
            model_type=agent.model_type,
            model_name=agent.model_name,
            prompt=prompt,
            temperature=self.config.get("temperature", 0.7),
            seed=self.config.get("seed", 42) + agent.id + hop
        )

        # 3. Phân tích kết quả có cấu trúc
        decision_data = agent.parse_llm_response(raw_output)
        decision = decision_data["decision"]
        new_belief = decision_data["updated_belief"]
        outgoing_msg = decision_data["outgoing_message"]
        reasoning = decision_data["reasoning"]

        # 4. Cập nhật trạng thái nhận thức của Agent và Node đồ thị
        agent.update_state(decision, new_belief)
        self.graph.nodes[agent.id]["belief_score"] = new_belief
        self.graph.nodes[agent.id]["state"] = agent.state.value

        # 5. Đo lường khoảng cách ngữ nghĩa (Semantic Drift) so với thông điệp nguồn
        if outgoing_msg:
            current_embed = await self.router.embed_text(outgoing_msg, preferred_type=agent.model_type)
            if len(self.origin_embedding) != len(current_embed):
                orig_hash = MetricsCalculator.compute_lightweight_embedding(self.origin_message)
                curr_hash = MetricsCalculator.compute_lightweight_embedding(outgoing_msg)
                drift_distance = MetricsCalculator.semantic_drift_distance(orig_hash, curr_hash)
            else:
                drift_distance = MetricsCalculator.semantic_drift_distance(self.origin_embedding, current_embed)
        else:
            drift_distance = 0.0

        return {
            "simulation_id": self.simulation_id,
            "hop": hop,
            "sender_id": sender_id,
            "agent_id": agent.id,
            "persona": agent.persona.value,
            "model_type": agent.model_type,
            "model_name": agent.model_name,
            "incoming_message": incoming_msg,
            "outgoing_message": outgoing_msg,
            "decision": decision,
            "reasoning": reasoning,
            "belief_score": new_belief,
            "drift_distance": drift_distance,
            "timestamp": time.time()
        }
