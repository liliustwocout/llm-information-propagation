"""
MAS-Diffusion-Lab: Giao diện Trực quan hóa Mô phỏng Lan truyền Thông tin Đa Tác tử (Streamlit Edition)
ĐỀ TÀI NCKH 2026 - NHÓM 1 (ĐẠI HỌC PHENIKAA)
Phụ trách Module: Lê Phạm Thành Đạt (Mô phỏng NetworkX, Embeddings & Giao diện Streamlit)
Chủ nhiệm Đề tài: Nguyễn Văn An
Giảng viên Hướng dẫn: TS. Phạm Ngọc Hưng
"""

import sys
import os
import asyncio
import time
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Đảm bảo import được module từ thư mục gốc
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st

from src.core.network import NetworkBuilder, TopologyType
from src.core.agent import LLMAgent, AgentPersona, AgentState
from src.core.metrics import MetricsCalculator
from src.core.engine import SimulationEngine
from src.adapters.router import ModelRouter

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="MAS-Diffusion-Lab | NCKH 2026",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo Session State
if "engine" not in st.session_state:
    st.session_state.engine = None
if "hop_history" not in st.session_state:
    st.session_state.hop_history = []
if "trace_history" not in st.session_state:
    st.session_state.trace_history = []
if "is_initialized" not in st.session_state:
    st.session_state.is_initialized = False

# Header & Giới thiệu
st.title("🔬 MAS-Diffusion-Lab: Mô phỏng Lan truyền Thông tin Đa Tác tử LLM")
st.markdown("""
> **Đề tài NCKH 2026:** *Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)*  
> **Đơn vị chủ trì:** Trường Công nghệ Thông tin - Đại học Phenikaa | **GVHD:** TS. Phạm Ngọc Hưng  
> **Sinh viên nghiên cứu:** Nguyễn Văn An (Chủ nhiệm đề tài) & Lê Phạm Thành Đạt (Phụ trách Giao diện & Đồ thị NetworkX)
""")

st.divider()

# Sidebar: Cấu hình Thực nghiệm
with st.sidebar:
    st.header("⚙️ Thiết lập Tham số Thực nghiệm")
    
    topology_choice = st.selectbox(
        "Cấu trúc Topo Mạng lưới (Topology):",
        options=["RING", "ER_RANDOM", "WS_SMALL_WORLD", "BA_SCALE_FREE", "SBM_COMMUNITY"],
        index=0,
        help="RING: Mạng vòng tuần tự (14 ngày đầu); WS: Thế giới nhỏ; BA: Mạng không tỷ lệ (KOL/Hub); SBM: Buồng vang."
    )

    num_nodes = st.slider("Số lượng Tác tử (N):", min_value=3, max_value=30, value=5, step=1)
    
    model_type = st.selectbox(
        "Nền tảng Mô hình AI (Backend):",
        options=["MOCK", "OLLAMA", "DEEPSEEK", "GEMINI", "OPENAI"],
        index=0,
        help="MOCK: Chạy offline không tốn tài nguyên; OLLAMA: Chạy cục bộ GPU RTX 3050 Ti; DEEPSEEK: Cloud chi phí thấp."
    )

    model_name = "llama3:8b"
    if model_type == "OLLAMA":
        model_name = st.selectbox("Mô hình Cục bộ:", ["llama3:8b", "qwen2.5:3b"])
    elif model_type == "DEEPSEEK":
        model_name = "deepseek-chat"
    elif model_type == "GEMINI":
        model_name = "gemini-1.5-flash"
    elif model_type == "OPENAI":
        model_name = "gpt-4o-mini"

    fc_ratio = st.slider("Tỷ lệ Fact-Checker can thiệp (%):", min_value=0.0, max_value=40.0, value=20.0, step=5.0) / 100.0
    fc_placement = st.selectbox("Vị trí đặt Fact-Checker:", ["HUB_DEGREE", "BRIDGE_BETWEENNESS", "RANDOM"])
    
    st.subheader("📝 Thông điệp Hạt giống (M0)")
    sample_msgs = [
        "Tổ chức Y tế Thế giới (WHO) khuyến cáo tiêm chủng đầy đủ để phòng ngừa các biến thể cúm mùa trong năm 2026.",
        "Tin khẩn cấp: Đã tìm ra phương pháp chữa khỏi hoàn toàn mọi bệnh chỉ bằng cách uống nước kiềm mỗi sáng!",
        "Mô hình AI mới có khả năng tự giải toán Olympic và viết mã nguồn không có bất kỳ lỗi nào."
    ]
    selected_sample = st.selectbox("Chọn mẫu thông điệp:", sample_msgs)
    custom_msg = st.text_area("Hoặc tự nhập thông điệp:", value=selected_sample, height=90)
    
    random_seed = st.number_input("Random Seed:", min_value=1, max_value=9999, value=42)

    init_btn = st.button("🚀 Khởi tạo Mô phỏng Mới", use_container_width=True, type="primary")

