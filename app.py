import streamlit as st
import math

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Tray Layout Optimizer", layout="wide")

st.title("🛠️ NPI Tray Design Layout Optimizer")
st.write("ระบบคำนวณ Slot และจัดวาง Layout สำหรับการออกแบบ Tray พร้อมตรวจสอบเงื่อนไข DFM อัตโนมัติ")

# --- SIDEBAR: INPUT PARAMETERS ---
st.sidebar.header("1. Product Dimensions (mm)")
p_w = st.sidebar.number_input("Product Width (W)", value=10.0, step=1.0)
p_l = st.sidebar.number_input("Product Length (L)", value=20.0, step=1.0)
p_h = st.sidebar.number_input("Product Height (H)", value=15.0, step=1.0)

st.sidebar.header("2. Tray Specification (mm)")
overall_w = st.sidebar.number_input("Tray Overall Width", value=375.0)
overall_l = st.sidebar.number_input("Tray Overall Length", value=280.0)

st.sidebar.header("3. Engineering Clearances")
c_wide = st.sidebar.slider("Wide Plane Clearance (>=30mm)", 5.0, 20.0, 14.0)
c_narrow = st.sidebar.slider("Narrow Plane Clearance (<30mm)", 5.0, 20.0, 11.0)
c_h_depth = st.sidebar.number_input("Vertical Clearance (Safety Margin)", value=12.0)

st.sidebar.header("4. DFM & Material Limits")
temp_clearance = st.sidebar.number_input("DFM Pitch (Between Slots)", value=8.0)
max_depth_ratio = st.sidebar.slider("Maximum Depth Ratio", 1.0, 5.0, 2.5)
max_material_limit = st.sidebar.number_input("Max Material Deformation (mm)", value=85.0)

# --- CALCULATION ENGINE ---
def calculate_layout_params(pw_used, pl_used, ph_used, orientation_name):
    clearance_w = c_wide if pw_used >= 30 else c_narrow
    clearance_l = c_wide if pl_used >= 30 else c_narrow
    
    slot_w = pw_used + clearance_w
    slot_l = pl_used + clearance_l
    slot_h = ph_used + c_h_depth
    
    min_plane_dim = min(slot_w, slot_l)
    max_allowable_depth = min_plane_dim * max_depth_ratio
    
    is_dfm_feasible = slot_h <= max_allowable_depth
    is_material_feasible = slot_h <= max_material_limit
    
    is_feasible = False
    feasibility_note = ""
    
    if not is_dfm_feasible:
        feasibility_note = f"DFM Error: Depth {slot_h:.1f} > Max {max_allowable_depth:.1f}"
    elif not is_material_feasible:
        feasibility_note = f"Material Error: Slot H {slot_h:.1f} > Limit {max_material_limit}mm"
    else:
        is_feasible = True

    slots_nw, slots_nl, total_slots = 0, 0, 0
    pitch_w, pitch_l = 0.0, 0.0
    if is_feasible:
        slots_nw = math.floor((overall_w - temp_clearance) / (slot_w + temp_clearance))
        slots_nl = math.floor((overall_l - temp_clearance) / (slot_l + temp_clearance))
        total_slots = slots_nw * slots_nl
        if total_slots > 0:
            pitch_w = (overall_w - (slots_nw * slot_w)) / (slots_nw + 1)
            pitch_l = (overall_l - (slots_nl * slot_l)) / (slots_nl + 1)
        else:
            is_feasible = False
            feasibility_note = "Slots = 0"

    return {
        "NAME": orientation_name, "PW": pw_used, "PL": pl_used, "PH": ph_used,
        "SW": slot_w, "SL": slot_l, "SH": slot_h,
        "NW": slots_nw, "NL": slots_nl, "TOTAL": total_slots,
        "PITCH_W": pitch_w, "PITCH_L": pitch_l,
        "FEASIBLE": is_feasible, "NOTE": feasibility_note
    }

