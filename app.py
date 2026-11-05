import streamlit as st
import math

# ============================================================
# APP CONFIG
# ============================================================
APP_VERSION = "V0.2 — RFQ Calibrated"

st.set_page_config(
    page_title=f"Tray Layout Optimizer {APP_VERSION}",
    layout="wide",
)

st.title("🛠️ NPI Tray Design Layout Optimizer (Capacity First)")
st.caption(
    f"{APP_VERSION} • RFQ concept screening • "
    "Pure Product → Pocket Clearance → Draft Expansion → Inter-Pocket Web"
)
st.write(
    "ระบบคัดเลือก Layout ที่เน้นจำนวน Slot สูงสุด ภายใต้เงื่อนไขที่เหมาะกับ RFQ "
    "โดยแยก Product Clearance, Draft และ Web ระหว่างช่องออกจากกัน"
)

# ============================================================
# SIDEBAR — INPUT PARAMETERS
# ============================================================
st.sidebar.header("1. Product Dimensions (mm)")
p_w = st.sidebar.number_input(
    "Product Width (W)",
    min_value=0.1,
    value=314.0,
    step=1.0,
)
p_l = st.sidebar.number_input(
    "Product Length (L)",
    min_value=0.1,
    value=60.0,
    step=1.0,
)
p_h = st.sidebar.number_input(
    "Product Height (H)",
    min_value=0.1,
    value=15.0,
    step=1.0,
)

force_horizontal = st.sidebar.checkbox(
    "⚠️ Force Horizontal (H-up) for Heavy/Large Components",
    value=False,
    help=(
        "เมื่อเปิด จะพิจารณาเฉพาะ orientation ที่ Original H เป็น Up-axis "
        "เหมาะกับชิ้นงานที่ห้ามตั้งขอบเพราะ component, CG, handling หรือ customer requirement"
    ),
)

st.sidebar.header("2. Tray Specification (mm)")
overall_w = st.sidebar.number_input(
    "Tray Overall Width",
    min_value=1.0,
    value=375.0,
    step=1.0,
)
overall_l = st.sidebar.number_input(
    "Tray Overall Length",
    min_value=1.0,
    value=260.0,
    step=1.0,
)
tray_margin = st.sidebar.number_input(
    "Tray Edge Margin / Stacking Shoulder",
    min_value=0.0,
    value=5.0,
    step=0.5,
    help=(
        "ระยะขอบที่กันไว้จาก Overall Tray ก่อนเริ่มพื้นที่ cavity layout "
        "Default 5 mm สำหรับ RFQ concept; ถ้า tray supplier / stacking feature ต้องการมากกว่านี้ให้เพิ่มภายหลัง"
    ),
)

# ============================================================
# ENGINEERING CLEARANCES
# ============================================================
st.sidebar.header("3. Engineering Clearances")

c_wide = st.sidebar.slider(
    "Wide Plane Clearance (>=30mm) — TOTAL",
    min_value=0.0,
    max_value=20.0,
    value=6.0,
    step=0.5,
    help=(
        "Default RFQ = 6 mm total ≈ 3 mm/side. "
        "เป็น Pocket/Cavity fit clearance ไม่ใช่ ESD bag thickness"
    ),
)

c_narrow = st.sidebar.slider(
    "Narrow Plane Clearance (<30mm) — TOTAL",
    min_value=0.0,
    max_value=20.0,
    value=4.0,
    step=0.5,
    help=(
        "Default RFQ = 4 mm total ≈ 2 mm/side. "
        "เหมาะกับ thin edge ของ PCBA / plate-like part ที่วางลง tray โดยตรง"
    ),
)

c_h_depth = st.sidebar.number_input(
    "Vertical Headroom / Safety Margin",
    min_value=0.0,
    max_value=30.0,
    value=5.0,
    step=0.5,
    help=(
        "Default RFQ = +5 mm เหนือ Product Height. "
        "ค่าเดิม +12 mm ค่อนข้าง conservative และทำให้ Draft Expansion เพิ่มตามไปด้วย"
    ),
)

handling = st.sidebar.radio(
    "Assembly Handling Method",
    [
        "Manual — Finger Access / Notch may be required",
        "Automation — Robotic / Vacuum",
    ],
    index=0,
    help=(
        "V0.2 ไม่บวกพื้นที่ finger access เข้าไปทุกช่อง เพราะ finger notch เป็น local feature. "
        "Manual mode จะใช้เป็น engineering note ไม่ใช่ลด capacity โดยอัตโนมัติ"
    ),
)

