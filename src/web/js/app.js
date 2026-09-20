// MAS-Diffusion-Lab Frontend Controller
// Enhanced with ui-ux-pro-max, frontend-design, claude-d3js-skill & animejs-animation

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const btnInit = document.getElementById("btn-init");
  const btnStep = document.getElementById("btn-step");
  const btnRun = document.getElementById("btn-run");
  const btnStop = document.getElementById("btn-stop");
  const btnExport = document.getElementById("btn-export");

  const hudHop = document.getElementById("hud-hop");
  const hudPenetration = document.getElementById("hud-penetration");
  const hudDrift = document.getElementById("hud-drift");
  const hudPolarization = document.getElementById("hud-polarization");
  const hudQueue = document.getElementById("hud-queue");

  const ollamaStatusPill = document.getElementById("ollama-status-pill");
  const ollamaDot = document.getElementById("ollama-dot");
  const ollamaVal = document.getElementById("ollama-val");
  const cloudDot = document.getElementById("cloud-dot");
  const cloudVal = document.getElementById("cloud-val");
  const activeEngineBadge = document.getElementById("active-engine-badge");

  const liveMessageFeed = document.getElementById("live-message-feed");
  const networkContainer = document.getElementById("network-canvas");
  const canvasPlaceholder = document.getElementById("canvas-placeholder");

  const ollamaModal = document.getElementById("ollama-modal");
  const btnOllamaGuide = document.getElementById("btn-ollama-guide");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnRecheckOllama = document.getElementById("btn-recheck-ollama");
  const recheckFeedback = document.getElementById("recheck-feedback");

  // Enhanced Controls & Inspector Elements
  const togglePacketWaves = document.getElementById("toggle-packet-waves");
  const btnFitGraph = document.getElementById("btn-fit-graph");
  const btnSnapshotGraph = document.getElementById("btn-snapshot-graph");
  const agentInspectorDrawer = document.getElementById("agent-inspector-drawer");
  const btnCloseInspector = document.getElementById("btn-close-inspector");

  // Execution Status Bar & Live Pipeline Terminal Elements
  const execDot = document.getElementById("exec-dot");
  const execStatusText = document.getElementById("exec-status-text");
  const execProgressFill = document.getElementById("exec-progress-fill");
  const execProgressPercent = document.getElementById("exec-progress-percent");
  const execTimerVal = document.getElementById("exec-timer-val");
  const execEtaBadge = document.getElementById("exec-eta-badge");
  const btnTogglePipeline = document.getElementById("btn-toggle-pipeline");
  const pipelineTerminalDrawer = document.getElementById("pipeline-terminal-drawer");
  const terminalActiveModel = document.getElementById("terminal-active-model");
  const terminalBody = document.getElementById("terminal-body");
  const btnClearTerminal = document.getElementById("btn-clear-terminal");
  const btnCloseTerminal = document.getElementById("btn-close-terminal");

  let activeTimerInterval = null;
  let hopStartTimeStamp = 0;
  let activeProcessingNodeId = null;

  // Quick claim chips
  document.querySelectorAll(".claim-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.getElementById("input-message").value = chip.getAttribute("data-msg");
      if (window.anime) {
        anime({
          targets: chip,
          scale: [0.95, 1.05, 1],
          duration: 300,
          easing: "easeOutQuad"
        });
      }
    });
  });

  // State
  let network = null;
  let nodesDataSet = null;
  let edgesDataSet = null;
  let ws = null;
  let currentSimulationId = null;
  let maxHopsConfig = 8;
  let allTraces = [];
  let currentFilter = "all";
  let currentGraphNodes = [];

  // Packet Wave Engine (Anime.js & D3 Canvas Integration)
  let activePackets = [];
  let activeRipples = [];
  let packetAnimFrame = null;
  let enablePacketWaves = true;
  let lastHudValues = { penetration: 0, drift: 0, polarization: 0 };

  // Color mappings
  const STATE_COLORS = {
    "UNINFORMED": { background: "#475569", border: "#64748b" },
    "EXPOSED": { background: "#38bdf8", border: "#0284c7" },
    "INFECTED_BELIEVER": { background: "#10b981", border: "#059669" },
    "INOCULATED_SKEPTIC": { background: "#f59e0b", border: "#d97706" },
    "REFRACTORY": { background: "#334155", border: "#475569" }
  };

  // ==================== CHARTS INITIALIZATION ====================
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8", font: { size: 10 } } },
      y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8", font: { size: 10 } } }
    }
  };

  const chartDiffusion = new Chart(document.getElementById("chart-diffusion").getContext("2d"), {
    type: "line",
    data: {
      labels: [0],
      datasets: [{
        label: "Độ phủ R(t) (%)",
        data: [0],
        borderColor: "#00f2fe",
        backgroundColor: "rgba(0, 242, 254, 0.15)",
        fill: true,
        tension: 0.35,
        borderWidth: 2
      }]
    },
    options: chartOptions
  });

  const chartDrift = new Chart(document.getElementById("chart-drift").getContext("2d"), {
    type: "bar",
    data: {
      labels: [0],
      datasets: [{
        label: "Trôi dạt Ngữ nghĩa",
        data: [0],
        backgroundColor: "rgba(245, 158, 11, 0.65)",
        borderColor: "#f59e0b",
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: chartOptions
  });

  const chartPolarization = new Chart(document.getElementById("chart-polarization").getContext("2d"), {
    type: "line",
    data: {
      labels: [0],
      datasets: [{
        label: "Chỉ số Phân cực",
        data: [0],
        borderColor: "#f43f5e",
        backgroundColor: "rgba(244, 63, 94, 0.15)",
        fill: true,
        tension: 0.35,
        borderWidth: 2
      }]
    },
    options: chartOptions
  });

  // ==================== SYSTEM STATUS CHECK ====================
  async function checkSystemStatus() {
    try {
      const res = await fetch("/api/system/status");
      if (!res.ok) return;
      const data = await res.json();

      // Ollama
      if (data.ollama && data.ollama.online) {
        ollamaDot.className = "status-dot";
        const modelCount = data.ollama.available_models ? data.ollama.available_models.length : 0;
        ollamaVal.textContent = `Online (${modelCount} models)`;
        activeEngineBadge.textContent = "Engine: OLLAMA CỤC BỘ";
        activeEngineBadge.style.color = "var(--accent-emerald)";

        // Cập nhật danh sách mô hình có sẵn vào dropdown
        const selectLocalModel = document.getElementById("select-local-model");
        if (selectLocalModel && data.ollama.available_models && data.ollama.available_models.length > 0) {
          const prevVal = selectLocalModel.value;
          const validChatModels = data.ollama.available_models.filter(m => !m.includes("embed"));
          if (validChatModels.length > 0) {
            selectLocalModel.innerHTML = "";
            validChatModels.forEach(m => {
              const opt = document.createElement("option");
              opt.value = m;
              let label = m;
              if (m.includes("qwen2.5:3b")) label = "Qwen 2.5 3B (Tối ưu GPU 4GB VRAM - Rất nhanh)";
              else if (m.includes("llama3:8b")) label = "Llama 3 8B (Tư duy sâu - Hybrid VRAM/RAM)";
              else if (m.includes("qwen2.5:7b")) label = "Qwen 2.5 7B (Tư duy logic cao)";
              opt.textContent = label;
              selectLocalModel.appendChild(opt);
            });
            if (validChatModels.includes(prevVal)) {
              selectLocalModel.value = prevVal;
            } else {
              const bestFit = validChatModels.find(m => m.includes("3b")) || validChatModels[0];
              selectLocalModel.value = bestFit;
            }
          }
        }
      } else {
        ollamaDot.className = "status-dot offline";
        ollamaVal.textContent = "Chưa kết nối (Dùng Mock)";
        activeEngineBadge.textContent = "Engine: MOCK SIMULATOR";
        activeEngineBadge.style.color = "var(--accent-cyan)";
      }

      // Cloud
      if (data.cloud && data.cloud.cloud_ready) {
        cloudDot.className = "status-dot";
        cloudVal.textContent = "Sẵn sàng";
      } else {
        cloudDot.className = "status-dot offline";
        cloudVal.textContent = "Chưa có Key (Tùy chọn)";
      }

      return data;
    } catch (e) {
      console.warn("Lỗi kiểm tra trạng thái hệ thống:", e);
    }
  }

  // ==================== EXECUTION TIMER & LIVE TERMINAL LOGGING ====================
  function startHopTimer() {
    if (activeTimerInterval) clearInterval(activeTimerInterval);
    hopStartTimeStamp = performance.now();
    if (execDot) execDot.className = "exec-pulse-dot running";
    activeTimerInterval = setInterval(() => {
      const elapsedMs = performance.now() - hopStartTimeStamp;
      const totalSec = Math.floor(elapsedMs / 1000);
      const mins = Math.floor(totalSec / 60);
      const secs = totalSec % 60;
      const tenths = Math.floor((elapsedMs % 1000) / 100);
      if (execTimerVal) {
        execTimerVal.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${tenths}`;
      }
    }, 100);
  }

  function stopHopTimer(finalSeconds = null) {
    if (activeTimerInterval) {
      clearInterval(activeTimerInterval);
      activeTimerInterval = null;
    }
    if (execDot) execDot.className = "exec-pulse-dot success";
    if (finalSeconds !== null && execTimerVal) {
      execTimerVal.textContent = `${finalSeconds}s`;
    }
    activeProcessingNodeId = null;
    if (network) network.redraw();
  }

  function logToTerminal(type, text) {
    if (!terminalBody) return;
    const line = document.createElement("div");
    line.className = `terminal-line ${type}`;
    const now = new Date();
    const timeStr = `[${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}]`;
    line.textContent = `${timeStr} ${text}`;
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  // ==================== WEBSOCKET SETUP ====================
  function setupWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
      console.log("[WebSocket] Kết nối realtime thành công");
      logToTerminal("info", "Kết nối WebSocket thành công. Sẵn sàng theo dõi tiến trình suy luận.");
    };

    ws.onmessage = (event) => {
      try {
        const msg = jsonParseSafe(event.data);
        if (!msg) return;

        if (msg.event === "HOP_STARTED") {
          const d = msg.data;
          startHopTimer();
          if (execProgressFill) execProgressFill.style.width = "0%";
          if (execProgressPercent) execProgressPercent.textContent = "0%";
          if (execStatusText) execStatusText.textContent = `⚡ Đang xử lý Hop ${d.hop}: Hàng đợi gồm ${d.total_messages} thông điệp...`;
          if (execEtaBadge) execEtaBadge.textContent = "ETA: Đang tính...";
          logToTerminal("info", `🚀 === BẮT ĐẦU HOP ${d.hop}: Đang phân tích ${d.total_messages} thông điệp qua LLMs ===`);
        } else if (msg.event === "AGENT_PROCESSING_START") {
          const d = msg.data;
          activeProcessingNodeId = d.agent_id;
          if (terminalActiveModel) terminalActiveModel.textContent = `Model: ${d.model_name}`;
          if (execStatusText) {
            execStatusText.textContent = `⚡ Hop ${d.hop}: Đang suy luận Tác tử #${d.agent_id} (${d.persona}) qua ${d.model_name} [${d.message_index}/${d.total_messages}]`;
          }
          if (network) {
            network.redraw();
          }
          logToTerminal("start", `🧠 [${d.message_index}/${d.total_messages}] Tác tử #${d.agent_id} (${d.persona}) đọc tin từ #${d.sender_id} • Mô hình: ${d.model_name}...`);
        } else if (msg.event === "AGENT_PROCESSING_END") {
          const d = msg.data;
          if (execProgressFill) execProgressFill.style.width = `${d.progress_percent}%`;
          if (execProgressPercent) execProgressPercent.textContent = `${Math.round(d.progress_percent)}%`;
          if (execEtaBadge) execEtaBadge.textContent = d.eta_seconds > 0 ? `ETA: ~${d.eta_seconds}s` : "Gần xong";

          // Update node in Vis.js data set immediately
          if (nodesDataSet) {
            const colorScheme = STATE_COLORS[d.decision === "IGNORE" ? "REFRACTORY" : (d.decision === "COUNTER" ? "INOCULATED_SKEPTIC" : "INFECTED_BELIEVER")];
            if (colorScheme) {
              nodesDataSet.update({
                id: d.agent_id,
                color: { background: colorScheme.background, border: colorScheme.border }
              });
            }
          }

          const decIcon = d.decision === "FORWARD" ? "➡️ Chuyển tiếp (FORWARD)" : (d.decision === "COUNTER" ? "🛡️ Phản biện (COUNTER)" : "🤐 Giữ im lặng (IGNORE)");
          const typeClass = d.decision === "FORWARD" ? "success" : (d.decision === "COUNTER" ? "counter" : "ignore");
          logToTerminal(typeClass, `✅ Tác tử #${d.agent_id} hoàn tất (${d.inference_duration}s) • ${decIcon} • Niềm tin: ${d.belief_score >= 0 ? '+' : ''}${d.belief_score} • Drift: ${d.drift_distance.toFixed(3)}`);
          if (d.reasoning) {
            logToTerminal("info", `   💭 Lập luận: "${d.reasoning.substring(0, 100)}${d.reasoning.length > 100 ? '...' : ''}"`);
          }
        } else if (msg.event === "HOP_COMPLETED") {
          const summary = msg.data.hop_summary;
          stopHopTimer(summary ? summary.hop_duration_seconds : null);
          if (execProgressFill) execProgressFill.style.width = "100%";
          if (execProgressPercent) execProgressPercent.textContent = "100%";
          if (execEtaBadge) execEtaBadge.textContent = "Hoàn tất";
          if (execStatusText && summary) {
            execStatusText.textContent = `✅ Hoàn thành Hop ${summary.hop} trong ${summary.hop_duration_seconds || 0}s (${summary.active_transmissions} tác tử, TB ${summary.avg_agent_duration || 0}s/tác tử)`;
            logToTerminal("success", `🏁 === HOÀN THÀNH HOP ${summary.hop} TRONG ${summary.hop_duration_seconds}s (Độ phủ: ${summary.penetration_rate}%, Drift: ${summary.average_semantic_drift}, Phân cực: ${summary.polarization_index}) ===\n`);
          }
          handleHopCompleted(msg.data);
        }
      } catch (e) {
        console.error("Lỗi xử lý WebSocket message:", e);
      }
    };

    ws.onclose = () => {
      setTimeout(setupWebSocket, 3000); // Reconnect
    };
  }

  function jsonParseSafe(str) {
    try { return JSON.parse(str); } catch { return null; }
  }

  // ==================== ANIMATED HUD NUMBER COUNTER ====================
  function animateHudValue(element, startVal, endVal, suffix = "", decimals = 1) {
    if (!element) return;
    if (window.anime && typeof startVal === "number" && typeof endVal === "number" && startVal !== endVal) {
      const obj = { val: startVal };
      anime({
        targets: obj,
        val: endVal,
        duration: 850,
        easing: "easeOutExpo",
        update: () => {
          element.textContent = obj.val.toFixed(decimals) + suffix;
        }
      });
    } else {
      element.textContent = (typeof endVal === "number" ? endVal.toFixed(decimals) : endVal) + suffix;
    }
  }

  // ==================== SIMULATION INITIALIZATION ====================
  btnInit.addEventListener("click", async () => {
    btnInit.disabled = true;
    btnInit.textContent = "Đang sinh mạng lưới...";

    const payload = {
      topology: document.getElementById("select-topology").value,
      num_nodes: parseInt(document.getElementById("input-nodes").value, 10),
      seed_message: document.getElementById("input-message").value,
      local_model: document.getElementById("select-local-model") ? document.getElementById("select-local-model").value : "qwen2.5:3b",
      fact_checker_ratio: parseFloat(document.getElementById("input-fc-ratio").value),
      fact_checker_placement: document.getElementById("select-fc-placement").value,
      cloud_ratio: parseFloat(document.getElementById("input-cloud-ratio").value) / 100.0,
      temperature: parseFloat(document.getElementById("input-temp").value),
      max_hops: parseInt(document.getElementById("input-hops").value, 10),
      seed: 42
    };

    maxHopsConfig = payload.max_hops;

    try {
      const res = await fetch("/api/simulation/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      currentSimulationId = data.simulation_id;
      currentGraphNodes = data.graph_data ? data.graph_data.nodes : [];

      // Render Graph
      renderVisNetwork(data.graph_data);

      // Reset HUD
      hudHop.textContent = `0 / ${maxHopsConfig}`;
      lastHudValues = { penetration: 0, drift: 0, polarization: 0 };
      hudPenetration.textContent = "0.0%";
      hudDrift.textContent = "0.000";
      hudPolarization.textContent = "0.000";
      hudQueue.textContent = `${data.pending_messages} tin`;

      // Reset Charts
      resetCharts();

      // Reset Execution Status Bar & Timer
      if (execProgressFill) execProgressFill.style.width = "0%";
      if (execProgressPercent) execProgressPercent.textContent = "0%";
      if (execTimerVal) execTimerVal.textContent = "00:00.0";
      if (execEtaBadge) execEtaBadge.textContent = "ETA: --";
      if (execStatusText) execStatusText.textContent = `Đã sinh mạng lưới ${data.total_nodes} tác tử. Sẵn sàng mô phỏng Hop 1.`;
      if (execDot) execDot.className = "exec-pulse-dot";
      logToTerminal("info", `🌐 Khởi tạo mạng lưới mới: ${data.total_nodes} tác tử, nút nguồn #${data.seed_node_id} (Seed Injection).`);

      // Reset Message Feed
      allTraces = [];
      liveMessageFeed.innerHTML = `
        <div class="trace-card" data-persona="SEED">
          <div class="trace-header">
            <span class="trace-agent">Nút Nguồn #${data.seed_node_id} (Seed Injection)</span>
            <span class="trace-hop-badge">Hop 0</span>
          </div>
          <div class="trace-msg">"${data.seed_message}"</div>
          <div class="trace-footer">
            <span>Bắt đầu thác thông tin</span>
            <span class="drift-badge">Dist: 0.000</span>
          </div>
        </div>
      `;

      // Close inspector if open
      closeAgentInspector();

      // Enable Action Buttons
      btnStep.disabled = false;
      btnRun.disabled = false;
      btnStop.disabled = true;
      btnExport.disabled = false;

    } catch (e) {
      alert("Lỗi khi khởi tạo mạng: " + e.message);
    } finally {
      btnInit.disabled = false;
      btnInit.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
        </svg> Khởi tạo Mạng lưới`;
    }
  });

  // ==================== VIS.JS GRAPH RENDERING ====================
  function renderVisNetwork(graphData) {
    if (canvasPlaceholder) canvasPlaceholder.style.display = "none";
    if (!graphData || !graphData.nodes) return;

    currentGraphNodes = graphData.nodes;

    // D3 Scale for dynamic node sizes based on degree centrality (claude-d3js-skill)
    const degreeExtent = (window.d3 && graphData.nodes.length > 0)
      ? d3.extent(graphData.nodes, n => n.degree || 1)
      : [1, 5];
    const minD = Math.min(1, degreeExtent[0] !== undefined ? degreeExtent[0] : 1);
    const maxD = Math.max(5, degreeExtent[1] !== undefined ? degreeExtent[1] : 5);
    const nodeSizeScale = (window.d3)
      ? d3.scaleSqrt().domain([minD, maxD]).range([14, 26])
      : (deg) => deg >= 5 ? 22 : 14;

    const formattedNodes = graphData.nodes.map(n => {
      const colorScheme = STATE_COLORS[n.state] || STATE_COLORS["UNINFORMED"];
      const isHub = n.degree >= 5;
      const nodeSize = Math.round(nodeSizeScale(n.degree || 1));
      return {
        id: n.id,
        label: `${n.id} (${n.persona.replace("_", " ").substring(0, 8)})`,
        x: n.x,
        y: n.y,
        shape: isHub ? "diamond" : "dot",
        size: nodeSize,
        color: {
          background: colorScheme.background,
          border: colorScheme.border,
          highlight: { background: "#00f2fe", border: "#ffffff" },
          hover: { background: "#38bdf8", border: "#ffffff" }
        },
        font: { color: "#f8fafc", size: 10, face: "Inter", strokeWidth: 2, strokeColor: "#0b0f19" },
        borderWidth: isHub ? 3 : 1.8,
        title: `Tác tử #${n.id}\nPersona: ${n.persona}\nModel: ${n.model_name}\nBậc liên kết: ${n.degree}\nNiềm tin: ${n.belief_score}`
      };
    });

    const formattedEdges = graphData.edges.map(e => ({
      id: e.id || `e_${e.from}_${e.to}`,
      from: e.from,
      to: e.to,
      color: { color: "rgba(148, 163, 184, 0.25)", highlight: "#00f2fe", hover: "#38bdf8" },
      width: 1.5,
      smooth: { type: "continuous", roundness: 0.15 }
    }));

    nodesDataSet = new vis.DataSet(formattedNodes);
    edgesDataSet = new vis.DataSet(formattedEdges);

    const data = { nodes: nodesDataSet, edges: edgesDataSet };
    const options = {
      physics: {
        enabled: true,
        solver: "barnesHut",
        barnesHut: {
          gravitationalConstant: -2200,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.2
        },
        stabilization: {
          enabled: true,
          iterations: 150,
          updateInterval: 25
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        selectable: true
      }
    };

    if (network) {
      try { network.destroy(); } catch (e) {}
    }

    network = new vis.Network(networkContainer, data, options);

    // After stabilization iterations done, fit graph automatically
    network.once("stabilizationIterationsDone", () => {
      network.fit({ animation: { duration: 500, easingFunction: "easeInOutQuad" } });
    });

    // Fallback fit after short timeout
    setTimeout(() => {
      if (network) {
        network.fit({ animation: { duration: 400, easingFunction: "easeOutQuad" } });
      }
    }, 300);

    // Click handler for Agent Inspector Drawer
    network.on("click", (params) => {
      if (params.nodes && params.nodes.length > 0) {
        openAgentInspector(params.nodes[0]);
      } else {
        closeAgentInspector();
      }
    });

    // Hook into Vis.js Canvas Render Loop for Animated Packet Waves & Ripples
    network.on("afterDrawing", (ctx) => {
      drawPacketsAndRipples(ctx);
    });
  }

  // ==================== PACKET WAVE & RIPPLE ENGINE ====================
  function spawnPacketWaves(traces) {
    if (!enablePacketWaves || !network || !traces || traces.length === 0) return;

    traces.forEach((trace, index) => {
      if (trace.sender_id === undefined || trace.agent_id === undefined) return;
      if (trace.sender_id === trace.agent_id) return;

      let color = "#00f2fe";
      if (trace.decision === "COUNTER") color = "#f59e0b";
      else if (trace.decision === "FORWARD") color = "#10b981";
      else if (trace.decision === "IGNORE") color = "#64748b";

      const packet = {
        from: trace.sender_id,
        to: trace.agent_id,
        progress: 0,
        color: color,
        decision: trace.decision,
        speed: 0.022 + (index % 3) * 0.004
      };

      setTimeout(() => {
        activePackets.push(packet);
        if (!packetAnimFrame) startPacketAnimationLoop();
      }, index * 80);
    });
  }

  function startPacketAnimationLoop() {
    function animate() {
      let stillActive = false;

      // Update in-flight packets
      for (let i = activePackets.length - 1; i >= 0; i--) {
        const pkt = activePackets[i];
        pkt.progress += pkt.speed;

        if (pkt.progress >= 1.0) {
          activeRipples.push({
            nodeId: pkt.to,
            radius: 8,
            maxRadius: 38,
            alpha: 0.85,
            color: pkt.color
          });
          activePackets.splice(i, 1);
        } else {
          stillActive = true;
        }
      }

      // Update impact ripples
      for (let i = activeRipples.length - 1; i >= 0; i--) {
        const rip = activeRipples[i];
        rip.radius += 1.3;
        rip.alpha -= 0.032;

        if (rip.alpha <= 0 || rip.radius >= rip.maxRadius) {
          activeRipples.splice(i, 1);
        } else {
          stillActive = true;
        }
      }

      if (network) network.redraw();

      if (stillActive) {
        packetAnimFrame = requestAnimationFrame(animate);
      } else {
        packetAnimFrame = null;
        if (network) network.redraw();
      }
    }

    packetAnimFrame = requestAnimationFrame(animate);
  }

  function drawPacketsAndRipples(ctx) {
    if (!network) return;

    // 0. Hiệu ứng Radar Spotlight phát sáng trên Tác tử đang được LLM suy luận
    if (activeProcessingNodeId !== null) {
      try {
        const pos = network.getPosition(activeProcessingNodeId);
        if (pos) {
          ctx.save();
          const t = Date.now() / 140;
          const pulseR = 24 + Math.sin(t) * 7;

          // Vòng hào quang radar ngoài
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, pulseR, 0, Math.PI * 2);
          ctx.strokeStyle = "#00f2fe";
          ctx.lineWidth = 2.8;
          ctx.shadowColor = "#00f2fe";
          ctx.shadowBlur = 20;
          ctx.stroke();

          // Tâm phát sáng
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, Math.max(2, pulseR - 6), 0, Math.PI * 2);
          ctx.fillStyle = "rgba(0, 242, 254, 0.28)";
          ctx.fill();
          ctx.restore();
        }
      } catch (e) {}
    }

    if (!enablePacketWaves) return;

    // 1. Draw impact ripples
    activeRipples.forEach(rip => {
      try {
        const pos = network.getPosition(rip.nodeId);
        if (pos) {
          ctx.save();
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, rip.radius, 0, Math.PI * 2);
          ctx.strokeStyle = rip.color;
          ctx.globalAlpha = Math.max(0, rip.alpha);
          ctx.lineWidth = 2.5;
          ctx.shadowColor = rip.color;
          ctx.shadowBlur = 12;
          ctx.stroke();
          ctx.restore();
        }
      } catch (e) {}
    });

    // 2. Draw packets traveling along graph edges
    activePackets.forEach(pkt => {
      try {
        const p1 = network.getPosition(pkt.from);
        const p2 = network.getPosition(pkt.to);
        if (p1 && p2) {
          const t = Math.min(1, Math.max(0, pkt.progress));
          // Cubic ease-in-out
          const easeT = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
          const px = p1.x + (p2.x - p1.x) * easeT;
          const py = p1.y + (p2.y - p1.y) * easeT;

          ctx.save();
          ctx.shadowColor = pkt.color;
          ctx.shadowBlur = 14;

          // Glowing outer aura
          ctx.beginPath();
          ctx.arc(px, py, 6, 0, Math.PI * 2);
          ctx.fillStyle = pkt.color;
          ctx.globalAlpha = 0.5;
          ctx.fill();

          // Bright center photon
          ctx.beginPath();
          ctx.arc(px, py, 3.2, 0, Math.PI * 2);
          ctx.fillStyle = "#ffffff";
          ctx.globalAlpha = 1.0;
          ctx.fill();

          // Trailing particles
          for (let i = 1; i <= 3; i++) {
            const lagT = Math.max(0, easeT - i * 0.045);
            const lx = p1.x + (p2.x - p1.x) * lagT;
            const ly = p1.y + (p2.y - p1.y) * lagT;
            ctx.beginPath();
            ctx.arc(lx, ly, Math.max(1, 3 - i * 0.7), 0, Math.PI * 2);
            ctx.fillStyle = pkt.color;
            ctx.globalAlpha = Math.max(0, 0.4 - i * 0.1);
            ctx.fill();
          }

          ctx.restore();
        }
      } catch (e) {}
    });
  }

  // ==================== AGENT PROFILE INSPECTOR DRAWER ====================
  function openAgentInspector(nodeId) {
    if (!agentInspectorDrawer) return;
    const node = currentGraphNodes.find(n => n.id === nodeId);
    if (!node) return;

    document.getElementById("inspector-name").textContent = `Tác tử #${node.id}`;
    document.getElementById("inspector-persona").textContent = node.persona || "CHƯA RÕ";
    document.getElementById("inspector-avatar").textContent = `#${node.id}`;
    document.getElementById("inspector-avatar").style.background = getPersonaGradient(node.persona);

    const b = node.belief_score !== undefined ? node.belief_score : 0;
    document.getElementById("inspector-belief-val").textContent = (b >= 0 ? "+" : "") + b.toFixed(2);
    
    // Position the belief needle (-1.0 to +1.0 -> 0% to 100%)
    const percent = Math.min(100, Math.max(0, (b + 1) * 50));
    const fillEl = document.getElementById("inspector-belief-fill");
    if (fillEl) fillEl.style.left = `${percent}%`;

    document.getElementById("inspector-model").textContent = node.model_name || "Ollama Local";
    document.getElementById("inspector-state").textContent = node.state || "UNINFORMED";
    document.getElementById("inspector-degree").textContent = node.degree || "--";
    
    if (network) {
      const neighbors = network.getConnectedNodes(nodeId);
      document.getElementById("inspector-neighbors").textContent = neighbors.length;
      network.selectNodes([nodeId]);
    }

    // Message History
    const agentTraces = allTraces.filter(t => t.agent_id === nodeId);
    const lastTrace = agentTraces[agentTraces.length - 1];
    const msgBox = document.getElementById("inspector-last-msg");
    if (lastTrace) {
      msgBox.innerHTML = `
        <div style="font-weight:600; color:var(--accent-cyan); margin-bottom:4px;">Hop ${lastTrace.hop} • Quyết định: ${lastTrace.decision}</div>
        <div style="color:#f8fafc; font-size:11px;">"${lastTrace.outgoing_message || 'Giữ im lặng (không chia sẻ)'}"</div>
        ${lastTrace.reasoning ? `<div style="margin-top:4px; font-size:10px; color:#94a3b8;"><em>Lập luận: ${lastTrace.reasoning}</em></div>` : ''}
      `;
    } else {
      msgBox.textContent = "Chưa có phát ngôn nào được ghi nhận cho tác tử này.";
    }

    agentInspectorDrawer.style.display = "flex";
    if (window.anime) {
      anime({
        targets: agentInspectorDrawer,
        translateX: [30, 0],
        opacity: [0, 1],
        duration: 300,
        easing: "easeOutCubic"
      });
    }
  }

  function closeAgentInspector() {
    if (!agentInspectorDrawer) return;
    if (window.anime && agentInspectorDrawer.style.display !== "none") {
      anime({
        targets: agentInspectorDrawer,
        translateX: [0, 30],
        opacity: [1, 0],
        duration: 200,
        easing: "easeInCubic",
        complete: () => {
          agentInspectorDrawer.style.display = "none";
        }
      });
    } else {
      agentInspectorDrawer.style.display = "none";
    }
  }

  function getPersonaGradient(persona) {
    if (persona === "FACT_CHECKER") return "linear-gradient(135deg, #10b981, #059669)";
    if (persona === "MALICIOUS_SPREADER") return "linear-gradient(135deg, #f43f5e, #be123c)";
    if (persona === "OPINION_LEADER") return "linear-gradient(135deg, #c084fc, #7e22ce)";
    if (persona === "DOGMATIC_PARTISAN") return "linear-gradient(135deg, #f59e0b, #b45309)";
    return "linear-gradient(135deg, #38bdf8, #0284c7)";
  }

  // ==================== CANVAS TOOLBAR EVENTS ====================
  if (togglePacketWaves) {
    togglePacketWaves.addEventListener("change", (e) => {
      enablePacketWaves = e.target.checked;
      if (!enablePacketWaves) {
        activePackets = [];
        activeRipples = [];
      }
    });
  }

  if (btnFitGraph) {
    btnFitGraph.addEventListener("click", () => {
      if (network) {
        network.fit({ animation: { duration: 650, easingFunction: "easeInOutQuad" } });
      }
    });
  }

  if (btnSnapshotGraph) {
    btnSnapshotGraph.addEventListener("click", () => {
      if (!network) return;
      try {
        const canvas = networkContainer.querySelector("canvas");
        if (canvas) {
          const imageURI = canvas.toDataURL("image/png");
          const a = document.createElement("a");
          a.href = imageURI;
          a.download = `mas_diffusion_network_${Date.now()}.png`;
          a.click();
        }
      } catch (e) {
        console.error("Lỗi chụp snapshot canvas:", e);
      }
    });
  }

  if (btnCloseInspector) {
    btnCloseInspector.addEventListener("click", closeAgentInspector);
  }

  // ==================== LIVE PIPELINE TERMINAL DRAWER ====================
  function togglePipelineDrawer(show = null) {
    if (!pipelineTerminalDrawer) return;
    const isCurrentlyOpen = pipelineTerminalDrawer.style.display !== "none";
    const targetState = show !== null ? show : !isCurrentlyOpen;

    if (targetState) {
      pipelineTerminalDrawer.style.display = "flex";
      if (btnTogglePipeline) btnTogglePipeline.classList.add("active");
      if (window.anime) {
        anime({
          targets: pipelineTerminalDrawer,
          translateY: [20, 0],
          opacity: [0, 1],
          duration: 300,
          easing: "easeOutCubic"
        });
      }
    } else {
      if (btnTogglePipeline) btnTogglePipeline.classList.remove("active");
      if (window.anime && isCurrentlyOpen) {
        anime({
          targets: pipelineTerminalDrawer,
          translateY: [0, 20],
          opacity: [1, 0],
          duration: 200,
          easing: "easeInCubic",
          complete: () => {
            pipelineTerminalDrawer.style.display = "none";
          }
        });
      } else {
        pipelineTerminalDrawer.style.display = "none";
      }
    }
  }

  if (btnTogglePipeline) {
    btnTogglePipeline.addEventListener("click", () => togglePipelineDrawer());
  }

  if (btnCloseTerminal) {
    btnCloseTerminal.addEventListener("click", () => togglePipelineDrawer(false));
  }

  if (btnClearTerminal) {
    btnClearTerminal.addEventListener("click", () => {
      if (terminalBody) {
        terminalBody.innerHTML = '<div class="terminal-line info">[ĐÃ XÓA] Màn hình log đã được làm sạch.</div>';
      }
    });
  }

  // ==================== SIMULATION CONTROL ====================
  btnStep.addEventListener("click", async () => {
    btnStep.disabled = true;
    togglePipelineDrawer(true); // Tự động mở terminal để người dùng quan sát trực quan
    try {
      const res = await fetch("/api/simulation/step", { method: "POST" });
      const data = await res.json();
      if (data.finished) {
        btnStep.disabled = true;
        btnRun.disabled = true;
      } else {
        btnStep.disabled = false;
      }
    } catch (e) {
      console.error("Lỗi khi chạy step:", e);
      btnStep.disabled = false;
    }
  });

  btnRun.addEventListener("click", async () => {
    btnRun.disabled = true;
    btnStep.disabled = true;
    btnStop.disabled = false;
    togglePipelineDrawer(true); // Mở terminal cho chế độ tự động
    try {
      await fetch("/api/simulation/run_all", { method: "POST" });
    } catch (e) {
      console.error("Lỗi khi bắt đầu run_all:", e);
    }
  });

  btnStop.addEventListener("click", async () => {
    try {
      await fetch("/api/simulation/stop", { method: "POST" });
      btnStop.disabled = true;
      btnStep.disabled = false;
      btnRun.disabled = false;
      stopHopTimer();
      logToTerminal("warn", "🛑 Người dùng đã gửi lệnh DỪNG khẩn cấp quá trình mô phỏng.");
    } catch (e) {
      console.error("Lỗi khi dừng:", e);
    }
  });

  // ==================== EVENT HANDLER: HOP COMPLETED ====================
  function handleHopCompleted(result) {
    if (!result || !result.hop_summary) return;

    const summary = result.hop_summary;

    // 1. Cập nhật HUD mượt mà với Anime.js counter
    hudHop.textContent = `${summary.hop} / ${maxHopsConfig}`;
    animateHudValue(hudPenetration, lastHudValues.penetration, summary.penetration_rate, "%", 1);
    animateHudValue(hudDrift, lastHudValues.drift, summary.average_semantic_drift, "", 3);
    animateHudValue(hudPolarization, lastHudValues.polarization, summary.polarization_index, "", 3);
    hudQueue.textContent = `${summary.remaining_queue_size} tin`;

    lastHudValues.penetration = summary.penetration_rate;
    lastHudValues.drift = summary.average_semantic_drift;
    lastHudValues.polarization = summary.polarization_index;

    // 2. Cập nhật màu sắc node trên Vis.js
    if (nodesDataSet && result.updated_nodes) {
      result.updated_nodes.forEach(un => {
        const colorScheme = STATE_COLORS[un.state] || STATE_COLORS["UNINFORMED"];
        nodesDataSet.update({
          id: un.id,
          color: { background: colorScheme.background, border: colorScheme.border },
          title: `Tác tử #${un.id}\nPersona: ${un.persona}\nTrạng thái: ${un.state}\nNiềm tin: ${un.belief_score}`
        });

        // Cập nhật trạng thái trong bộ nhớ cục bộ
        const localNode = currentGraphNodes.find(n => n.id === un.id);
        if (localNode) {
          localNode.state = un.state;
          localNode.belief_score = un.belief_score;
        }
      });
    }

    // 3. Kích hoạt hiệu ứng xung sóng lan truyền (Packet Wave Engine)
    if (result.traces && result.traces.length > 0) {
      spawnPacketWaves(result.traces);
    }

    // 4. Cập nhật biểu đồ Chart.js
    appendChartData(summary.hop, summary.penetration_rate, summary.average_semantic_drift, summary.polarization_index);

    // 5. Thêm các thông điệp mới vào Live Message Feed
    if (result.traces && result.traces.length > 0) {
      const newCardElements = [];
      result.traces.forEach(trace => {
        allTraces.push(trace);
        const card = renderTraceCard(trace);
        if (card) newCardElements.push(card);
      });

      // Anime.js staggered reveal of message cards
      if (window.anime && newCardElements.length > 0) {
        anime({
          targets: newCardElements,
          translateY: [15, 0],
          opacity: [0, 1],
          duration: 350,
          delay: anime.stagger(50),
          easing: "easeOutCubic"
        });
      }
    }

    if (result.finished) {
      btnStep.disabled = true;
      btnRun.disabled = true;
      btnStop.disabled = true;
    }
  }

  function renderTraceCard(trace) {
    if (currentFilter !== "all") {
      if (currentFilter === "drift" && trace.drift_distance < 0.2) return null;
      if (currentFilter !== "drift" && trace.decision !== currentFilter) return null;
    }

    const card = document.createElement("div");
    card.className = `trace-card ${trace.decision}`;
    card.setAttribute("data-persona", trace.persona);
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `Thông điệp từ Tác tử #${trace.agent_id}`);

    card.innerHTML = `
      <div class="trace-header">
        <span class="trace-agent">Agent #${trace.agent_id} (${trace.persona.replace("_", " ")})</span>
        <span class="trace-hop-badge">Hop ${trace.hop} • ${trace.decision}</span>
      </div>
      <div class="trace-msg">${trace.outgoing_message ? `"${trace.outgoing_message}"` : '<em style="color:#64748b">Quyết định im lặng (không chia sẻ)</em>'}</div>
      <div class="trace-footer">
        <span>Niềm tin: ${trace.belief_score >= 0 ? '+' : ''}${trace.belief_score}</span>
        <span class="drift-badge">Drift: ${trace.drift_distance.toFixed(3)}</span>
      </div>
    `;

    // Click on card opens Agent Inspector
    card.addEventListener("click", () => {
      openAgentInspector(trace.agent_id);
    });

    liveMessageFeed.insertBefore(card, liveMessageFeed.firstChild);
    return card;
  }

  // Filter chips in Feed
  document.querySelectorAll(".filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      currentFilter = chip.getAttribute("data-filter");

      // Re-render feed
      liveMessageFeed.innerHTML = "";
      allTraces.forEach(renderTraceCard);
    });
  });

  // ==================== CHARTS UPDATE ====================
  function appendChartData(hop, penetration, drift, polarization) {
    chartDiffusion.data.labels.push(hop);
    chartDiffusion.data.datasets[0].data.push(penetration);
    chartDiffusion.update();

    chartDrift.data.labels.push(hop);
    chartDrift.data.datasets[0].data.push(drift);
    chartDrift.update();

    chartPolarization.data.labels.push(hop);
    chartPolarization.data.datasets[0].data.push(polarization);
    chartPolarization.update();
  }

  function resetCharts() {
    [chartDiffusion, chartDrift, chartPolarization].forEach(chart => {
      chart.data.labels = [0];
      chart.data.datasets[0].data = [0];
      chart.update();
    });
  }

  // ==================== EXPORT DATA ====================
  btnExport.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/simulation/export", { method: "POST" });
      const data = await res.json();
      alert(`Xuất dữ liệu thành công!\nCác tệp đã được lưu vào thư mục 'experiments/':\n- ${data.files.metrics_csv}\n- ${data.files.traces_csv}\n- ${data.files.json_path}`);
    } catch (e) {
      alert("Lỗi khi xuất dữ liệu: " + e.message);
    }
  });

  // ==================== MODAL & OLLAMA GUIDE ====================
  btnOllamaGuide.addEventListener("click", () => ollamaModal.classList.add("open"));
  ollamaStatusPill.addEventListener("click", () => ollamaModal.classList.add("open"));
  btnCloseModal.addEventListener("click", () => ollamaModal.classList.remove("open"));
  ollamaModal.addEventListener("click", (e) => {
    if (e.target === ollamaModal) ollamaModal.classList.remove("open");
  });

  btnRecheckOllama.addEventListener("click", async () => {
    recheckFeedback.textContent = "Đang kiểm tra lại...";
    const data = await checkSystemStatus();
    if (data && data.ollama && data.ollama.online) {
      recheckFeedback.style.color = "var(--accent-emerald)";
      recheckFeedback.textContent = "✓ Đã tìm thấy Ollama đang chạy!";
    } else {
      recheckFeedback.style.color = "var(--accent-rose)";
      recheckFeedback.textContent = "✗ Chưa phát hiện Ollama. Hãy đảm bảo app Ollama đã bật!";
    }
  });

  // Initial Boot
  checkSystemStatus();
  setupWebSocket();
});