# Run 6-Way Analysis
dims = [p_w, p_l, p_h]
dim_names = ['W', 'L', 'H']
results = []
case_idx = 1
for i in range(3):
    h_val, h_nm = dims[i], dim_names[i]
    rem_dims = [dims[j] for j in range(3) if j != i]
    rem_nms = [dim_names[j] for j in range(3) if j != i]
    results.append(calculate_layout_params(rem_dims[0], rem_dims[1], h_val, f"Case {case_idx}: {rem_nms[0]}x{rem_nms[1]}x{h_nm}"))
    case_idx += 1
    results.append(calculate_layout_params(rem_dims[1], rem_dims[0], h_val, f"Case {case_idx}: {rem_nms[1]}x{rem_nms[0]}x{h_nm}"))
    case_idx += 1

results.sort(key=lambda x: (x['FEASIBLE'], x['TOTAL']), reverse=True)

# --- SVG PLOTTING ---
def generate_svg_tray(res, color_theme):
    if not res["FEASIBLE"]:
        return f'<svg width="100%" height="200"><rect width="100%" height="100%" fill="#fee2e2" rx="10"/><text x="50%" y="50%" fill="#ef4444" text-anchor="middle">{res["NOTE"]}</text></svg>'
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {overall_w} {overall_l}" xmlns="http://www.w3.org/2000/svg" style="background-color: white; border: 2px solid {color_theme}; border-radius: 8px;">'
    svg += f'<rect x="0" y="0" width="{overall_w}" height="{overall_l}" fill="none" stroke="{color_theme}" stroke-width="4" />'
    for i in range(res["NW"]):
        for j in range(res["NL"]):
            x = res["PITCH_W"] + i * (res["SW"] + res["PITCH_W"])
            y = res["PITCH_L"] + j * (res["SL"] + res["PITCH_L"])
            svg += f'<rect x="{x}" y="{y}" width="{res["SW"]}" height="{res["SL"]}" fill="#f3f4f6" stroke="#9ca3af" stroke-width="1" />'
    svg += '</svg>'
    return svg

# --- DISPLAY ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🥇 Optimal Feasible Case")
    best = results[0]
    if best["FEASIBLE"]:
        st.success(f"**{best['NAME']}**")
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Total Slots", f"{best['TOTAL']} Pcs")
        c_m2.metric("Tray Thick", f"{best['SH']:.1f} mm")
        c_m3.metric("Layout", f"{best['NW']}x{best['NL']}")
        st.write(generate_svg_tray(best, "#16a34a"), unsafe_allow_html=True)

with col2:
    st.subheader("🥈 Runner-up Case")
    runner_up = results[1]
    if runner_up["FEASIBLE"]:
        st.info(f"**{runner_up['NAME']}**")
        st.write(f"Total Slots: {runner_up['TOTAL']} | Thick: {runner_up['SH']:.1f} mm")
        st.write(generate_svg_tray(runner_up, "#2563eb"), unsafe_allow_html=True)

st.write("---")
st.subheader("📊 6-Way Feasibility Summary Table")
table_data = []
for r in results:
    table_data.append({
        "Status": "✅ Pass" if r["FEASIBLE"] else "❌ Fail",
        "Case": r["NAME"],
        "Orientation (WxL)": f"{r['PW']:.1f} x {r['PL']:.1f}",
        "Slot Dim (WxLxH)": f"{r['SW']:.1f}x{r['SL']:.1f}x{r['SH']:.1f}",
        "Tray Thick (mm)": f"{r['SH']:.1f}", # ดึงค่าความหนากลับมาแล้วครับ
        "Total Slots": r["TOTAL"],
        "Pitch (W/L)": f"{r['PITCH_W']:.1f} / {r['PITCH_L']:.1f}",
        "Feasibility Note": r["NOTE"] if not r["FEASIBLE"] else "Optimal" if r == results[0] else "-"
    })
st.dataframe(table_data, use_container_width=True)