# Hàm vẽ đồ thị NetworkX bằng Matplotlib
def draw_network_graph(G, agents, informed_nodes):
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    
    # Bố cục layout
    if len(G) <= 5 and nx.is_connected(G):
        pos = nx.circular_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42, k=0.45)

    node_colors = []
    for node in G.nodes():
        agent = agents.get(node)
        if not agent:
            node_colors.append("#94a3b8")
        elif agent.persona == AgentPersona.FACT_CHECKER:
            node_colors.append("#10b981") # Xanh lá: Fact-Checker
        elif node in informed_nodes:
            if agent.belief_score > 0.3:
                node_colors.append("#ef4444") # Đỏ: Tin vào tin đồn
            elif agent.belief_score < -0.3:
                node_colors.append("#06b6d4") # Cyan: Nghi ngờ/Bác bỏ
            else:
                node_colors.append("#f59e0b") # Vàng: Trung lập
        else:
            node_colors.append("#cbd5e1") # Xám nhạt: Chưa nhận tin

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=550, edgecolors="#1e293b", linewidths=1.5, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#64748b", width=1.5, alpha=0.7, ax=ax)
    
    # Nhãn tên node
    labels = {n: f"{n}\n({agents[n].persona.value[:4]})" if n in agents else str(n) for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_family="sans-serif", ax=ax)
    
    ax.axis("off")
    plt.tight_layout()
    return fig

# Khởi tạo mô phỏng khi người dùng bấm nút
if init_btn or (not st.session_state.is_initialized and st.session_state.engine is None):
    router = ModelRouter()
    engine = SimulationEngine(router=router)
    
    init_res = engine.initialize_simulation(
        topology=TopologyType(topology_choice),
        num_nodes=num_nodes,
        seed_message=custom_msg,
        local_model=model_name,
        fact_checker_ratio=fc_ratio,
        fact_checker_placement=fc_placement,
        cloud_ratio=1.0 if model_type in ["DEEPSEEK", "GEMINI", "OPENAI"] else 0.0,
        temperature=0.7,
        max_hops=10,
        seed=random_seed
    )
    
    st.session_state.engine = engine
    st.session_state.hop_history = list(engine.hop_metrics_history)
    st.session_state.trace_history = []
    st.session_state.is_initialized = True
    st.success(f"Khởi tạo thành công mạng lưới {topology_choice} với {num_nodes} tác tử! Tác tử nguồn #{engine.origin_node_id} đã nhận thông điệp ban đầu.")