# ============================================================
# DFM / MATERIAL LIMITS
# ============================================================
st.sidebar.header("4. DFM & Material Limits")

base_web_clearance = st.sidebar.number_input(
    "Minimum Web Between Pocket Openings",
    min_value=0.0,
    max_value=30.0,
    value=6.0,
    step=0.5,
    help=(
        "Default RFQ = 6 mm ระหว่าง top opening ของ cavity ที่ติดกัน. "
        "ต้องยืนยันอีกครั้งกับ material / forming process / supplier เมื่อออก detailed design"
    ),
)

dynamic_web_factor = st.sidebar.slider(
    "Dynamic Web Factor",
    min_value=0.0,
    max_value=3.0,
    value=1.0,
    step=0.25,
    help=(
        "เพิ่ม web ตาม Pocket Depth Index. "
        "Default ลดจาก 1.5 → 1.0 เพื่อไม่ให้ RFQ concept conservative เกินไป"
    ),
)

max_depth_ratio = st.sidebar.slider(
    "Max Pocket Depth Index (RFQ Screen)",
    min_value=1.0,
    max_value=5.0,
    value=2.5,
    step=0.1,
    help=(
        "เป็น heuristic สำหรับ concept screening เท่านั้น ไม่ใช่ thermoforming draw ratio มาตรฐานสากล. "
        "Final DFM ต้อง confirm กับ material, thickness, forming process และ supplier"
    ),
)

max_material_limit = st.sidebar.number_input(
    "Max Tray Pocket / Material Height",
    min_value=1.0,
    value=85.0,
    step=1.0,
)

draft_angle = st.sidebar.number_input(
    "Draft Angle (Degrees)",
    min_value=0.0,
    max_value=15.0,
    value=3.0,
    step=0.5,
    help="Default 3° สำหรับ RFQ concept. Final draft angle ให้ supplier/DFM confirm อีกครั้ง",
)

# ============================================================
# CALCULATION HELPERS
# ============================================================
def floor_count_with_internal_web(usable_span, pocket_span, min_web):
    """
    Count cavities when:
      required span = N*pocket + (N-1)*web

    Edge margin is handled separately by tray_margin, so we must NOT add
    another full web before the first pocket and after the last pocket.

    Rearranged:
      N <= (usable + web) / (pocket + web)
    """
    if usable_span <= 0 or pocket_span <= 0:
        return 0

    denom = pocket_span + min_web
    if denom <= 0:
        return 0

    return max(0, math.floor((usable_span + min_web + 1e-9) / denom))


def centered_grid_geometry(usable_span, pocket_span, count, min_web):
    """
    Preserve the requested internal web and center the whole cavity array.
    Returns:
      used_span, edge_free_each_side, actual_internal_web
    """
    if count <= 0:
        return 0.0, 0.0, 0.0

    used = count * pocket_span + max(0, count - 1) * min_web
    free = max(0.0, usable_span - used)
    edge_free = free / 2.0

    return used, edge_free, min_web


