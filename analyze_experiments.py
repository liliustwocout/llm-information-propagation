"""
MAS-Diffusion-Lab: Script Phân tích Thống kê ANOVA & Trực quan hóa Dữ liệu Thực nghiệm
═══════════════════════════════════════════════════════════════════════════════════
Đề tài NCKH 2026: "Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm
quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)"

Mục tiêu:
  - Kiểm định 4 giả thuyết H1, H2, H3, H4 bằng phân tích phương sai ANOVA và T-test
  - Tạo các biểu đồ khoa học phục vụ bài báo (box-plot, heatmap, bar chart)
  - Xuất bảng tổng hợp thống kê mô tả (descriptive statistics)

Cách sử dụng:
  python analyze_experiments.py                          # Tự tìm file SUMMARY_*.csv mới nhất
  python analyze_experiments.py --input experiments/SUMMARY_20260926_120000.csv
  python analyze_experiments.py --input experiments/SUMMARY_*.csv --output-dir analysis_results
"""

import sys
import os
import glob
import argparse
import warnings
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Thử import matplotlib (bắt buộc cho biểu đồ)
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend cho server/headless
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[!] matplotlib chưa cài. Chạy: pip install matplotlib")

# Thử import statsmodels (cho Two-way ANOVA chính thức)
try:
    import statsmodels.api as sm
    from statsmodels.formula.api import ols
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("[!] statsmodels chưa cài. Chạy: pip install statsmodels")
    print("    Sẽ sử dụng scipy.stats (One-way ANOVA / Kruskal-Wallis) thay thế.\n")

warnings.filterwarnings("ignore", category=FutureWarning)


# ═══════════════════════════════════════════════════════════════════
# 1. Nạp và Tiền xử lý Dữ liệu
# ═══════════════════════════════════════════════════════════════════