# Giao diện chính hiển thị
if st.session_state.engine:
    engine = st.session_state.engine
    
    # Layout 2 cột: Cột trái vẽ đồ thị, cột phải hiển thị nút điều khiển & chỉ số
    col1, col2 = st.columns([1.1, 1.0])
    
    with col1:
        st.subheader("🌐 Cấu trúc Đồ thị Mạng lưới Thời gian thực")
        fig = draw_network_graph(engine.graph, engine.agents, engine.informed_nodes)
        st.pyplot(fig)
        
        st.caption("Chú giải màu: 🟩 Fact-Checker | 🟥 Tin tưởng (Infected) | 🟨 Trung lập/Lurker | 🟦 Phản biện | ⬜ Chưa nhận tin")

    with col2:
        st.subheader("⚡ Điều khiển Bước nhảy (Hop Control)")
        
        c_step1, c_step2, c_reset = st.columns([1, 1, 1])
        with c_step1:
            step_btn = st.button("⏭️ Chạy 1 Hop Kế tiếp", use_container_width=True, disabled=engine.is_finished)
        with c_step2:
            auto_btn = st.button("⏩ Chạy Tự động Hết", use_container_width=True, disabled=engine.is_finished)
        with c_reset:
            reset_btn = st.button("🔄 Đặt lại từ đầu", use_container_width=True)

        if reset_btn:
            st.session_state.engine = None
            st.session_state.hop_history = []
            st.session_state.trace_history = []
            st.session_state.is_initialized = False
            st.rerun()

        # Thực thi 1 hop
        if step_btn and not engine.is_finished:
            with st.spinner(f"Đang thực thi Bước nhảy (Hop) #{engine.current_hop + 1}..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                step_res = loop.run_until_complete(engine.step())
                loop.close()
                st.session_state.hop_history = list(engine.hop_metrics_history)
                st.session_state.trace_history = list(engine.all_traces)
                st.rerun()

        # Thực thi tự động
        if auto_btn and not engine.is_finished:
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for h in range(1, 11):
                if engine.is_finished:
                    break
                status_text.text(f"Đang chạy Hop #{engine.current_hop + 1}...")
                res = loop.run_until_complete(engine.step())
                progress_bar.progress(min(1.0, h / 10.0))
                time.sleep(0.3)
                if res.get("finished"):
                    break
            loop.close()
            st.session_state.hop_history = list(engine.hop_metrics_history)
            st.session_state.trace_history = list(engine.all_traces)
            st.rerun()

        # Thống kê nhanh các chỉ số
        st.markdown("#### 📊 Thống kê Động học Tổng thể")
        last_metrics = engine.hop_metrics_history[-1] if engine.hop_metrics_history else {}
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Bước nhảy hiện tại", f"Hop #{engine.current_hop}")
        m1.metric("Độ phủ thông tin R(t)", f"{last_metrics.get('penetration_rate', 0.0)}%")
        
        m2.metric("Số nút đã nhận tin", f"{len(engine.informed_nodes)} / {len(engine.agents)}")
        m2.metric("Độ trôi dạt ngữ nghĩa", f"{last_metrics.get('average_semantic_drift', 0.0)}")
        
        m3.metric("Tin trong hàng đợi", f"{len(engine.message_queue)}")
        m3.metric("Chỉ số phân cực (PI)", f"{last_metrics.get('polarization_index', 0.0)}")

    st.divider()

    # Vùng biểu đồ suy giảm ngữ nghĩa và động học
    st.subheader("📈 Đồ thị Động học & Biến dạng Ngữ nghĩa qua các Bước nhảy")
    if len(st.session_state.hop_history) > 1:
        df_metrics = pd.DataFrame(st.session_state.hop_history)
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("**Độ trôi dạt ngữ nghĩa (Semantic Drift Distance) qua từng Hop**")
            st.line_chart(df_metrics.set_index("hop")[["average_semantic_drift"]])
        with c_chart2:
            st.markdown("**Độ phủ lan truyền R(t) % trên mạng lưới**")
            st.line_chart(df_metrics.set_index("hop")[["penetration_rate"]])
    else:
        st.info("Bấm **'Chạy 1 Hop Kế tiếp'** để bắt đầu quan sát các đồ thị suy giảm ngữ nghĩa.")

    # Vùng nhật ký truyền tin chi tiết
    st.subheader("💬 Nhật ký Trao đổi Thông tin giữa các Tác tử")
    if st.session_state.trace_history:
        traces_to_show = []
        for t in reversed(st.session_state.trace_history):
            traces_to_show.append({
                "Hop": t.get("hop"),
                "Người gửi": f"Agent #{t.get('sender_id')}",
                "Người nhận": f"Agent #{t.get('agent_id')}",
                "Persona": t.get("persona"),
                "Quyết định": t.get("decision"),
                "Niềm tin": t.get("belief_score"),
                "Độ trôi dạt": t.get("drift_distance"),
                "Tin nhận được": t.get("incoming_message"),
                "Tin gửi đi": t.get("outgoing_message")
            })
        st.dataframe(pd.DataFrame(traces_to_show), use_container_width=True, height=280)
    else:
        st.text("Chưa có thông điệp nào được truyền tiếp.")