def calculate_layout_params(pw_used, pl_used, ph_used, orientation_name):
    # --------------------------------------------------------
    # 1) PURE PRODUCT → BOTTOM POCKET ENVELOPE
    # --------------------------------------------------------
    clearance_w = c_wide if pw_used >= 30.0 else c_narrow
    clearance_l = c_wide if pl_used >= 30.0 else c_narrow

    pocket_bottom_w = pw_used + clearance_w
    pocket_bottom_l = pl_used + clearance_l

    # --------------------------------------------------------
    # 2) POCKET DEPTH / HEADROOM
    # --------------------------------------------------------
    slot_h = ph_used + c_h_depth

    # --------------------------------------------------------
    # 3) DRAFT EXPANSION
    # Top opening expands from the bottom pocket envelope.
    # --------------------------------------------------------
    draft_each_side = slot_h * math.tan(math.radians(draft_angle))
    draft_expansion_total = 2.0 * draft_each_side

    slot_w = pocket_bottom_w + draft_expansion_total
    slot_l = pocket_bottom_l + draft_expansion_total

    # --------------------------------------------------------
    # 4) RFQ POCKET DEPTH INDEX
    # Use BOTTOM pocket plane, not the draft-expanded top opening.
    # --------------------------------------------------------
    min_bottom_plane = min(pocket_bottom_w, pocket_bottom_l)
    current_ratio = (
        slot_h / min_bottom_plane
        if min_bottom_plane > 0
        else float("inf")
    )

    # --------------------------------------------------------
    # 5) INTER-POCKET WEB
    # This web exists BETWEEN cavities only.
    # Do not double-count edge web because tray_margin already reserves edge area.
    # --------------------------------------------------------
    req_web = base_web_clearance + (current_ratio * dynamic_web_factor)

    # RFQ guard against pathological zero web.
    req_web = max(3.0, req_web)

    # Manual finger access is treated as LOCAL geometry, not a global pitch penalty.
    handling_note = (
        "Manual: add local finger notch/access feature during detailed design"
        if "Manual" in handling
        else "Automation: confirm robot/vacuum access and pick tolerance"
    )

    # --------------------------------------------------------
    # 6) USABLE TRAY AREA
    # --------------------------------------------------------
    usable_w = overall_w - (2.0 * tray_margin)
    usable_l = overall_l - (2.0 * tray_margin)

    # Correct cavity count:
    # N*pocket + (N-1)*web <= usable_span
    slots_nw = floor_count_with_internal_web(
        usable_w,
        slot_w,
        req_web,
    )
    slots_nl = floor_count_with_internal_web(
        usable_l,
        slot_l,
        req_web,
    )

    total_slots = slots_nw * slots_nl

    used_w, edge_free_w, actual_web_w = centered_grid_geometry(
        usable_w,
        slot_w,
        slots_nw,
        req_web,
    )
    used_l, edge_free_l, actual_web_l = centered_grid_geometry(
        usable_l,
        slot_l,
        slots_nl,
        req_web,
    )

    # --------------------------------------------------------
    # 7) DFM / RFQ SCREENING
    # --------------------------------------------------------
    is_material_feasible = slot_h <= max_material_limit
    is_ratio_pass = current_ratio <= max_depth_ratio
    is_single_row = (
        total_slots > 0
        and (slots_nw == 1 or slots_nl == 1)
    )

    if total_slots == 0:
        status = "❌ DOES NOT FIT"
        score = 0
        note = "Pocket opening exceeds usable tray area"

    elif not is_material_feasible:
        status = "❌ MATERIAL / HEIGHT LIMIT"
        score = 0
        note = (
            f"Pocket depth {slot_h:.1f} mm > "
            f"limit {max_material_limit:.1f} mm"
        )

    elif is_ratio_pass:
        status = "✅ RFQ FEASIBLE"
        score = 3
        note = f"Concept-fit pass • {handling_note}"

    elif is_single_row:
        status = "⚠️ RFQ WARNING"
        score = 2
        note = (
            f"Pocket depth index {current_ratio:.2f} > "
            f"{max_depth_ratio:.2f}; rib/formed support or supplier review required"
        )

    else:
        status = "❌ DFM SCREEN FAIL"
        score = 1
        note = (
            f"Pocket depth index {current_ratio:.2f} > "
            f"{max_depth_ratio:.2f}; too deep for current RFQ assumption"
        )

    return {
        "NAME": orientation_name,
        "PW": pw_used,
        "PL": pl_used,
        "PH": ph_used,

        "CLEAR_W": clearance_w,
        "CLEAR_L": clearance_l,

        "BOTTOM_W": pocket_bottom_w,
        "BOTTOM_L": pocket_bottom_l,

        "SW": slot_w,
        "SL": slot_l,
        "SH": slot_h,

        "DRAFT_EACH_SIDE": draft_each_side,
        "DRAFT_TOTAL": draft_expansion_total,

        "NW": slots_nw,
        "NL": slots_nl,
        "TOTAL": total_slots,

        "USABLE_W": usable_w,
        "USABLE_L": usable_l,
        "USED_W": used_w,
        "USED_L": used_l,

        "EDGE_FREE_W": edge_free_w,
        "EDGE_FREE_L": edge_free_l,

        "WEB_W": actual_web_w,
        "WEB_L": actual_web_l,
        "REQ_PITCH": req_web,

        "STATUS": status,
        "NOTE": note,
        "RATIO": current_ratio,
        "SCORE": score,
    }


# ============================================================
# RUN 6-WAY ORIENTATION ANALYSIS
# ============================================================
dims = [p_w, p_l, p_h]
dim_names = ["W", "L", "H"]

results = []
case_idx = 1

for i in range(3):
    h_val = dims[i]
    h_nm = dim_names[i]

    if force_horizontal and h_nm != "H":
        continue

    rem_dims = [dims[j] for j in range(3) if j != i]
    rem_nms = [dim_names[j] for j in range(3) if j != i]

    results.append(
        calculate_layout_params(
            rem_dims[0],
            rem_dims[1],
            h_val,
            f"Case {case_idx}: {rem_nms[0]} × {rem_nms[1]} × {h_nm} (Up)",
        )
    )
    case_idx += 1

    results.append(
        calculate_layout_params(
            rem_dims[1],
            rem_dims[0],
            h_val,
            f"Case {case_idx}: {rem_nms[1]} × {rem_nms[0]} × {h_nm} (Up)",
        )
    )
    case_idx += 1


