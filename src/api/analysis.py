"""
Module Phân tích & Đánh giá Thực nghiệm theo từng Hop.

Gồm 2 tầng:
  1. Thống kê định lượng (tính toán xác định bằng Python, không dùng LLM).
  2. Báo cáo nhận định khoa học (LLM-as-a-Judge): Gemini Cloud hoặc Ollama cục bộ.
"""
import os
import json
from collections import Counter, defaultdict
from typing import Dict, Any, List, Optional

import httpx

DECISIONS = ["FORWARD", "COUNTER", "IGNORE"]


def _safe_round(val: float, nd: int = 4) -> float:
    try:
        return round(float(val), nd)
    except Exception:
        return 0.0


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def _trace_stats(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Thống kê mô tả cho một tập vết truyền tin (traces)."""
    decisions = Counter(t.get("decision", "IGNORE") for t in traces)
    drifts = [float(t.get("drift_distance", 0.0)) for t in traces if t.get("outgoing_message")]
    beliefs = [float(t.get("belief_score", 0.0)) for t in traces]
    total = len(traces)

    persona_stats: Dict[str, Dict[str, Any]] = {}
    by_persona = defaultdict(list)
    for t in traces:
        by_persona[t.get("persona", "UNKNOWN")].append(t)
    for persona, items in by_persona.items():
        p_dec = Counter(i.get("decision", "IGNORE") for i in items)
        p_drifts = [float(i.get("drift_distance", 0.0)) for i in items if i.get("outgoing_message")]
        persona_stats[persona] = {
            "count": len(items),
            "decisions": {d: p_dec.get(d, 0) for d in DECISIONS},
            "avg_drift": _safe_round(_mean(p_drifts)),
            "avg_belief": _safe_round(_mean([float(i.get("belief_score", 0.0)) for i in items]), 3),
        }

    top_drift = sorted(
        [t for t in traces if t.get("outgoing_message")],
        key=lambda t: float(t.get("drift_distance", 0.0)),
        reverse=True,
    )[:5]

    return {
        "total_interactions": total,
        "decisions": {d: decisions.get(d, 0) for d in DECISIONS},
        "decision_ratio": {d: _safe_round(decisions.get(d, 0) / total * 100, 1) if total else 0.0 for d in DECISIONS},
        "drift_mean": _safe_round(_mean(drifts)),
        "drift_std": _safe_round(_std(drifts)),
        "drift_max": _safe_round(max(drifts) if drifts else 0.0),
        "drift_min": _safe_round(min(drifts) if drifts else 0.0),
        "belief_mean": _safe_round(_mean(beliefs), 3),
        "belief_std": _safe_round(_std(beliefs), 3),
        "unique_agents": len({t.get("agent_id") for t in traces}),
        "persona_stats": persona_stats,
        "top_drift_agents": [
            {
                "agent_id": t.get("agent_id"),
                "persona": t.get("persona"),
                "hop": t.get("hop"),
                "drift_distance": _safe_round(t.get("drift_distance", 0.0)),
                "decision": t.get("decision"),
            }
            for t in top_drift
        ],
    }


def build_analysis_payload(engine) -> Dict[str, Any]:
    """Tổng hợp toàn bộ dữ liệu + thống kê định lượng cho trang phân tích."""
    config = dict(engine.config or {})
    topo = config.get("topology")
    if topo is not None and hasattr(topo, "value"):
        config["topology"] = topo.value

    traces = list(engine.all_traces or [])
    hop_metrics = list(engine.hop_metrics_history or [])

    traces_by_hop = defaultdict(list)
    for t in traces:
        traces_by_hop[int(t.get("hop", 0))].append(t)

    per_hop = []
    for hm in hop_metrics:
        h = int(hm.get("hop", 0))
        per_hop.append({
            "hop": h,
            "metrics": hm,
            "stats": _trace_stats(traces_by_hop.get(h, [])),
        })

    agents = []
    if engine.graph is not None:
        for aid, agent in engine.agents.items():
            agents.append({
                "id": aid,
                "persona": agent.persona.value,
                "model_type": agent.model_type,
                "model_name": agent.model_name,
                "belief_score": _safe_round(agent.belief_score, 3),
                "state": agent.state.value,
                "degree": int(engine.graph.degree(aid)),
                "is_seed": aid == engine.seed_node_id,
            })

    return {
        "simulation_id": engine.simulation_id,
        "config": config,
        "seed_node_id": engine.seed_node_id,
        "origin_message": engine.origin_message,
        "current_hop": engine.current_hop,
        "max_hops": engine.max_hops,
        "is_finished": engine.is_finished,
        "is_running": engine.is_running,
        "hop_metrics": hop_metrics,
        "per_hop": per_hop,
        "overall": _trace_stats(traces),
        "agents": agents,
        "traces": traces,
    }


# ==================== BÁO CÁO NHẬN ĐỊNH KHOA HỌC ====================

SYSTEM_PROMPT = (
    "Bạn là chuyên gia nghiên cứu về Khoa học Xã hội Tính toán, Hệ đa tác tử (MAS) và "
    "Mô hình Ngôn ngữ Lớn (LLMs). Nhiệm vụ: viết báo cáo nhận định khoa học khách quan, "
    "bằng tiếng Việt, dựa HOÀN TOÀN trên số liệu thực nghiệm được cung cấp. "
    "Tuyệt đối không bịa thêm số liệu. Nếu dữ liệu không đủ để kết luận, hãy nói rõ hạn chế. "
    "Không dùng emoji. Trình bày bằng Markdown với các tiêu đề cấp ##."
)


def _truncate(text: Optional[str], n: int) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= n else text[:n] + "..."


def build_report_prompt(payload: Dict[str, Any], hop: Optional[int], compact: bool) -> str:
    cfg = payload["config"]
    msg_len = 160 if compact else 400
    max_traces = 40 if compact else 400

    if hop is not None:
        scope = f"PHẠM VI PHÂN TÍCH: chỉ Hop {hop} (có tham chiếu bối cảnh các hop trước)."
        traces = [t for t in payload["traces"] if int(t.get("hop", 0)) == hop]
    else:
        scope = f"PHẠM VI PHÂN TÍCH: toàn bộ chu trình ({payload['current_hop']} hop đã chạy)."
        traces = payload["traces"]

    traces = traces[:max_traces]

    lines = [
        scope,
        "",
        "## CẤU HÌNH THỰC NGHIỆM",
        f"- Topology: {cfg.get('topology')}; N = {cfg.get('num_nodes')}; Max hops = {cfg.get('max_hops')}",
        f"- Fact-Checker: {float(cfg.get('fact_checker_ratio', 0)) * 100:.0f}% đặt tại {cfg.get('fact_checker_placement')}",
        f"- Mô hình cục bộ: {cfg.get('local_model')}; Tỷ lệ Cloud: {float(cfg.get('cloud_ratio', 0)) * 100:.0f}%; Nhiệt độ: {cfg.get('temperature')}; Seed: {cfg.get('seed')}",
        f"- Thông điệp gốc M0: \"{payload['origin_message']}\"",
        "",
        "## CHỈ SỐ VĨ MÔ THEO HOP",
        "hop | truyền | kích hoạt mới | R(t)% | PI | Drift TB | R_t | còn hàng đợi | FORWARD | COUNTER | IGNORE | Drift max",
    ]
    for ph in payload["per_hop"]:
        m, s = ph["metrics"], ph["stats"]
        lines.append(
            f"{m['hop']} | {m['active_transmissions']} | {len(m.get('newly_activated_nodes', []))} | "
            f"{m['penetration_rate']} | {m['polarization_index']} | {m['average_semantic_drift']} | "
            f"{m['reproduction_rate']} | {m['remaining_queue_size']} | {s['decisions']['FORWARD']} | "
            f"{s['decisions']['COUNTER']} | {s['decisions']['IGNORE']} | {s['drift_max']}"
        )

    scope_stats = next((p["stats"] for p in payload["per_hop"] if p["hop"] == hop), None) if hop is not None else payload["overall"]
    if scope_stats:
        lines += ["", "## THỐNG KÊ THEO PERSONA (trong phạm vi phân tích)"]
        for persona, ps in scope_stats["persona_stats"].items():
            lines.append(
                f"- {persona}: {ps['count']} lượt; F/C/I = {ps['decisions']['FORWARD']}/"
                f"{ps['decisions']['COUNTER']}/{ps['decisions']['IGNORE']}; drift TB {ps['avg_drift']}; niềm tin TB {ps['avg_belief']}"
            )

    lines += ["", f"## VẾT TRUYỀN TIN CHI TIẾT ({len(traces)} bản ghi)"]
    for t in traces:
        lines.append(
            f"[Hop {t.get('hop')}] #{t.get('sender_id')} -> #{t.get('agent_id')} ({t.get('persona')}, {t.get('model_name')}) "
            f"| {t.get('decision')} | b={t.get('belief_score')} | drift={_safe_round(t.get('drift_distance', 0), 3)}\n"
            f"  Lập luận: {_truncate(t.get('reasoning'), msg_len)}\n"
            f"  Phát ngôn: {_truncate(t.get('outgoing_message'), msg_len) or '(im lặng)'}"
        )

    lines += [
        "",
        "## YÊU CẦU BÁO CÁO",
        "Viết báo cáo gồm các mục sau (tiêu đề ##):",
        "1. Tóm tắt kết quả chính (3-5 gạch đầu dòng có số liệu cụ thể).",
        "2. Động học lan truyền: tốc độ khuếch tán R(t), hệ số R_t, điểm bão hòa; liên hệ với đặc trưng topology.",
        "3. Biến dạng ngữ nghĩa: xu hướng Drift qua các hop, tác tử/persona gây biến dạng nhiều nhất, ví dụ cụ thể từ phát ngôn.",
        "4. Phân cực niềm tin và hành vi quyết định: phân tích PI, tỷ lệ FORWARD/COUNTER/IGNORE theo persona.",
        "5. Hiệu quả can thiệp của Fact-Checker (nếu có trong dữ liệu).",
        "6. Hạn chế của lượt chạy và khuyến nghị cho các lần thực nghiệm tiếp theo (tham số nhiệt độ, tỷ lệ/vị trí Fact-Checker, số lần lặp K).",
    ]
    return "\n".join(lines)


async def _call_gemini(prompt: str, api_key: str, model: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 8192},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(url, json=body)
    if res.status_code != 200:
        raise RuntimeError(f"Gemini API lỗi {res.status_code}: {res.text[:300]}")
    data = res.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini không trả về nội dung: {json.dumps(data)[:300]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not text.strip():
        raise RuntimeError("Gemini trả về nội dung rỗng.")
    return text


async def _call_ollama(prompt: str, base_url: str, model: str) -> str:
    body = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048, "num_ctx": 8192},
    }
    async with httpx.AsyncClient(timeout=600.0) as client:
        res = await client.post(f"{base_url.rstrip('/')}/api/generate", json=body)
    if res.status_code != 200:
        raise RuntimeError(f"Ollama lỗi {res.status_code}: {res.text[:300]}")
    text = res.json().get("response", "")
    if not text.strip():
        raise RuntimeError("Ollama trả về nội dung rỗng.")
    return text


async def generate_report(engine, router, provider: str, hop: Optional[int], model: Optional[str] = None) -> Dict[str, Any]:
    payload = build_analysis_payload(engine)
    if not payload["hop_metrics"]:
        raise ValueError("Chưa có hop nào được chạy để phân tích.")

    provider = (provider or "gemini").lower()
    if provider == "gemini":
        api_key = router.cloud.gemini_key
        if not api_key:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY trong file .env.")
        model_used = model or router.cloud.gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        prompt = build_report_prompt(payload, hop, compact=False)
        text = await _call_gemini(prompt, api_key, model_used)
    elif provider == "ollama":
        model_used = model or payload["config"].get("local_model") or router.ollama.default_model
        prompt = build_report_prompt(payload, hop, compact=True)
        text = await _call_ollama(prompt, router.ollama.base_url, model_used)
    else:
        raise ValueError(f"Provider không hợp lệ: {provider}")

    return {
        "simulation_id": payload["simulation_id"],
        "provider": provider,
        "model": model_used,
        "scope_hop": hop,
        "hops_analyzed": payload["current_hop"],
        "report_markdown": text,
    }
