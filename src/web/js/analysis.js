// MAS-Diffusion-Lab — Trang Phân tích & Đánh giá Thực nghiệm theo từng Hop

document.addEventListener("DOMContentLoaded", () => {
  // ==================== STATE ====================
  let data = null;
  let scope = null; // null = toàn bộ chu trình, số = Hop cụ thể
  let lastSimId = null;
  let knownHops = new Set();
  const reportCache = {};
  let currentReport = null;
  let charts = {};
  let ws = null;
  let refreshTimer = null;
  let traceFilter = { search: "", decision: "all", sort: "order" };

  const $ = (id) => document.getElementById(id);
  const COLORS = {
    cyan: "#00f2fe", amber: "#f59e0b", rose: "#f43f5e", emerald: "#10b981",
    violet: "#818cf8", slate: "#64748b", blue: "#38bdf8"
  };
  const PERSONA_LABELS = {
    GULLIBLE_SPREADER: "Dễ tin & lan truyền",
    NEUTRAL_OBSERVER: "Quan sát trung lập",
    DOGMATIC_PARTISAN: "Bảo thủ phe phái",
    OPINION_LEADER: "Thủ lĩnh dư luận",
    MALICIOUS_SPREADER: "Lan truyền ác ý",
    FACT_CHECKER: "Kiểm chứng sự thật"
  };
  const TOPO_LABELS = {
    BA_SCALE_FREE: "Barabási–Albert (BA)",
    WS_SMALL_WORLD: "Watts–Strogatz (WS)",
    ER_RANDOM: "Erdős–Rényi (ER)",
    SBM_COMMUNITY: "Stochastic Block (SBM)",
    RING: "Mạng vòng (Ring)"
  };
  const PLACEMENT_LABELS = { HUB_DEGREE: "Nút trục (Hubs)", BRIDGE_BETWEENNESS: "Cầu nối (Bridges)", RANDOM: "Ngẫu nhiên" };

  // ==================== UTILS ====================
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (v, d = 3) => (typeof v === "number" && isFinite(v) ? v.toFixed(d) : (v ?? "--"));
  const signed = (v, d = 2) => (typeof v === "number" ? `${v >= 0 ? "+" : ""}${v.toFixed(d)}` : "--");
  const driftColor = (d) => (d < 0.2 ? COLORS.emerald : d < 0.4 ? COLORS.amber : COLORS.rose);
  const personaLabel = (p) => PERSONA_LABELS[p] || (p || "").replace(/_/g, " ");

  function deltaHtml(curr, prev, d = 3, invert = false) {
    if (prev === undefined || prev === null || typeof curr !== "number") return "";
    const diff = curr - prev;
    if (Math.abs(diff) < Math.pow(10, -d)) return `<span class="an-delta flat">±0</span>`;
    const good = invert ? diff < 0 : diff > 0;
    const arrow = diff > 0 ? "▲" : "▼";
    return `<span class="an-delta ${good ? "up" : "down"}">${arrow} ${Math.abs(diff).toFixed(d)}</span>`;
  }

  function scopeLabel(s = scope) {
    return s === null ? "Toàn bộ chu trình" : `Hop ${s}`;
  }

  function scopeTraces() {
    if (!data) return [];
    const all = data.traces.map((t, i) => ({ ...t, _idx: i }));
    return scope === null ? all : all.filter(t => Number(t.hop) === scope);
  }

  function scopeStats() {
    if (!data) return null;
    if (scope === null) return data.overall;
    const ph = data.per_hop.find(p => p.hop === scope);
    return ph ? ph.stats : null;
  }

  function download(content, filename, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // ==================== DATA LOADING ====================
  async function load() {
    try {
      const res = await fetch("/api/analysis/data", { cache: "no-store" });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Không tải được dữ liệu");

      if (!body.hop_metrics || body.hop_metrics.length === 0) {
        showEmpty("Mô phỏng đã được khởi tạo nhưng chưa chạy Hop nào. Hãy chạy ít nhất 1 Hop rồi quay lại đây.");
        data = body;
        updateHeader();
        return;
      }

      if (lastSimId && body.simulation_id !== lastSimId) {
        // Phiên mô phỏng mới: reset phạm vi & bộ nhớ báo cáo
        scope = null;
        knownHops = new Set();
        Object.keys(reportCache).forEach(k => delete reportCache[k]);
        resetReportView();
      }
      lastSimId = body.simulation_id;
      data = body;

      if (scope !== null && !data.per_hop.some(p => p.hop === scope)) scope = null;

      $("an-empty").hidden = true;
      $("an-content").hidden = false;
      renderAll();
    } catch (e) {
      showEmpty(e.message);
    }
  }

  function showEmpty(msg) {
    $("an-content").hidden = true;
    $("an-empty").hidden = false;
    $("an-empty-msg").textContent = msg;
  }

  function scheduleRefresh() {
    if (!$("an-auto-refresh").checked) return;
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(load, 400);
  }

  // ==================== RENDER ====================
  function renderAll() {
    updateHeader();
    renderConfig();
    renderTimeline();
    renderScope();
  }

  function renderScope() {
    renderKpis();
    renderCharts();
    renderHopTable();
    renderPersona();
    renderTopDrift();
    renderTraces();
    updateReportScope();
  }

  function updateHeader() {
    if (!data) return;
    $("an-sim-id").textContent = data.simulation_id;
    let status;
    if (data.is_running) status = `Đang chạy • Hop ${data.current_hop}/${data.max_hops}`;
    else if (data.is_finished) status = `Hoàn tất • ${data.current_hop} Hop`;
    else status = `Tạm dừng tại Hop ${data.current_hop}/${data.max_hops}`;
    $("an-sim-status").textContent = status;
    document.title = `Phân tích ${data.simulation_id} (${data.current_hop} Hop) | MAS-Diffusion-Lab`;
  }

  function renderConfig() {
    const c = data.config || {};
    const items = [
      ["Topology", TOPO_LABELS[c.topology] || c.topology],
      ["Số tác tử N", c.num_nodes],
      ["Hop đã chạy", `${data.current_hop} / ${data.max_hops}`],
      ["Nút nguồn", `#${data.seed_node_id}`],
      ["Fact-Checker", `${Math.round((c.fact_checker_ratio || 0) * 100)}% • ${PLACEMENT_LABELS[c.fact_checker_placement] || c.fact_checker_placement}`],
      ["Mô hình cục bộ", c.local_model],
      ["Tỷ lệ Cloud", `${Math.round((c.cloud_ratio || 0) * 100)}%`],
      ["Nhiệt độ τ / Seed", `${c.temperature} / ${c.seed}`]
    ];
    $("an-config-grid").innerHTML = items.map(([k, v]) =>
      `<div class="an-config-item"><span class="an-label">${esc(k)}</span><strong>${esc(v)}</strong></div>`
    ).join("");
    $("an-seed-msg").textContent = data.origin_message || "--";
  }

  function renderTimeline() {
    const track = $("an-timeline");
    const steps = [{ hop: null, title: "Toàn bộ chu trình", sub: `${data.per_hop.length} Hop • ${data.overall.total_interactions} lượt`, pct: null }];
    data.per_hop.forEach(p => {
      steps.push({ hop: p.hop, title: `Hop ${p.hop}`, sub: `R ${num(p.metrics.penetration_rate, 0)}% • D ${num(p.metrics.average_semantic_drift, 2)}`, pct: p.metrics.penetration_rate });
    });

    track.innerHTML = steps.map(s => {
      const isNew = s.hop !== null && !knownHops.has(s.hop) && knownHops.size > 0;
      return `<button class="an-step ${s.hop === scope ? "active" : ""} ${isNew ? "new" : ""}" data-hop="${s.hop === null ? "" : s.hop}">
        <span class="an-step-title">${esc(s.title)}</span>
        <span class="an-step-sub">${esc(s.sub)}</span>
        ${s.pct !== null ? `<span class="an-step-bar" style="width:${Math.min(100, s.pct)}%"></span>` : ""}
      </button>`;
    }).join("");
    data.per_hop.forEach(p => knownHops.add(p.hop));

    track.querySelectorAll(".an-step").forEach(btn => {
      btn.addEventListener("click", () => {
        const v = btn.getAttribute("data-hop");
        selectScope(v === "" ? null : Number(v));
      });
    });
  }

  function selectScope(hop) {
    if (hop === scope) return;
    scope = hop;
    $("an-timeline").querySelectorAll(".an-step").forEach(btn => {
      const v = btn.getAttribute("data-hop");
      btn.classList.toggle("active", (v === "" ? null : Number(v)) === scope);
    });
    renderScope();
  }

  // ---------- KPIs ----------
  function renderKpis() {
    const stats = scopeStats();
    if (!stats) return;
    let m, prev, rtLabel;
    if (scope === null) {
      m = data.hop_metrics[data.hop_metrics.length - 1];
      prev = null;
      rtLabel = "R_t trung bình";
    } else {
      const i = data.hop_metrics.findIndex(h => h.hop === scope);
      m = data.hop_metrics[i];
      prev = i > 0 ? data.hop_metrics[i - 1] : null;
      rtLabel = "Hệ số R_t";
    }
    const rtVal = scope === null
      ? data.hop_metrics.reduce((a, h) => a + (h.reproduction_rate || 0), 0) / data.hop_metrics.length
      : m.reproduction_rate;
    const driftVal = scope === null ? stats.drift_mean : m.average_semantic_drift;
    const total = stats.total_interactions || 0;
    const dec = stats.decisions;
    const pct = (k) => (total ? (dec[k] / total) * 100 : 0);

    const kpis = [
      { label: scope === null ? "Độ thẩm thấu cuối R(t)" : "Độ thẩm thấu R(t)", val: `${num(m.penetration_rate, 1)}%`, color: COLORS.cyan,
        foot: `${m.informed_total} / ${data.config.num_nodes} tác tử ${prev ? deltaHtml(m.penetration_rate, prev.penetration_rate, 1) : ""}` },
      { label: "Biến dạng ngữ nghĩa TB", val: num(driftVal, 3), color: COLORS.amber,
        foot: `max ${num(stats.drift_max, 3)} • σ ${num(stats.drift_std, 3)} ${prev ? deltaHtml(m.average_semantic_drift, prev.average_semantic_drift, 3, true) : ""}` },
      { label: scope === null ? "Phân cực cuối PI" : "Chỉ số phân cực PI", val: num(m.polarization_index, 3), color: COLORS.rose,
        foot: `Niềm tin TB ${signed(stats.belief_mean, 2)} ${prev ? deltaHtml(m.polarization_index, prev.polarization_index, 3, true) : ""}` },
      { label: rtLabel, val: num(rtVal, 2), color: COLORS.violet,
        foot: rtVal > 1 ? "Lan truyền bùng nổ (>1)" : rtVal === 1 ? "Ổn định (=1)" : "Suy giảm (<1)" },
      { label: "Lượt tương tác", val: total, color: COLORS.blue,
        foot: `${stats.unique_agents} tác tử khác nhau${scope !== null ? ` • ${num(m.hop_duration_seconds, 1)}s` : ""}` }
    ];

    $("an-kpis").innerHTML = kpis.map(k => `
      <div class="an-kpi glass-panel" style="--kpi-color:${k.color}">
        <span class="an-label">${esc(k.label)}</span>
        <div class="an-kpi-val">${k.val}</div>
        <div class="an-kpi-foot">${k.foot}</div>
      </div>`).join("") + `
      <div class="an-kpi glass-panel" style="--kpi-color:${COLORS.emerald}">
        <span class="an-label">Phân bố quyết định</span>
        <div class="an-decision-bar">
          <span style="width:${pct("FORWARD")}%;background:${COLORS.emerald}" title="FORWARD"></span>
          <span style="width:${pct("COUNTER")}%;background:${COLORS.amber}" title="COUNTER"></span>
          <span style="width:${pct("IGNORE")}%;background:${COLORS.slate}" title="IGNORE"></span>
        </div>
        <div class="an-kpi-foot">F ${dec.FORWARD} • C ${dec.COUNTER} • I ${dec.IGNORE}</div>
      </div>`;
  }

  // ---------- Charts ----------
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.font.family = "Inter, sans-serif";
  Chart.defaults.font.size = 11;
  const gridColor = "rgba(255,255,255,0.05)";

  function renderCharts() {
    const labels = data.hop_metrics.map(h => `Hop ${h.hop}`);
    const selIdx = scope === null ? -1 : data.hop_metrics.findIndex(h => h.hop === scope);
    const radii = data.hop_metrics.map((_, i) => (i === selIdx ? 7 : 3.5));

    // Dynamics
    const dyn = {
      labels,
      datasets: [
        { label: "R(t) %", data: data.hop_metrics.map(h => h.penetration_rate), borderColor: COLORS.cyan, backgroundColor: "rgba(0,242,254,0.12)", fill: true, tension: 0.35, yAxisID: "y", pointRadius: radii },
        { label: "Drift TB", data: data.hop_metrics.map(h => h.average_semantic_drift), borderColor: COLORS.amber, backgroundColor: COLORS.amber, tension: 0.35, yAxisID: "y1", pointRadius: radii },
        { label: "PI", data: data.hop_metrics.map(h => h.polarization_index), borderColor: COLORS.rose, backgroundColor: COLORS.rose, tension: 0.35, yAxisID: "y1", pointRadius: radii, borderDash: [5, 4] }
      ]
    };
    if (!charts.dynamics) {
      charts.dynamics = new Chart($("an-chart-dynamics"), {
        type: "line",
        data: dyn,
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: { legend: { labels: { boxWidth: 10, usePointStyle: true } } },
          scales: {
            x: { grid: { color: gridColor } },
            y: { position: "left", min: 0, max: 100, grid: { color: gridColor }, title: { display: true, text: "R(t) %" } },
            y1: { position: "right", min: 0, grid: { drawOnChartArea: false }, title: { display: true, text: "Drift / PI" } }
          },
          onClick: (evt, els, chart) => {
            const pts = chart.getElementsAtEventForMode(evt, "index", { intersect: false }, true);
            if (pts.length) selectScope(data.hop_metrics[pts[0].index].hop);
          }
        }
      });
    } else {
      charts.dynamics.data = dyn;
      charts.dynamics.update();
    }

    // Decisions per hop
    const decData = {
      labels,
      datasets: ["FORWARD", "COUNTER", "IGNORE"].map((k, i) => ({
        label: k,
        data: data.per_hop.map(p => p.stats.decisions[k]),
        backgroundColor: data.per_hop.map((p) => {
          const base = [COLORS.emerald, COLORS.amber, COLORS.slate][i];
          return selIdx === -1 || p.hop === scope ? base : base + "55";
        }),
        borderRadius: 3,
        stack: "dec"
      }))
    };
    if (!charts.decisions) {
      charts.decisions = new Chart($("an-chart-decisions"), {
        type: "bar",
        data: decData,
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { boxWidth: 10, usePointStyle: true } } },
          scales: {
            x: { stacked: true, grid: { color: gridColor } },
            y: { stacked: true, beginAtZero: true, grid: { color: gridColor }, ticks: { precision: 0 } }
          },
          onClick: (evt, els) => {
            if (els.length) selectScope(data.per_hop[els[0].index].hop);
          }
        }
      });
    } else {
      charts.decisions.data = decData;
      charts.decisions.update();
    }

    // Persona chart (scope)
    const stats = scopeStats();
    const personas = Object.keys(stats.persona_stats);
    const perData = {
      labels: personas.map(personaLabel),
      datasets: [
        { label: "Drift TB", data: personas.map(p => stats.persona_stats[p].avg_drift), backgroundColor: "rgba(245,158,11,0.7)", borderRadius: 4, yAxisID: "y" },
        { label: "Niềm tin TB", data: personas.map(p => stats.persona_stats[p].avg_belief), backgroundColor: "rgba(129,140,248,0.7)", borderRadius: 4, yAxisID: "y1" }
      ]
    };
    $("an-persona-chart-scope").textContent = scopeLabel();
    if (!charts.persona) {
      charts.persona = new Chart($("an-chart-persona"), {
        type: "bar",
        data: perData,
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { boxWidth: 10, usePointStyle: true } } },
          scales: {
            x: { grid: { color: gridColor }, ticks: { maxRotation: 30, minRotation: 0 } },
            y: { position: "left", beginAtZero: true, grid: { color: gridColor }, title: { display: true, text: "Drift" } },
            y1: { position: "right", min: -1, max: 1, grid: { drawOnChartArea: false }, title: { display: true, text: "Niềm tin" } }
          }
        }
      });
    } else {
      charts.persona.data = perData;
      charts.persona.update();
    }
  }

  // ---------- Hop table ----------
  function renderHopTable() {
    const tbody = $("an-hop-table").querySelector("tbody");
    tbody.innerHTML = data.per_hop.map((p, i) => {
      const m = p.metrics, s = p.stats;
      const prev = i > 0 ? data.per_hop[i - 1].metrics : null;
      return `<tr class="clickable ${p.hop === scope ? "selected" : ""}" data-hop="${p.hop}">
        <td><strong>Hop ${p.hop}</strong></td>
        <td class="an-mono">${m.active_transmissions}</td>
        <td class="an-mono">${(m.newly_activated_nodes || []).length}</td>
        <td class="an-mono">${num(m.penetration_rate, 1)} ${prev ? deltaHtml(m.penetration_rate, prev.penetration_rate, 1) : ""}</td>
        <td class="an-mono" style="color:${driftColor(m.average_semantic_drift)}">${num(m.average_semantic_drift, 4)} ${prev ? deltaHtml(m.average_semantic_drift, prev.average_semantic_drift, 3, true) : ""}</td>
        <td class="an-mono">${num(s.drift_max, 3)}</td>
        <td class="an-mono">${num(m.polarization_index, 3)} ${prev ? deltaHtml(m.polarization_index, prev.polarization_index, 3, true) : ""}</td>
        <td class="an-mono">${num(m.reproduction_rate, 2)}</td>
        <td class="an-mono"><span style="color:${COLORS.emerald}">${s.decisions.FORWARD}</span> / <span style="color:${COLORS.amber}">${s.decisions.COUNTER}</span> / <span style="color:${COLORS.slate}">${s.decisions.IGNORE}</span></td>
        <td class="an-mono">${m.remaining_queue_size}</td>
        <td class="an-mono">${num(m.hop_duration_seconds, 1)}s</td>
      </tr>`;
    }).join("");
    tbody.querySelectorAll("tr").forEach(tr => {
      tr.addEventListener("click", () => {
        const h = Number(tr.getAttribute("data-hop"));
        selectScope(h === scope ? null : h);
      });
    });
  }

  // ---------- Persona table ----------
  function renderPersona() {
    const stats = scopeStats();
    $("an-persona-scope").textContent = scopeLabel();
    const tbody = $("an-persona-table").querySelector("tbody");
    const rows = Object.entries(stats.persona_stats).sort((a, b) => b[1].count - a[1].count);
    if (!rows.length) {
      tbody.innerHTML = `<tr class="an-empty-row"><td colspan="7">Không có tương tác trong phạm vi này.</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map(([p, s]) => `
      <tr>
        <td><span class="an-badge persona ${p === "FACT_CHECKER" ? "FACT_CHECKER" : ""}">${esc(personaLabel(p))}</span></td>
        <td class="an-mono">${s.count}</td>
        <td class="an-mono" style="color:${COLORS.emerald}">${s.decisions.FORWARD}</td>
        <td class="an-mono" style="color:${COLORS.amber}">${s.decisions.COUNTER}</td>
        <td class="an-mono" style="color:${COLORS.slate}">${s.decisions.IGNORE}</td>
        <td class="an-mono" style="color:${driftColor(s.avg_drift)}">${num(s.avg_drift, 3)}</td>
        <td class="an-mono">${signed(s.avg_belief, 2)}</td>
      </tr>`).join("");
  }

  // ---------- Top drift ----------
  function renderTopDrift() {
    const list = $("an-top-drift");
    const items = scopeTraces().filter(t => t.outgoing_message)
      .sort((a, b) => (b.drift_distance || 0) - (a.drift_distance || 0)).slice(0, 5);
    if (!items.length) {
      list.innerHTML = `<li style="cursor:default;grid-template-columns:1fr"><span class="an-hint">Không có phát ngôn nào trong phạm vi này.</span></li>`;
      return;
    }
    list.innerHTML = items.map((t, i) => `
      <li data-idx="${t._idx}">
        <span class="an-rank">${i + 1}</span>
        <div class="an-top-main">
          <strong>Tác tử #${t.agent_id}</strong> <span class="an-badge persona">${esc(personaLabel(t.persona))}</span>
          <div>Hop ${t.hop} • nhận từ #${t.sender_id} • <span class="an-badge ${t.decision}">${t.decision}</span></div>
        </div>
        <span class="an-top-val">${num(t.drift_distance, 3)}</span>
      </li>`).join("");
    list.querySelectorAll("li[data-idx]").forEach(li => {
      li.addEventListener("click", () => openTraceDetail(Number(li.getAttribute("data-idx"))));
    });
  }

  // ---------- Trace table ----------
  function renderTraces() {
    let items = scopeTraces();
    const q = traceFilter.search.trim().toLowerCase();
    if (q) {
      items = items.filter(t =>
        `#${t.agent_id} #${t.sender_id} ${t.agent_id} ${t.persona} ${personaLabel(t.persona)} ${t.model_name} ${t.outgoing_message || ""} ${t.reasoning || ""}`
          .toLowerCase().includes(q));
    }
    if (traceFilter.decision !== "all") items = items.filter(t => t.decision === traceFilter.decision);
    if (traceFilter.sort === "drift_desc") items.sort((a, b) => (b.drift_distance || 0) - (a.drift_distance || 0));
    else if (traceFilter.sort === "belief_desc") items.sort((a, b) => (b.belief_score || 0) - (a.belief_score || 0));
    else if (traceFilter.sort === "belief_asc") items.sort((a, b) => (a.belief_score || 0) - (b.belief_score || 0));

    $("an-trace-count").textContent = items.length;
    const tbody = $("an-trace-table").querySelector("tbody");
    if (!items.length) {
      tbody.innerHTML = `<tr class="an-empty-row"><td colspan="8">Không có tương tác phù hợp.</td></tr>`;
      return;
    }
    tbody.innerHTML = items.map(t => {
      const d = t.drift_distance || 0;
      return `<tr class="clickable" data-idx="${t._idx}">
        <td class="an-mono">${t.hop}</td>
        <td class="an-mono">#${t.sender_id} → <strong>#${t.agent_id}</strong></td>
        <td><span class="an-badge persona ${t.persona === "FACT_CHECKER" ? "FACT_CHECKER" : ""}">${esc(personaLabel(t.persona))}</span></td>
        <td class="an-mono" style="font-size:0.7rem">${esc(t.model_name)}</td>
        <td><span class="an-badge ${t.decision}">${t.decision}</span></td>
        <td class="an-mono">${signed(t.belief_score, 2)}</td>
        <td><div class="an-drift-cell"><div class="an-drift-meter"><span style="width:${Math.min(100, d * 100)}%;background:${driftColor(d)}"></span></div><span class="an-mono">${num(d, 3)}</span></div></td>
        <td><div class="an-msg-cell">${t.outgoing_message ? esc(t.outgoing_message) : '<em>Im lặng (không chia sẻ)</em>'}</div></td>
      </tr>`;
    }).join("");
    tbody.querySelectorAll("tr[data-idx]").forEach(tr => {
      tr.addEventListener("click", () => openTraceDetail(Number(tr.getAttribute("data-idx"))));
    });
  }

  $("an-trace-search").addEventListener("input", (e) => { traceFilter.search = e.target.value; renderTraces(); });
  $("an-trace-decision").addEventListener("change", (e) => { traceFilter.decision = e.target.value; renderTraces(); });
  $("an-trace-sort").addEventListener("change", (e) => { traceFilter.sort = e.target.value; renderTraces(); });

  // ==================== DRILLDOWN MODAL ====================
  function tokenize(s) {
    return (s || "").split(/(\s+)/).filter(x => x.length);
  }

  function wordDiff(a, b) {
    const A = tokenize(a), B = tokenize(b);
    const n = A.length, m = B.length;
    if (n * m > 400000) return esc(b); // tránh quá tải với văn bản rất dài
    const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
    for (let i = n - 1; i >= 0; i--) {
      for (let j = m - 1; j >= 0; j--) {
        dp[i][j] = A[i].toLowerCase() === B[j].toLowerCase() ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
    let i = 0, j = 0, out = "";
    while (i < n && j < m) {
      if (A[i].toLowerCase() === B[j].toLowerCase()) { out += esc(B[j]); i++; j++; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) { out += /^\s+$/.test(A[i]) ? A[i] : `<del>${esc(A[i])}</del>`; i++; }
      else { out += /^\s+$/.test(B[j]) ? B[j] : `<ins>${esc(B[j])}</ins>`; j++; }
    }
    while (i < n) { out += /^\s+$/.test(A[i]) ? A[i] : `<del>${esc(A[i])}</del>`; i++; }
    while (j < m) { out += /^\s+$/.test(B[j]) ? B[j] : `<ins>${esc(B[j])}</ins>`; j++; }
    return out;
  }

  function openTraceDetail(idx) {
    const t = data.traces[idx];
    if (!t) return;
    const agent = (data.agents || []).find(a => a.id === t.agent_id) || {};
    const history = data.traces.map((x, i) => ({ ...x, _idx: i })).filter(x => x.agent_id === t.agent_id);

    $("an-modal-title").textContent = `Tác tử #${t.agent_id} • Hop ${t.hop}`;
    $("an-modal-sub").textContent = `${personaLabel(t.persona)} • ${t.model_type} / ${t.model_name} • Bậc liên kết ${agent.degree ?? "--"}${agent.is_seed ? " • Nút nguồn" : ""}`;

    const d = t.drift_distance || 0;
    const detail = [
      ["Nhận từ", `#${t.sender_id}`],
      ["Quyết định", `<span class="an-badge ${t.decision}">${t.decision}</span>`],
      ["Niềm tin b<sub>i</sub>", signed(t.belief_score, 2)],
      ["Drift so với M<sub>0</sub>", `<span style="color:${driftColor(d)}">${num(d, 4)}</span>`],
      ["Trạng thái hiện tại", esc(agent.state || "--")]
    ];

    const hasOut = !!t.outgoing_message;
    $("an-modal-body").innerHTML = `
      <div class="an-detail-grid">
        ${detail.map(([k, v]) => `<div class="an-detail-item"><span class="an-label">${k}</span><strong>${v}</strong></div>`).join("")}
      </div>

      <div class="an-block" style="--block-color:${COLORS.blue}">
        <div class="an-block-title">Thông điệp đầu vào (từ #${t.sender_id})</div>
        <div class="an-block-content">${esc(t.incoming_message) || "--"}</div>
      </div>

      <div class="an-block" style="--block-color:${COLORS.violet}">
        <div class="an-block-title">Chuỗi suy luận nội tâm</div>
        <div class="an-block-content ${t.reasoning ? "" : "muted"}">${t.reasoning ? esc(t.reasoning) : "Không ghi nhận lập luận."}</div>
      </div>

      <div class="an-block" style="--block-color:${COLORS.emerald}">
        <div class="an-block-title">Thông điệp phát tán đầu ra</div>
        <div class="an-block-content ${hasOut ? "" : "muted"}">${hasOut ? esc(t.outgoing_message) : "Tác tử chọn im lặng, không chia sẻ thông điệp."}</div>
      </div>

      ${hasOut ? `
      <div class="an-block" style="--block-color:${COLORS.amber}">
        <div class="an-block-title">
          So sánh biến dạng văn bản
          <select class="an-input" id="an-diff-mode" style="padding:3px 8px;font-size:0.7rem;text-transform:none;letter-spacing:0">
            <option value="incoming">Đầu vào → Đầu ra</option>
            <option value="origin">Thông điệp gốc M0 → Đầu ra</option>
          </select>
          <span class="an-diff-legend"><del>bị lược bỏ</del> <ins>được thêm vào</ins></span>
        </div>
        <div class="an-block-content an-diff" id="an-diff-body">${wordDiff(t.incoming_message, t.outgoing_message)}</div>
      </div>` : ""}

      <div class="an-block" style="--block-color:${COLORS.cyan}">
        <div class="an-block-title">Lịch sử tương tác của tác tử (${history.length} lượt)</div>
        <div class="an-history-list">
          ${history.map(h => `
            <div class="an-history-item ${h._idx === idx ? "current" : ""}" data-idx="${h._idx}">
              <span class="an-mono">Hop ${h.hop}</span>
              <span class="an-mono">#${h.sender_id} → #${h.agent_id}</span>
              <span><span class="an-badge ${h.decision}">${h.decision}</span></span>
              <span class="an-mono">b ${signed(h.belief_score, 2)}</span>
              <span class="an-mono" style="color:${driftColor(h.drift_distance || 0)}">drift ${num(h.drift_distance || 0, 3)}</span>
            </div>`).join("")}
        </div>
      </div>`;

    const diffMode = $("an-diff-mode");
    if (diffMode) {
      diffMode.addEventListener("change", () => {
        const src = diffMode.value === "origin" ? data.origin_message : t.incoming_message;
        $("an-diff-body").innerHTML = wordDiff(src, t.outgoing_message);
      });
    }
    $("an-modal-body").querySelectorAll(".an-history-item").forEach(el => {
      el.addEventListener("click", () => openTraceDetail(Number(el.getAttribute("data-idx"))));
    });

    $("an-modal").classList.add("open");
    $("an-modal").setAttribute("aria-hidden", "false");
    $("an-modal-body").scrollTop = 0;
  }

  function closeModal() {
    $("an-modal").classList.remove("open");
    $("an-modal").setAttribute("aria-hidden", "true");
  }
  $("an-modal-close").addEventListener("click", closeModal);
  $("an-modal").addEventListener("click", (e) => { if (e.target === $("an-modal")) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

  // ==================== BÁO CÁO NHẬN ĐỊNH KHOA HỌC ====================
  const reportKey = (provider) => `${provider}|${scope === null ? "all" : scope}|${data ? data.current_hop : 0}`;

  function updateReportScope() {
    $("an-report-scope").textContent = scopeLabel();
    const cached = data ? reportCache[reportKey($("an-report-provider").value)] : null;
    if (cached) showReport(cached);
    else if (currentReport) resetReportView();
  }

  function resetReportView() {
    currentReport = null;
    $("an-report-meta").hidden = true;
    $("an-btn-copy-report").disabled = true;
    $("an-btn-download-report").disabled = true;
    $("an-report-body").innerHTML = `<p class="an-report-placeholder">Chọn phạm vi (toàn bộ chu trình hoặc một Hop cụ thể) rồi bấm <strong>Sinh Báo cáo Nhận định</strong>. Báo cáo sẽ phân tích động học lan truyền, biến dạng ngữ nghĩa, phân cực niềm tin, hiệu quả Fact-Checker và đưa ra khuyến nghị cho các lần thực nghiệm tiếp theo.</p>`;
  }

  function renderMarkdown(md) {
    if (window.marked) {
      const html = marked.parse(md);
      return window.DOMPurify ? DOMPurify.sanitize(html) : html;
    }
    return `<pre style="white-space:pre-wrap">${esc(md)}</pre>`;
  }

  function showReport(rep) {
    currentReport = rep;
    const meta = $("an-report-meta");
    meta.hidden = false;
    meta.textContent = `Mô hình đánh giá: ${rep.provider === "gemini" ? "Gemini" : "Ollama"} / ${rep.model} • Phạm vi: ${rep.scope_hop === null ? "Toàn bộ chu trình" : "Hop " + rep.scope_hop} • Dữ liệu đến Hop ${rep.hops_analyzed} • Sinh lúc ${rep.generated_at}`;
    $("an-report-body").innerHTML = renderMarkdown(rep.report_markdown);
    $("an-btn-copy-report").disabled = false;
    $("an-btn-download-report").disabled = false;
  }

  $("an-report-provider").addEventListener("change", updateReportScope);

  $("an-btn-report").addEventListener("click", async () => {
    if (!data) return;
    const btn = $("an-btn-report");
    const provider = $("an-report-provider").value;
    const key = reportKey(provider);
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="an-spinner" style="width:13px;height:13px"></span> Đang sinh báo cáo...`;
    $("an-report-meta").hidden = true;
    $("an-report-body").innerHTML = `
      <div class="an-loading"><span class="an-spinner"></span>Đang tổng hợp số liệu ${esc(scopeLabel())} và gửi tới ${provider === "gemini" ? "Gemini" : "Ollama cục bộ"}${provider === "ollama" ? " (có thể mất 1-3 phút trên GPU 4GB)" : ""}...</div>
      <div class="an-skeleton-line" style="width:90%"></div>
      <div class="an-skeleton-line" style="width:75%"></div>
      <div class="an-skeleton-line" style="width:82%"></div>`;

    try {
      const res = await fetch("/api/analysis/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, hop: scope })
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Không sinh được báo cáo");
      body.generated_at = new Date().toLocaleString("vi-VN");
      reportCache[key] = body;
      showReport(body);
    } catch (e) {
      $("an-report-body").innerHTML = `<p class="an-error">Lỗi: ${esc(e.message)}</p>
        <p class="an-hint">Gợi ý: kiểm tra GEMINI_API_KEY trong file .env, hoặc chuyển sang Ollama (cục bộ) nếu không có Internet.</p>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  });

  function reportAsMarkdown() {
    if (!currentReport || !data) return "";
    const r = currentReport;
    return `# Báo cáo Nhận định Khoa học — ${data.simulation_id}\n\n` +
      `- Phạm vi: ${r.scope_hop === null ? "Toàn bộ chu trình" : "Hop " + r.scope_hop}\n` +
      `- Dữ liệu đến Hop: ${r.hops_analyzed}\n` +
      `- Mô hình đánh giá: ${r.provider} / ${r.model}\n` +
      `- Thời điểm: ${r.generated_at}\n\n---\n\n${r.report_markdown}\n`;
  }

  $("an-btn-copy-report").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(reportAsMarkdown());
      const b = $("an-btn-copy-report");
      b.textContent = "Đã sao chép";
      setTimeout(() => (b.textContent = "Sao chép"), 1500);
    } catch (e) { alert("Không sao chép được: " + e.message); }
  });

  $("an-btn-download-report").addEventListener("click", () => {
    if (!currentReport) return;
    const s = currentReport.scope_hop === null ? "all" : `hop${currentReport.scope_hop}`;
    download("\uFEFF" + reportAsMarkdown(), `${data.simulation_id}_bao_cao_${s}.md`, "text/markdown;charset=utf-8");
  });

  // ==================== HEADER ACTIONS ====================
  $("an-btn-back").addEventListener("click", () => {
    if (window.opener && !window.opener.closed) {
      try { window.opener.focus(); } catch (e) {}
      window.close();
    } else {
      window.location.href = "/";
    }
  });
  $("an-btn-refresh").addEventListener("click", load);
  $("an-btn-export-json").addEventListener("click", () => {
    if (!data) return;
    download(JSON.stringify(data, null, 2), `${data.simulation_id}_analysis.json`, "application/json");
  });

  // ==================== WEBSOCKET AUTO-REFRESH ====================
  function setupWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    ws.onmessage = (event) => {
      let msg;
      try { msg = JSON.parse(event.data); } catch { return; }
      if (msg.event === "HOP_COMPLETED" || msg.event === "SIMULATION_INITIALIZED") scheduleRefresh();
    };
    ws.onclose = () => setTimeout(setupWebSocket, 3000);
  }

  load();
  setupWebSocket();
});