# Remove exact duplicate geometries generated by equal product dimensions.
deduped = {}
for r in results:
    key = (
        round(r["SW"], 4),
        round(r["SL"], 4),
        round(r["SH"], 4),
        r["NW"],
        r["NL"],
        r["SCORE"],
    )
    if key not in deduped:
        deduped[key] = r

results = list(deduped.values())

# Capacity first.
# On equal capacity:
#   1) better DFM score
#   2) lower pocket depth index
#   3) more residual edge margin
practical_results = sorted(
    [r for r in results if r["SCORE"] >= 2],
    key=lambda x: (
        x["TOTAL"],
        x["SCORE"],
        -x["RATIO"],
        min(x["EDGE_FREE_W"], x["EDGE_FREE_L"]),
    ),
    reverse=True,
)

results.sort(
    key=lambda x: (
        x["SCORE"],
        x["TOTAL"],
        -x["RATIO"],
    ),
    reverse=True,
)


# ============================================================
# SVG PLOTTING
# ============================================================
def generate_svg_tray(res):
    color = (
        "#16a34a"
        if res["SCORE"] == 3
        else "#ca8a04"
        if res["SCORE"] == 2
        else "#ef4444"
    )

    svg = (
        f'<svg width="100%" height="auto" '
        f'viewBox="0 0 {overall_w} {overall_l}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background-color:white;border:3px solid {color};'
        f'border-radius:8px;">'
    )

    # Overall tray.
    svg += (
        f'<rect x="0" y="0" width="{overall_w}" height="{overall_l}" '
        f'fill="#ffffff" stroke="{color}" stroke-width="4" />'
    )

    # Usable layout boundary.
    svg += (
        f'<rect x="{tray_margin}" y="{tray_margin}" '
        f'width="{res["USABLE_W"]}" height="{res["USABLE_L"]}" '
        f'fill="#f8fafc" stroke="#64748b" stroke-width="1.5" '
        f'stroke-dasharray="5,5" />'
    )

    if res["TOTAL"] > 0:
        start_x = tray_margin + res["EDGE_FREE_W"]
        start_y = tray_margin + res["EDGE_FREE_L"]

        for i in range(res["NW"]):
            for j in range(res["NL"]):
                x = start_x + i * (res["SW"] + res["WEB_W"])
                y = start_y + j * (res["SL"] + res["WEB_L"])

                # Draft-expanded top opening.
                svg += (
                    f'<rect x="{x}" y="{y}" '
                    f'width="{res["SW"]}" height="{res["SL"]}" '
                    f'fill="#f3f4f6" stroke="#6b7280" '
                    f'stroke-width="0.9" rx="1" />'
                )

                # Bottom pocket / product-clearance envelope.
                inset = res["DRAFT_EACH_SIDE"]
                inner_w = max(0.1, res["SW"] - 2.0 * inset)
                inner_l = max(0.1, res["SL"] - 2.0 * inset)

                svg += (
                    f'<rect x="{x + inset}" y="{y + inset}" '
                    f'width="{inner_w}" height="{inner_l}" '
                    f'fill="#dbeafe" fill-opacity="0.35" '
                    f'stroke="#2563eb" stroke-width="0.7" '
                    f'stroke-dasharray="3,2" rx="1" />'
                )

    svg += "</svg>"
    return svg


# ============================================================
# RFQ ASSUMPTION SUMMARY
# ============================================================
st.info(
    "**RFQ-Calibrated defaults:** "
    f"Wide clearance = {c_wide:.1f} mm total • "
    f"Narrow clearance = {c_narrow:.1f} mm total • "
    f"Vertical headroom = {c_h_depth:.1f} mm • "
    f"Base web = {base_web_clearance:.1f} mm • "
    f"Draft = {draft_angle:.1f}°. "
    "These are concept-screening assumptions, not final supplier DFM values."
)

st.caption(
    "Important V0.2 change: Tray Edge Margin is reserved only at the outer tray boundary. "
    "Minimum Web is counted only BETWEEN adjacent cavity openings. "
    "This avoids the previous double-counting that could unnecessarily remove one row/column."
)