def load_summary_data(filepath: str) -> pd.DataFrame:
    """
    Đọc file SUMMARY CSV tổng hợp từ run_experiments.py.
    """
    df = pd.read_csv(filepath)
    # Loại bỏ các phiên lỗi
    df = df[df["simulation_id"] != "ERROR"].copy()
    # Đảm bảo kiểu dữ liệu
    numeric_cols = [
        "fc_ratio", "seed", "num_nodes", "max_hops_config", "actual_hops",
        "time_seconds", "final_coverage_pct", "final_drift",
        "final_polarization", "final_R_t", "final_informed_total",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Tạo nhãn ngắn cho Topology
    topo_short = {
        "barabasi_albert": "BA",
        "watts_strogatz": "WS",
        "erdos_renyi": "ER",
        "stochastic_block_model": "SBM",
    }
    df["topo_short"] = df["topology"].map(topo_short).fillna(df["topology"])
    
    # Nhãn tỷ lệ Fact-Checker
    df["fc_label"] = df["fc_ratio"].apply(lambda x: f"{x*100:.0f}%")
    
    print(f"[✓] Đã nạp {len(df)} phiên thực nghiệm từ {filepath}")
    print(f"    Topologies: {df['topo_short'].unique().tolist()}")
    print(f"    FC Ratios : {sorted(df['fc_ratio'].unique().tolist())}")
    print(f"    Seeds     : {sorted(df['seed'].unique().tolist())}")
    print()
    return df


def find_latest_summary(experiments_dir: str = "experiments") -> Optional[str]:
    """Tìm file SUMMARY_*.csv mới nhất trong thư mục experiments."""
    pattern = os.path.join(experiments_dir, "SUMMARY_*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


# ═══════════════════════════════════════════════════════════════════
# 2. Thống kê Mô tả (Descriptive Statistics)
# ═══════════════════════════════════════════════════════════════════

def descriptive_statistics(df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """
    Tổng hợp thống kê mô tả theo nhóm (Topology × FC_Ratio × Placement).
    """
    print("═" * 70)
    print("📊 BẢNG THỐNG KÊ MÔ TẢ (Descriptive Statistics)")
    print("═" * 70)

    metrics = ["final_coverage_pct", "final_drift", "final_polarization", "final_R_t"]
    group_cols = ["topo_short", "fc_ratio", "fc_placement"]

    # Chỉ nhóm theo các cột tồn tại
    available_groups = [c for c in group_cols if c in df.columns]
    
    agg_dict = {}
    for m in metrics:
        if m in df.columns:
            agg_dict[m] = ["count", "mean", "std", "min", "max"]
    
    desc = df.groupby(available_groups).agg(agg_dict).round(4)
    desc.columns = ["_".join(col).strip() for col in desc.columns.values]
    desc = desc.reset_index()

    # Hiển thị
    print(desc.to_string(index=False))
    print()

    # Lưu ra CSV
    desc_path = os.path.join(output_dir, "descriptive_statistics.csv")
    desc.to_csv(desc_path, index=False, encoding="utf-8")
    print(f"  [+] Đã lưu: {desc_path}")
    return desc


# ═══════════════════════════════════════════════════════════════════
# 3. Kiểm định Giả thuyết (Hypothesis Testing)
# ═══════════════════════════════════════════════════════════════════

def test_H1_semantic_drift(df: pd.DataFrame, output_dir: str):
    """
    H1: Khoảng cách ngữ nghĩa cosine tăng theo số hop.
    Phân tích: So sánh final_drift giữa các kịch bản có/không có FC.
    Sử dụng Independent Samples T-test hoặc Mann-Whitney U test.
    """
    print("\n" + "═" * 70)
    print("🔬 KIỂM ĐỊNH H1: Semantic Drift tăng theo bước nhảy")
    print("═" * 70)
    
    # So sánh Drift giữa FC=0% vs FC>0%
    no_fc = df[df["fc_ratio"] == 0.0]["final_drift"].dropna()
    with_fc = df[df["fc_ratio"] > 0.0]["final_drift"].dropna()

    if len(no_fc) < 2 or len(with_fc) < 2:
        print("  [!] Không đủ dữ liệu để kiểm định H1. Cần ít nhất 2 mẫu mỗi nhóm.")
        return

    print(f"  Nhóm Không FC (n={len(no_fc)}): Mean={no_fc.mean():.4f}, Std={no_fc.std():.4f}")
    print(f"  Nhóm Có FC    (n={len(with_fc)}): Mean={with_fc.mean():.4f}, Std={with_fc.std():.4f}")

    # Kiểm tra phân phối chuẩn (Shapiro-Wilk)
    _, p_shapiro_no = stats.shapiro(no_fc) if len(no_fc) <= 50 else (0, 0.05)
    _, p_shapiro_with = stats.shapiro(with_fc) if len(with_fc) <= 50 else (0, 0.05)

    if p_shapiro_no > 0.05 and p_shapiro_with > 0.05:
        # Phân phối chuẩn → T-test
        t_stat, p_value = stats.ttest_ind(no_fc, with_fc, equal_var=False)
        test_name = "Welch's T-test"
    else:
        # Không phân phối chuẩn → Mann-Whitney U
        t_stat, p_value = stats.mannwhitneyu(no_fc, with_fc, alternative="two-sided")
        test_name = "Mann-Whitney U test"

    print(f"\n  Phương pháp: {test_name}")
    print(f"  Thống kê kiểm định: {t_stat:.4f}")
    print(f"  p-value: {p_value:.6f}")

    if p_value < 0.05:
        print(f"  ✅ KẾT LUẬN: Có sự khác biệt có ý nghĩa thống kê (p={p_value:.4f} < 0.05)")
        if no_fc.mean() > with_fc.mean():
            print("    → Fact-Checker giúp GIẢM Semantic Drift → H1 được hỗ trợ")
        else:
            print("    → Có FC nhưng Drift cao hơn → Cần phân tích sâu hơn")
    else:
        print(f"  ❌ KẾT LUẬN: Không đủ bằng chứng bác bỏ H0 (p={p_value:.4f} ≥ 0.05)")

    # So sánh Drift theo Topology (One-way ANOVA)
    print(f"\n  --- Phân tích Drift theo Topology (One-way ANOVA) ---")
    topo_groups = [group["final_drift"].dropna().values for _, group in df.groupby("topo_short")]
    topo_groups = [g for g in topo_groups if len(g) >= 2]

    if len(topo_groups) >= 2:
        f_stat, p_anova = stats.f_oneway(*topo_groups)
        print(f"  F-statistic: {f_stat:.4f}")
        print(f"  p-value: {p_anova:.6f}")
        if p_anova < 0.05:
            print(f"  ✅ Cấu trúc mạng ẢNH HƯỞNG có ý nghĩa đến Semantic Drift")
        else:
            print(f"  ❌ Chưa đủ bằng chứng về ảnh hưởng của cấu trúc mạng")


def test_H2_topology_speed(df: pd.DataFrame, output_dir: str):
    """
    H2: Mạng BA bùng phát nhanh gấp 2x so với ER.
    So sánh R(t) final và R_t giữa BA vs ER.
    """
    print("\n" + "═" * 70)
    print("🔬 KIỂM ĐỊNH H2: BA Scale-Free lan truyền nhanh hơn ER Random")
    print("═" * 70)

    ba = df[df["topo_short"] == "BA"]["final_coverage_pct"].dropna()
    er = df[df["topo_short"] == "ER"]["final_coverage_pct"].dropna()

    if len(ba) < 2 or len(er) < 2:
        print("  [!] Không đủ dữ liệu. Cần chạy thêm thực nghiệm cho BA và ER.")
        return

    print(f"  BA Coverage (n={len(ba)}): Mean={ba.mean():.2f}%, Std={ba.std():.2f}%")
    print(f"  ER Coverage (n={len(er)}): Mean={er.mean():.2f}%, Std={er.std():.2f}%")
    
    ratio = ba.mean() / er.mean() if er.mean() > 0 else float("inf")
    print(f"  Tỷ lệ BA/ER: {ratio:.2f}x")

    t_stat, p_value = stats.ttest_ind(ba, er, equal_var=False)
    print(f"\n  Welch's T-test: t={t_stat:.4f}, p={p_value:.6f}")

    if p_value < 0.05 and ba.mean() > er.mean():
        print(f"  ✅ BA lan truyền NHANH hơn ER có ý nghĩa thống kê (ratio={ratio:.2f}x)")
        if ratio >= 2.0:
            print("    → H2 ĐƯỢC XÁC NHẬN: BA nhanh ≥ 2x so với ER")
        else:
            print(f"    → H2 BÁN XÁC NHẬN: BA nhanh hơn nhưng chưa đạt 2x (chỉ {ratio:.2f}x)")
    else:
        print(f"  ❌ Chưa đủ bằng chứng xác nhận H2 (p={p_value:.4f})")

    # So sánh R_t giữa 4 Topo
    print(f"\n  --- So sánh R_t ban đầu giữa các Topology ---")
    for topo in ["BA", "WS", "ER", "SBM"]:
        subset = df[df["topo_short"] == topo]["final_R_t"].dropna()
        if len(subset) > 0:
            print(f"    {topo}: R_t = {subset.mean():.3f} ± {subset.std():.3f} (n={len(subset)})")


def test_H3_cloud_anchors(df: pd.DataFrame, output_dir: str):
    """
    H3: Mô hình Cloud tại Hub giúp giảm Drift 40%.
    Lưu ý: Giả thuyết này yêu cầu dữ liệu từ thực nghiệm có cloud_ratio > 0.
    Nếu chưa có, in hướng dẫn cách chạy.
    """
    print("\n" + "═" * 70)
    print("🔬 KIỂM ĐỊNH H3: Cloud Models làm 'mỏ neo nhận thức' giảm Drift")
    print("═" * 70)

    if "model" in df.columns:
        models = df["model"].unique()
        if len(models) <= 1:
            print(f"  [!] Chỉ có 1 loại model: {models}")
            print("  → H3 yêu cầu chạy thực nghiệm bổ sung với cloud_ratio > 0")
            print("  → Gợi ý: Sửa run_experiments.py thêm cloud_ratio=0.15 vào config")
            print("  → Hoặc so sánh giữa qwen2.5:3b vs llama3:8b (proxy test)")
            return

    print("  [!] Chưa có dữ liệu Cloud vs Local. Bỏ qua kiểm định H3.")
    print("  → Cần bổ sung thực nghiệm với tham số cloud_ratio > 0")


def test_H4_placement_strategy(df: pd.DataFrame, output_dir: str):
    """
    H4: Fact-Checker tại Bridge hiệu quả hơn Random.
    So sánh final_coverage_pct giữa các chiến lược placement khi FC > 0.
    """
    print("\n" + "═" * 70)
    print("🔬 KIỂM ĐỊNH H4: Placement tại Bridge tốt hơn Random")
    print("═" * 70)

    df_fc = df[df["fc_ratio"] > 0].copy()
    if len(df_fc) < 4:
        print("  [!] Không đủ dữ liệu FC > 0. Cần chạy thêm thực nghiệm.")
        return

    placements = df_fc["fc_placement"].unique()
    print(f"  Các chiến lược placement: {placements.tolist()}")

    # So sánh Coverage giữa các Placement
    for placement in placements:
        subset = df_fc[df_fc["fc_placement"] == placement]
        cov = subset["final_coverage_pct"].dropna()
        drift = subset["final_drift"].dropna()
        print(f"\n  [{placement}] (n={len(subset)}):")
        print(f"    Coverage R(t): {cov.mean():.2f}% ± {cov.std():.2f}%")
        print(f"    Drift:         {drift.mean():.4f} ± {drift.std():.4f}")

    # So sánh thống kê giữa BRIDGE vs RANDOM (nếu có đủ dữ liệu)
    bridge = df_fc[df_fc["fc_placement"] == "BRIDGE_BETWEENNESS"]["final_coverage_pct"].dropna()
    random_pl = df_fc[df_fc["fc_placement"] == "RANDOM"]["final_coverage_pct"].dropna()

    if len(bridge) >= 2 and len(random_pl) >= 2:
        t_stat, p_value = stats.ttest_ind(bridge, random_pl, equal_var=False)
        print(f"\n  Bridge vs Random — Welch's T-test:")
        print(f"    t-statistic: {t_stat:.4f}")
        print(f"    p-value: {p_value:.6f}")
        if p_value < 0.05:
            if bridge.mean() < random_pl.mean():
                print(f"    ✅ Bridge placement KIỀM CHẾ lan truyền tốt hơn Random → H4 xác nhận")
            else:
                print(f"    ⚠ Bridge có Coverage CAO hơn Random → Cần xem xét lại H4")
        else:
            print(f"    ❌ Chưa đủ bằng chứng phân biệt Bridge vs Random (p ≥ 0.05)")

    # Hub vs Bridge
    hub = df_fc[df_fc["fc_placement"] == "HUB_DEGREE"]["final_coverage_pct"].dropna()
    if len(hub) >= 2 and len(bridge) >= 2:
        t_stat2, p_val2 = stats.ttest_ind(hub, bridge, equal_var=False)
        print(f"\n  Hub vs Bridge — Welch's T-test:")
        print(f"    Hub Coverage:    {hub.mean():.2f}% ± {hub.std():.2f}%")
        print(f"    Bridge Coverage: {bridge.mean():.2f}% ± {bridge.std():.2f}%")
        print(f"    t={t_stat2:.4f}, p={p_val2:.6f}")


def test_twoway_anova(df: pd.DataFrame, output_dir: str):
    """
    Two-way ANOVA: Topo × FC_Ratio → final_coverage_pct
    Yêu cầu statsmodels. Nếu không có, dùng scipy thay thế.
    """
    print("\n" + "═" * 70)
    print("🔬 TWO-WAY ANOVA: Topology × FC_Ratio → Coverage R(t)")
    print("═" * 70)

    if not HAS_STATSMODELS:
        print("  [!] statsmodels chưa cài. Chạy: pip install statsmodels")
        print("  → Đang dùng One-way ANOVA (scipy) thay thế...")
        
        # Fallback: One-way ANOVA cho từng yếu tố
        for factor, col in [("Topology", "topo_short"), ("FC_Ratio", "fc_label")]:
            groups = [g["final_coverage_pct"].dropna().values for _, g in df.groupby(col)]
            groups = [g for g in groups if len(g) >= 2]
            if len(groups) >= 2:
                f_stat, p_val = stats.f_oneway(*groups)
                print(f"  One-way ANOVA ({factor}): F={f_stat:.4f}, p={p_val:.6f}")
            else:
                print(f"  One-way ANOVA ({factor}): Không đủ nhóm dữ liệu.")
        return

    # Two-way ANOVA chính thức với statsmodels
    df_anova = df[["topo_short", "fc_ratio", "final_coverage_pct"]].dropna().copy()
    df_anova["fc_ratio"] = df_anova["fc_ratio"].astype(str)

    if len(df_anova) < 10:
        print("  [!] Không đủ dữ liệu cho Two-way ANOVA (cần ≥ 10 quan sát).")
        return

    try:
        model = ols("final_coverage_pct ~ C(topo_short) * C(fc_ratio)", data=df_anova).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        print("\n  BẢNG ANOVA (Type II):")
        print(anova_table.to_string())

        # Kiểm tra ý nghĩa
        print("\n  Diễn giải:")
        for src in anova_table.index:
            if src == "Residual":
                continue
            p = anova_table.loc[src, "PR(>F)"]
            sig = "✅ CÓ" if p < 0.05 else "❌ KHÔNG"
            print(f"    {src}: p={p:.6f} → {sig} ý nghĩa thống kê")

        # Post-hoc Tukey HSD cho Topology
        print("\n  --- Post-hoc Tukey HSD (Topology) ---")
        try:
            tukey = pairwise_tukeyhsd(
                df_anova["final_coverage_pct"],
                df_anova["topo_short"],
                alpha=0.05,
            )
            print(tukey.summary())
        except Exception as e:
            print(f"  [!] Không thể chạy Tukey HSD: {e}")

    except Exception as e:
        print(f"  [!] Lỗi khi chạy Two-way ANOVA: {e}")


# ═══════════════════════════════════════════════════════════════════
# 4. Trực quan hóa Dữ liệu (Data Visualization)
# ═══════════════════════════════════════════════════════════════════

def plot_coverage_by_topology(df: pd.DataFrame, output_dir: str):
    """Box-plot: Coverage R(t) phân theo Topology."""
    if not HAS_MATPLOTLIB:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    
    topos = sorted(df["topo_short"].unique())
    data = [df[df["topo_short"] == t]["final_coverage_pct"].dropna().values for t in topos]
    
    bp = ax.boxplot(data, labels=topos, patch_artist=True, widths=0.6)
    colors = ["#4FC3F7", "#81C784", "#FFB74D", "#E57373"]
    for patch, color in zip(bp["boxes"], colors[:len(topos)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel("Topology", fontsize=12, fontweight="bold")
    ax.set_ylabel("Coverage R(t) %", fontsize=12, fontweight="bold")
    ax.set_title("Tỷ lệ bao phủ R(t) theo Cấu trúc mạng", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    
    path = os.path.join(output_dir, "boxplot_coverage_by_topology.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Biểu đồ: {path}")


def plot_drift_by_fc_ratio(df: pd.DataFrame, output_dir: str):
    """Bar-chart: Semantic Drift theo tỷ lệ Fact-Checker."""
    if not HAS_MATPLOTLIB:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    fc_labels = sorted(df["fc_ratio"].unique())
    means = [df[df["fc_ratio"] == r]["final_drift"].mean() for r in fc_labels]
    stds = [df[df["fc_ratio"] == r]["final_drift"].std() for r in fc_labels]
    
    x_labels = [f"{r*100:.0f}%" for r in fc_labels]
    bars = ax.bar(x_labels, means, yerr=stds, capsize=5, color=["#E57373", "#FFB74D", "#81C784"],
                  edgecolor="white", linewidth=1.5, alpha=0.85)

    ax.set_xlabel("Tỷ lệ Fact-Checker", fontsize=12, fontweight="bold")
    ax.set_ylabel("Semantic Drift (1 - Cosine Similarity)", fontsize=12, fontweight="bold")
    ax.set_title("Độ biến dạng ngữ nghĩa theo Tỷ lệ Fact-Checker", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    # Ghi giá trị trên cột
    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f"{m:.4f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    path = os.path.join(output_dir, "barchart_drift_by_fc_ratio.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Biểu đồ: {path}")


def plot_polarization_heatmap(df: pd.DataFrame, output_dir: str):
    """Heatmap: Polarization Index theo Topology × FC_Ratio."""
    if not HAS_MATPLOTLIB:
        return

    pivot = df.pivot_table(
        values="final_polarization",
        index="topo_short",
        columns="fc_label",
        aggfunc="mean",
    )

    if pivot.empty:
        print("  [!] Không đủ dữ liệu cho heatmap Polarization.")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    # Ghi giá trị vào ô
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                        color="white" if val > pivot.values.max() * 0.6 else "black",
                        fontsize=11, fontweight="bold")

    ax.set_xlabel("Tỷ lệ Fact-Checker", fontsize=12, fontweight="bold")
    ax.set_ylabel("Topology", fontsize=12, fontweight="bold")
    ax.set_title("Chỉ số Phân cực PI(t) — Topology × FC Ratio", fontsize=14, fontweight="bold")

    fig.colorbar(im, ax=ax, label="Polarization Index")

    path = os.path.join(output_dir, "heatmap_polarization.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Biểu đồ: {path}")


def plot_placement_comparison(df: pd.DataFrame, output_dir: str):
    """Grouped bar-chart: So sánh chiến lược Placement (H4)."""
    if not HAS_MATPLOTLIB:
        return

    df_fc = df[df["fc_ratio"] > 0].copy()
    if df_fc.empty:
        return

    placements = sorted(df_fc["fc_placement"].unique())
    if len(placements) < 2:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Subplot 1: Coverage
    cov_means = [df_fc[df_fc["fc_placement"] == p]["final_coverage_pct"].mean() for p in placements]
    cov_stds = [df_fc[df_fc["fc_placement"] == p]["final_coverage_pct"].std() for p in placements]
    colors = ["#4FC3F7", "#81C784", "#FFB74D"]
    axes[0].bar(placements, cov_means, yerr=cov_stds, capsize=5,
                color=colors[:len(placements)], edgecolor="white", linewidth=1.5, alpha=0.85)
    axes[0].set_ylabel("Coverage R(t) %", fontsize=11, fontweight="bold")
    axes[0].set_title("Bao phủ theo Placement", fontsize=13, fontweight="bold")
    axes[0].grid(axis="y", alpha=0.3)

    # Subplot 2: Drift
    drift_means = [df_fc[df_fc["fc_placement"] == p]["final_drift"].mean() for p in placements]
    drift_stds = [df_fc[df_fc["fc_placement"] == p]["final_drift"].std() for p in placements]
    axes[1].bar(placements, drift_means, yerr=drift_stds, capsize=5,
                color=colors[:len(placements)], edgecolor="white", linewidth=1.5, alpha=0.85)
    axes[1].set_ylabel("Semantic Drift", fontsize=11, fontweight="bold")
    axes[1].set_title("Drift theo Placement", fontsize=13, fontweight="bold")
    axes[1].grid(axis="y", alpha=0.3)

    fig.suptitle("So sánh Chiến lược Bố trí Fact-Checker (H4)", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    path = os.path.join(output_dir, "placement_comparison.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Biểu đồ: {path}")


def plot_reproduction_rate_by_topology(df: pd.DataFrame, output_dir: str):
    """Box-plot: Hệ số lây nhiễm R_t theo Topology (H2)."""
    if not HAS_MATPLOTLIB:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    topos = sorted(df["topo_short"].unique())
    data = [df[df["topo_short"] == t]["final_R_t"].dropna().values for t in topos]

    bp = ax.boxplot(data, labels=topos, patch_artist=True, widths=0.6)
    colors = ["#4FC3F7", "#81C784", "#FFB74D", "#E57373"]
    for patch, color in zip(bp["boxes"], colors[:len(topos)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, label="R_t = 1 (Ngưỡng dịch)")
    ax.set_xlabel("Topology", fontsize=12, fontweight="bold")
    ax.set_ylabel("Reproduction Rate R_t", fontsize=12, fontweight="bold")
    ax.set_title("Hệ số Lây nhiễm Hiệu dụng R_t theo Topology", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(output_dir, "boxplot_Rt_by_topology.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Biểu đồ: {path}")


# ═══════════════════════════════════════════════════════════════════
# 5. Main Entry Point
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MAS-Diffusion-Lab: Phân tích thống kê ANOVA và trực quan hóa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python analyze_experiments.py
  python analyze_experiments.py --input experiments/SUMMARY_20260926_120000.csv
  python analyze_experiments.py --output-dir analysis_results
        """,
    )
    parser.add_argument(
        "--input", type=str, default=None,
        help="Đường dẫn tới file SUMMARY_*.csv. Mặc định: tự tìm file mới nhất.",
    )
    parser.add_argument(
        "--output-dir", type=str, default="experiments/analysis",
        help="Thư mục lưu kết quả phân tích (mặc định: experiments/analysis)",
    )
    args = parser.parse_args()

    # Tìm file dữ liệu
    if args.input:
        input_path = args.input
    else:
        input_path = find_latest_summary()
        if not input_path:
            print("╔══════════════════════════════════════════════════════════╗")
            print("║  [!] KHÔNG TÌM THẤY FILE SUMMARY_*.csv                 ║")
            print("║                                                         ║")
            print("║  Vui lòng chạy thực nghiệm trước:                      ║")
            print("║  python run_experiments.py --mode full --seeds 42 43 44  ║")
            print("╚══════════════════════════════════════════════════════════╝")
            sys.exit(1)

    if not os.path.exists(input_path):
        print(f"[!] File không tồn tại: {input_path}")
        sys.exit(1)

    # Tạo thư mục output
    os.makedirs(args.output_dir, exist_ok=True)

    # Nạp dữ liệu
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  MAS-Diffusion-Lab — Statistical Analysis Engine        ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    df = load_summary_data(input_path)

    if len(df) == 0:
        print("[!] Không có dữ liệu hợp lệ. Vui lòng kiểm tra file CSV.")
        sys.exit(1)

    # ── 1. Thống kê mô tả ──
    descriptive_statistics(df, args.output_dir)

    # ── 2. Kiểm định giả thuyết ──
    test_H1_semantic_drift(df, args.output_dir)
    test_H2_topology_speed(df, args.output_dir)
    test_H3_cloud_anchors(df, args.output_dir)
    test_H4_placement_strategy(df, args.output_dir)

    # ── 3. Two-way ANOVA ──
    test_twoway_anova(df, args.output_dir)

    # ── 4. Trực quan hóa ──
    print("\n" + "═" * 70)
    print("📊 TRỰC QUAN HÓA DỮ LIỆU (Exporting Charts)")
    print("═" * 70)

    if HAS_MATPLOTLIB:
        plot_coverage_by_topology(df, args.output_dir)
        plot_drift_by_fc_ratio(df, args.output_dir)
        plot_polarization_heatmap(df, args.output_dir)
        plot_placement_comparison(df, args.output_dir)
        plot_reproduction_rate_by_topology(df, args.output_dir)
    else:
        print("  [!] Bỏ qua biểu đồ vì thiếu matplotlib.")

    # ── Tổng kết ──
    print(f"\n{'═'*70}")
    print(f"✅ PHÂN TÍCH HOÀN TẤT")
    print(f"{'═'*70}")
    print(f"  📁 Kết quả lưu tại: {args.output_dir}/")
    print(f"  📊 Số phiên phân tích: {len(df)}")
    print(f"  📈 Biểu đồ: {'Có' if HAS_MATPLOTLIB else 'Không (thiếu matplotlib)'}")
    print(f"  📐 ANOVA: {'statsmodels (Two-way)' if HAS_STATSMODELS else 'scipy (One-way fallback)'}")


if __name__ == "__main__":
    main()
