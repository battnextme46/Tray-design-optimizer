import streamlit as st
import math

# ============================================================
# APP CONFIG
# ============================================================
APP_VERSION = "V0.3 — Product Envelope + Engineering Section View"

st.set_page_config(
    page_title=f"Tray Layout Optimizer {APP_VERSION}",
    layout="wide",
)

st.title("🛠️ NPI Tray Design Layout Optimizer (Capacity First)")
st.caption(
    f"{APP_VERSION} • RFQ concept screening • "
    "Pure Product → Pocket Clearance → Draft Expansion → Inter-Pocket Web → Engineering Section"
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

shoulder_reserve = st.sidebar.number_input(
    "Minimum Pocket-to-Shoulder Reserve",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.5,
    help=(
        "ระยะขั้นต่ำจากขอบพื้นที่ Stacking Shoulder ถึงขอบ Pocket Opening. "
        "Default RFQ = 2 mm/side เพื่อไม่ให้ cavity ชิด shoulder เกินไป"
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

st.sidebar.header("5. Visualization")

section_view_mode = st.sidebar.selectbox(
    "Section View Direction",
    options=[
        "Auto — Critical Plane",
        "X Section — Width Plane",
        "Y Section — Length Plane",
        "Show Both",
    ],
    index=0,
    help=(
        "Auto จะเลือก section ของ floor plane ที่มี bottom-pocket dimension เล็กกว่า "
        "เพราะมักเป็นแกนที่มีความเสี่ยงเรื่อง depth/fit สูงกว่า. "
        "Show Both ใช้สำหรับ engineering review."
    ),
)

st.sidebar.caption(
    "V0.3 Visualization only: solver / capacity ranking remains unchanged from V0.2.1."
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

    # V0.2.1:
    # Reserve a minimum gap between the Stacking Shoulder boundary
    # and the first/last Pocket Opening.
    layout_w = max(0.0, usable_w - (2.0 * shoulder_reserve))
    layout_l = max(0.0, usable_l - (2.0 * shoulder_reserve))

    # Correct cavity count:
    # N*pocket + (N-1)*web <= layout_span
    slots_nw = floor_count_with_internal_web(
        layout_w,
        slot_w,
        req_web,
    )
    slots_nl = floor_count_with_internal_web(
        layout_l,
        slot_l,
        req_web,
    )

    total_slots = slots_nw * slots_nl

    # Center the selected grid inside the full usable region.
    # This means EDGE_FREE_* is the actual Pocket-to-Shoulder gap
    # after layout selection and will normally be >= shoulder_reserve.
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
        "LAYOUT_W": layout_w,
        "LAYOUT_L": layout_l,
        "USED_W": used_w,
        "USED_L": used_l,

        "SHOULDER_RESERVE": shoulder_reserve,
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
    """
    Engineering Top View.

    Visual layers:
      - green = pure product bounding envelope
      - blue dashed = bottom pocket / fit-clearance envelope
      - grey = draft-expanded pocket top opening
      - grey dashed = stacking-shoulder boundary
      - orange dashed = minimum pocket-to-shoulder reserve boundary
    """
    color = (
        "#16a34a"
        if res["SCORE"] == 3
        else "#ca8a04"
        if res["SCORE"] == 2
        else "#ef4444"
    )

    svg = (
        f'<svg width="100%" height="auto" '
        f'viewBox="0 0 {overall_w} {overall_l + 18}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background-color:white;border:3px solid {color};'
        f'border-radius:8px;">'
    )

    # Overall tray.
    svg += (
        f'<rect x="0" y="0" width="{overall_w}" height="{overall_l}" '
        f'fill="#ffffff" stroke="{color}" stroke-width="4" />'
    )

    # Stacking shoulder / usable boundary.
    svg += (
        f'<rect x="{tray_margin}" y="{tray_margin}" '
        f'width="{res["USABLE_W"]}" height="{res["USABLE_L"]}" '
        f'fill="#f8fafc" stroke="#64748b" stroke-width="1.5" '
        f'stroke-dasharray="5,5" />'
    )

    # Minimum pocket-to-shoulder reserve boundary.
    reserve_x = tray_margin + res["SHOULDER_RESERVE"]
    reserve_y = tray_margin + res["SHOULDER_RESERVE"]
    reserve_w = max(
        0.0,
        res["USABLE_W"] - 2.0 * res["SHOULDER_RESERVE"],
    )
    reserve_l = max(
        0.0,
        res["USABLE_L"] - 2.0 * res["SHOULDER_RESERVE"],
    )

    svg += (
        f'<rect x="{reserve_x}" y="{reserve_y}" '
        f'width="{reserve_w}" height="{reserve_l}" '
        f'fill="none" stroke="#f59e0b" stroke-width="0.9" '
        f'stroke-dasharray="2,2" />'
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

                # Bottom pocket / clearance envelope.
                inset = res["DRAFT_EACH_SIDE"]
                bottom_x = x + inset
                bottom_y = y + inset
                bottom_w = res["BOTTOM_W"]
                bottom_l = res["BOTTOM_L"]

                svg += (
                    f'<rect x="{bottom_x}" y="{bottom_y}" '
                    f'width="{bottom_w}" height="{bottom_l}" '
                    f'fill="#dbeafe" fill-opacity="0.22" '
                    f'stroke="#2563eb" stroke-width="0.8" '
                    f'stroke-dasharray="3,2" rx="1" />'
                )

                # PURE PRODUCT envelope centered inside the bottom pocket.
                product_x = bottom_x + res["CLEAR_W"] / 2.0
                product_y = bottom_y + res["CLEAR_L"] / 2.0

                svg += (
                    f'<rect x="{product_x}" y="{product_y}" '
                    f'width="{res["PW"]}" height="{res["PL"]}" '
                    f'fill="#22c55e" fill-opacity="0.72" '
                    f'stroke="#15803d" stroke-width="0.9" rx="0.8" />'
                )

    # Legend.
    legend_y = overall_l + 12
    svg += (
        f'<text x="{overall_w/2}" y="{legend_y}" '
        f'font-family="system-ui,sans-serif" font-size="6.4" '
        f'fill="#475569" text-anchor="middle">'
        f'Green = Product Envelope • Blue dashed = Pocket Bottom / Fit Clearance • '
        f'Grey = Top Opening • Orange dashed = Shoulder Reserve Boundary'
        f'</text>'
    )

    svg += "</svg>"
    return svg


def choose_auto_section_plane(res):
    """
    Auto chooses the plane with the smaller bottom-pocket dimension.
    This is normally the more critical pocket-depth / forming plane.
    """
    if res["BOTTOM_W"] <= res["BOTTOM_L"]:
        return "X"
    return "Y"


def get_section_plane_data(res, plane):
    if plane == "X":
        return {
            "plane": "X",
            "title": "X SECTION — WIDTH PLANE",
            "product_span": res["PW"],
            "clearance_total": res["CLEAR_W"],
            "bottom_span": res["BOTTOM_W"],
            "top_span": res["SW"],
            "web": res["WEB_W"],
            "count": res["NW"],
            "axis_label": "Product Width / Tray Width direction",
        }

    return {
        "plane": "Y",
        "title": "Y SECTION — LENGTH PLANE",
        "product_span": res["PL"],
        "clearance_total": res["CLEAR_L"],
        "bottom_span": res["BOTTOM_L"],
        "top_span": res["SL"],
        "web": res["WEB_L"],
        "count": res["NL"],
        "axis_label": "Product Length / Tray Length direction",
    }


def generate_section_svg(res, plane):
    """
    Representative 2D engineering section of up to 3 adjacent pockets.

    Assumption for RFQ concept:
      product rests on the pocket bottom.
      therefore:
        Product Top below Tray Top = Pocket Depth - Product Height
                                   = Vertical Headroom
    """
    d = get_section_plane_data(res, plane)

    sample_count = max(1, min(3, int(d["count"])))
    pocket_top = d["top_span"]
    pocket_bottom = d["bottom_span"]
    web = d["web"]
    product_span = d["product_span"]

    pocket_depth = res["SH"]
    product_height = res["PH"]
    top_clearance = max(0.0, pocket_depth - product_height)

    # Drawing scaling.
    scale_x = 2.1
    scale_z = 2.8

    left_pad = 42.0
    right_pad = 42.0
    top_pad = 58.0
    bottom_pad = 48.0

    section_span = (
        sample_count * pocket_top
        + max(0, sample_count - 1) * web
    )

    view_w = left_pad + section_span * scale_x + right_pad
    view_h = top_pad + pocket_depth * scale_z + bottom_pad

    y_top = top_pad
    y_bottom = y_top + pocket_depth * scale_z

    svg = (
        f'<svg width="100%" height="auto" '
        f'viewBox="0 0 {view_w} {view_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#ffffff;border:2px solid #334155;border-radius:10px;">'
    )

    # Title.
    svg += (
        f'<text x="{view_w/2}" y="24" '
        f'font-family="system-ui,sans-serif" font-size="13" '
        f'font-weight="700" fill="#0f172a" text-anchor="middle">'
        f'{d["title"]} • Representative {sample_count} pocket(s)'
        f'</text>'
    )

    svg += (
        f'<text x="{view_w/2}" y="41" '
        f'font-family="system-ui,sans-serif" font-size="7.5" '
        f'fill="#64748b" text-anchor="middle">'
        f'{d["axis_label"]}'
        f'</text>'
    )

    # Tray top reference line.
    svg += (
        f'<line x1="{left_pad-14}" y1="{y_top}" '
        f'x2="{view_w-right_pad+14}" y2="{y_top}" '
        f'stroke="#0f172a" stroke-width="2.2" />'
    )
    svg += (
        f'<text x="{left_pad-18}" y="{y_top-5}" '
        f'font-family="system-ui,sans-serif" font-size="7" '
        f'fill="#0f172a" text-anchor="start">TRAY TOP</text>'
    )

    current_x = left_pad

    for idx in range(sample_count):
        top_left = current_x
        top_right = current_x + pocket_top * scale_x

        # Bottom opening is centered relative to top opening.
        draft_inset = (pocket_top - pocket_bottom) * scale_x / 2.0
        bottom_left = top_left + draft_inset
        bottom_right = top_right - draft_inset

        # Pocket interior fill.
        pocket_points = (
            f"{top_left},{y_top} "
            f"{top_right},{y_top} "
            f"{bottom_right},{y_bottom} "
            f"{bottom_left},{y_bottom}"
        )
        svg += (
            f'<polygon points="{pocket_points}" '
            f'fill="#f8fafc" stroke="none" />'
        )

        # Drafted pocket walls.
        svg += (
            f'<line x1="{top_left}" y1="{y_top}" '
            f'x2="{bottom_left}" y2="{y_bottom}" '
            f'stroke="#64748b" stroke-width="1.5" />'
        )
        svg += (
            f'<line x1="{top_right}" y1="{y_top}" '
            f'x2="{bottom_right}" y2="{y_bottom}" '
            f'stroke="#64748b" stroke-width="1.5" />'
        )

        # Pocket bottom.
        svg += (
            f'<line x1="{bottom_left}" y1="{y_bottom}" '
            f'x2="{bottom_right}" y2="{y_bottom}" '
            f'stroke="#475569" stroke-width="1.6" />'
        )

        # Product bounding envelope — GREEN.
        product_w_px = product_span * scale_x
        product_h_px = product_height * scale_z

        product_x = (
            (bottom_left + bottom_right) / 2.0
            - product_w_px / 2.0
        )
        product_y = y_bottom - product_h_px

        svg += (
            f'<rect x="{product_x}" y="{product_y}" '
            f'width="{product_w_px}" height="{product_h_px}" '
            f'fill="#22c55e" fill-opacity="0.76" '
            f'stroke="#15803d" stroke-width="1.2" rx="1.5" />'
        )

        # Product top reference.
        svg += (
            f'<line x1="{product_x}" y1="{product_y}" '
            f'x2="{product_x+product_w_px}" y2="{product_y}" '
            f'stroke="#166534" stroke-width="1.0" stroke-dasharray="3,2" />'
        )

        # Web / tray top material between pockets.
        if idx < sample_count - 1:
            web_x1 = top_right
            web_x2 = top_right + web * scale_x
            svg += (
                f'<line x1="{web_x1}" y1="{y_top}" '
                f'x2="{web_x2}" y2="{y_top}" '
                f'stroke="#0f172a" stroke-width="3.2" />'
            )

        current_x = top_right + web * scale_x

    # Vertical dimension: pocket depth.
    dim_x = view_w - right_pad + 20
    svg += (
        f'<line x1="{dim_x}" y1="{y_top}" x2="{dim_x}" y2="{y_bottom}" '
        f'stroke="#2563eb" stroke-width="1" />'
    )
    svg += (
        f'<line x1="{dim_x-4}" y1="{y_top}" x2="{dim_x+4}" y2="{y_top}" '
        f'stroke="#2563eb" stroke-width="1" />'
    )
    svg += (
        f'<line x1="{dim_x-4}" y1="{y_bottom}" x2="{dim_x+4}" y2="{y_bottom}" '
        f'stroke="#2563eb" stroke-width="1" />'
    )
    svg += (
        f'<text x="{dim_x+5}" y="{(y_top+y_bottom)/2}" '
        f'font-family="system-ui,sans-serif" font-size="7" '
        f'fill="#1d4ed8">'
        f'Pocket {pocket_depth:.1f} mm'
        f'</text>'
    )

    # Vertical dimension: top clearance / product top below tray top.
    clearance_y = y_top + top_clearance * scale_z
    clear_x = left_pad - 16
    svg += (
        f'<line x1="{clear_x}" y1="{y_top}" '
        f'x2="{clear_x}" y2="{clearance_y}" '
        f'stroke="#f59e0b" stroke-width="1.2" />'
    )
    svg += (
        f'<text x="{clear_x-3}" y="{(y_top+clearance_y)/2}" '
        f'font-family="system-ui,sans-serif" font-size="7" '
        f'fill="#b45309" text-anchor="end">'
        f'Headroom {top_clearance:.1f} mm'
        f'</text>'
    )

    # Bottom summary.
    svg += (
        f'<text x="{view_w/2}" y="{view_h-25}" '
        f'font-family="system-ui,sans-serif" font-size="7.5" '
        f'fill="#475569" text-anchor="middle">'
        f'Green = Product Maximum Envelope • '
        f'Bottom Pocket = {pocket_bottom:.1f} mm • '
        f'Top Opening = {pocket_top:.1f} mm • '
        f'Web = {web:.1f} mm • Draft = {draft_angle:.1f}°'
        f'</text>'
    )
    svg += (
        f'<text x="{view_w/2}" y="{view_h-11}" '
        f'font-family="system-ui,sans-serif" font-size="7.5" '
        f'fill="#475569" text-anchor="middle">'
        f'Product H = {product_height:.1f} mm • '
        f'Product top is {top_clearance:.1f} mm below Tray Top'
        f'</text>'
    )

    svg += "</svg>"
    return svg


def render_section_view(res):
    top_clearance = max(0.0, res["SH"] - res["PH"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Product Height", f"{res['PH']:.1f} mm")
    m2.metric("Pocket Depth", f"{res['SH']:.1f} mm")
    m3.metric("Top Clearance", f"{top_clearance:.1f} mm")
    m4.metric(
        "Product Position",
        "✅ Below Tray Top" if top_clearance > 0.0 else "⚠️ Flush / Protrusion",
    )

    if top_clearance >= c_h_depth - 1e-9:
        st.success(
            f"✅ Product maximum envelope is {top_clearance:.1f} mm below Tray Top "
            f"(target vertical headroom = {c_h_depth:.1f} mm)."
        )
    elif top_clearance > 0:
        st.warning(
            f"⚠️ Product remains below Tray Top, but only by {top_clearance:.1f} mm."
        )
    else:
        st.error("❌ Product maximum envelope reaches or protrudes above Tray Top.")

    if section_view_mode == "Show Both":
        sx, sy = st.columns(2)
        with sx:
            st.markdown("**X Section — Width Plane**")
            st.write(generate_section_svg(res, "X"), unsafe_allow_html=True)
        with sy:
            st.markdown("**Y Section — Length Plane**")
            st.write(generate_section_svg(res, "Y"), unsafe_allow_html=True)

    else:
        if section_view_mode == "X Section — Width Plane":
            plane = "X"
        elif section_view_mode == "Y Section — Length Plane":
            plane = "Y"
        else:
            plane = choose_auto_section_plane(res)

        auto_note = (
            "Auto selected the smaller bottom-pocket plane as the critical section."
            if section_view_mode == "Auto — Critical Plane"
            else "Manual section selection."
        )

        st.caption(
            f"{auto_note} Current section = "
            f"{'X / Width' if plane == 'X' else 'Y / Length'}."
        )
        st.write(generate_section_svg(res, plane), unsafe_allow_html=True)


def render_engineering_summary(res):
    data = {
        "Pure Product Floor": f"{res['PW']:.1f} × {res['PL']:.1f} mm",
        "Product Height": f"{res['PH']:.1f} mm",
        "Pocket Bottom": f"{res['BOTTOM_W']:.1f} × {res['BOTTOM_L']:.1f} mm",
        "Pocket Top Opening": f"{res['SW']:.1f} × {res['SL']:.1f} mm",
        "Pocket Depth": f"{res['SH']:.1f} mm",
        "Vertical Headroom": f"{max(0.0, res['SH'] - res['PH']):.1f} mm",
        "Clearance W / L": f"{res['CLEAR_W']:.1f} / {res['CLEAR_L']:.1f} mm total",
        "Draft Expansion": f"{res['DRAFT_TOTAL']:.1f} mm total",
        "Inter-Pocket Web": f"{res['REQ_PITCH']:.1f} mm",
        "Pocket-to-Shoulder W / L": (
            f"{res['EDGE_FREE_W']:.1f} / {res['EDGE_FREE_L']:.1f} mm"
        ),
        "Depth Index": f"{res['RATIO']:.2f}",
        "Layout": f"{res['NW']} × {res['NL']} = {res['TOTAL']} slots",
    }

    st.table(
        {
            "Engineering Item": list(data.keys()),
            "Value": list(data.values()),
        }
    )

    st.info(
        "Green product geometry is the maximum rectangular Product Envelope only. "
        "V0.3 does not infer actual PCBA component shapes, connector keep-outs, "
        "capacitor/choke profiles or local support features."
    )


def render_option_result(res, title):
    st.subheader(title)
    st.markdown(f"### {res['STATUS']}")
    st.write(f"**{res['NAME']}**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Slots", f"{res['TOTAL']} pcs")
    m2.metric("Layout", f"{res['NW']} × {res['NL']}")
    m3.metric("Pocket Depth", f"{res['SH']:.1f} mm")
    m4.metric("Depth Index", f"{res['RATIO']:.2f}")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric(
        "Pocket Bottom",
        f"{res['BOTTOM_W']:.1f} × {res['BOTTOM_L']:.1f}",
    )
    s2.metric(
        "Top Opening",
        f"{res['SW']:.1f} × {res['SL']:.1f}",
    )
    s3.metric("Min Web", f"{res['REQ_PITCH']:.1f} mm")

    actual_shoulder_gap = min(
        res["EDGE_FREE_W"],
        res["EDGE_FREE_L"],
    )

    s4.metric(
        "Pocket-to-Shoulder Gap",
        f"{actual_shoulder_gap:.1f} mm",
    )

    if actual_shoulder_gap < shoulder_reserve + 0.5:
        st.warning(
            f"⚠️ Tight shoulder fit: actual gap = {actual_shoulder_gap:.1f} mm "
            f"(minimum target = {shoulder_reserve:.1f} mm)."
        )
    elif actual_shoulder_gap < shoulder_reserve + 2.0:
        st.info(
            f"ℹ️ Shoulder gap is acceptable but relatively tight: "
            f"{actual_shoulder_gap:.1f} mm."
        )
    else:
        st.success(
            f"✅ Comfortable pocket-to-shoulder gap: "
            f"{actual_shoulder_gap:.1f} mm."
        )

    tab_top, tab_section, tab_summary = st.tabs(
        [
            "🟩 Top View",
            "📐 Section View",
            "📊 Engineering Summary",
        ]
    )

    with tab_top:
        st.write(generate_svg_tray(res), unsafe_allow_html=True)
        st.caption(
            "Top View legend: Green = Product Envelope • "
            "Blue dashed = Pocket Bottom / Product Clearance • "
            "Grey = Draft-expanded Top Opening."
        )

    with tab_section:
        render_section_view(res)

    with tab_summary:
        render_engineering_summary(res)

    st.caption(res["NOTE"])


# ============================================================
# RFQ ASSUMPTION SUMMARY
# ============================================================
st.info(
    "**RFQ-Calibrated defaults:** "
    f"Wide clearance = {c_wide:.1f} mm total • "
    f"Narrow clearance = {c_narrow:.1f} mm total • "
    f"Vertical headroom = {c_h_depth:.1f} mm • "
    f"Pocket-to-Shoulder reserve = {shoulder_reserve:.1f} mm/side • "
    f"Base web = {base_web_clearance:.1f} mm • "
    f"Draft = {draft_angle:.1f}°. "
    "These are concept-screening assumptions, not final supplier DFM values."
)

st.caption(
    "V0.3 keeps V0.2.1 solver geometry unchanged. "
    "New visualization shows Pure Product in green and provides X/Y engineering sections. "
    f"Pocket openings still remain at least {shoulder_reserve:.1f} mm inside the stacking-shoulder boundary."
)

# ============================================================
# DISPLAY — BEST / ALTERNATIVE
# ============================================================
col1, col2 = st.columns(2)

with col1:
    if practical_results:
        render_option_result(
            practical_results[0],
            "🥇 Best Capacity Option",
        )
    else:
        st.subheader("🥇 Best Capacity Option")
        st.error("ไม่มีรูปแบบการวางที่ผ่าน RFQ / DFM screening")

with col2:
    if len(practical_results) > 1:
        render_option_result(
            practical_results[1],
            "🥈 Alternative Option",
        )
    else:
        st.subheader("🥈 Alternative Option")
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
            "Shoulder Min": f"{r['SHOULDER_RESERVE']:.1f}",
            "Pocket-Shoulder W": f"{r['EDGE_FREE_W']:.1f}",
            "Pocket-Shoulder L": f"{r['EDGE_FREE_L']:.1f}",
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

**Pocket-to-Shoulder reserve**
- Default = **2 mm/side**
- This is measured from the inner Stacking Shoulder boundary to the nearest Pocket Opening.
- It prevents a capacity-first layout from pushing the cavity almost onto the shoulder line.
- Overall minimum distance from tray outer edge to pocket is therefore approximately:
  `Tray Edge Margin + Pocket-to-Shoulder Reserve`.

**Inter-pocket web**
- Base = **6 mm**
- Dynamic addition = `Pocket Depth Index × 1.0`
- The web is counted **between adjacent pockets only**.
- Outer edge protection is controlled separately by `Tray Edge Margin + Shoulder Reserve`.

**Manual handling**
- Finger notch / finger access should normally be a **local feature**.
- The solver therefore does not enlarge every cavity pitch simply because manual handling is selected.

**V0.3 Product / Section visualization**
- Green = **Pure Product Maximum Envelope**.
- Blue dashed = **Bottom Pocket / Product Clearance Envelope**.
- Grey pocket outline = **Draft-expanded Top Opening**.
- Product is assumed to rest on the **Pocket Bottom** for RFQ section screening.
- Therefore `Product Top below Tray Top = Pocket Depth - Product Height`.
- `Auto — Critical Plane` selects the smaller bottom-pocket plane for the representative section.
- `Show Both` displays Width-plane and Length-plane sections side-by-side.
- The visual does **not** infer actual PCBA component height maps or local connector/keep-out geometry.

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