# ============================================================
# DISPLAY — BEST / ALTERNATIVE
# ============================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🥇 Best Capacity Option")

    if practical_results:
        best = practical_results[0]

        st.markdown(f"### {best['STATUS']}")
        st.write(f"**{best['NAME']}**")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Slots", f"{best['TOTAL']} pcs")
        m2.metric("Layout", f"{best['NW']} × {best['NL']}")
        m3.metric("Pocket Depth", f"{best['SH']:.1f} mm")
        m4.metric("Depth Index", f"{best['RATIO']:.2f}")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric(
            "Pocket Bottom",
            f"{best['BOTTOM_W']:.1f} × {best['BOTTOM_L']:.1f}",
        )
        s2.metric(
            "Top Opening",
            f"{best['SW']:.1f} × {best['SL']:.1f}",
        )
        s3.metric("Min Web", f"{best['REQ_PITCH']:.1f} mm")
        s4.metric(
            "Residual Edge",
            f"{min(best['EDGE_FREE_W'], best['EDGE_FREE_L']):.1f} mm",
        )

        st.write(generate_svg_tray(best), unsafe_allow_html=True)
        st.caption(best["NOTE"])

    else:
        st.error("ไม่มีรูปแบบการวางที่ผ่าน RFQ / DFM screening")


with col2:
    st.subheader("🥈 Alternative Option")

    if len(practical_results) > 1:
        runner_up = practical_results[1]

        st.markdown(f"### {runner_up['STATUS']}")
        st.write(f"**{runner_up['NAME']}**")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Slots", f"{runner_up['TOTAL']} pcs")
        m2.metric("Layout", f"{runner_up['NW']} × {runner_up['NL']}")
        m3.metric("Pocket Depth", f"{runner_up['SH']:.1f} mm")

        st.write(generate_svg_tray(runner_up), unsafe_allow_html=True)
        st.caption(runner_up["NOTE"])

    else:
        st.write("ไม่มีทางเลือกสำรองที่เหมาะสม")


# ============================================================
# FULL ANALYSIS TABLE
# ============================================================
st.write("---")
st.subheader("📊 Full Analysis Table")

table_data = []

for r in results:
    table_data.append(
        {
            "Status": r["STATUS"],
            "Case": r["NAME"],
            "Layout": f"{r['NW']} × {r['NL']}",
            "Total Slots": r["TOTAL"],
            "Pure Product": f"{r['PW']:.1f} × {r['PL']:.1f} × {r['PH']:.1f}",
            "Bottom Pocket": f"{r['BOTTOM_W']:.1f} × {r['BOTTOM_L']:.1f}",
            "Top Opening": f"{r['SW']:.1f} × {r['SL']:.1f}",
            "Pocket Depth": f"{r['SH']:.1f}",
            "Depth Index": f"{r['RATIO']:.2f}",
            "Min Web": f"{r['REQ_PITCH']:.1f}",
            "Edge Free W": f"{r['EDGE_FREE_W']:.1f}",
            "Edge Free L": f"{r['EDGE_FREE_L']:.1f}",
            "Note": r["NOTE"],
        }
    )

st.dataframe(
    table_data,
    use_container_width=True,
)

# ============================================================
# ENGINEERING NOTES
# ============================================================
with st.expander("🧠 RFQ Engineering Assumptions / Why these defaults?"):
    st.markdown(
        """
### Default philosophy

**Pocket fit clearance**
- Wide plane ≥30 mm: **6 mm total ≈ 3 mm/side**
- Narrow plane <30 mm: **4 mm total ≈ 2 mm/side**

These values are intended as RFQ concept defaults for direct PCBA/product placement.
They are **not ESD-bag allowances**.

**Vertical headroom**
- Default = **5 mm**
- The previous +12 mm assumption was intentionally conservative, but it also increased
  draft expansion and could reduce tray capacity unnecessarily.

**Inter-pocket web**
- Base = **6 mm**
- Dynamic addition = `Pocket Depth Index × 1.0`
- The web is counted **between adjacent pockets only**.
- Outer edge protection is already controlled separately by `Tray Edge Margin`.

**Manual handling**
- Finger notch / finger access should normally be a **local feature**.
- V0.2 therefore does not enlarge every cavity pitch simply because manual handling is selected.

**Draft**
- 3° is retained as an RFQ starting assumption.
- Final draft must be confirmed with the tray forming process / supplier.

### Important limitation
The `Pocket Depth Index = pocket depth / minimum bottom-pocket plane dimension`
is a practical RFQ heuristic, not a substitute for supplier thermoforming DFM.
Final feasibility still depends on material type, sheet thickness, forming method,
corner radius, rib geometry, draw distribution and process capability.
"""
    )
