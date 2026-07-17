import streamlit as st
import math

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Tray Layout Optimizer", layout="wide")

st.title("🛠️ NPI Tray Design Layout Optimizer (Capacity First)")
st.write("ระบบคัดเลือก Layout ที่เน้นจำนวน Slot สูงสุด ภายใต้เงื่อนไขที่ผลิตได้จริง (พร้อม DFM Checklist)")

# --- SIDEBAR: INPUT PARAMETERS ---
st.sidebar.header("1. Product Dimensions (mm)")
p_w = st.sidebar.number_input("Product Width (W)", value=314.0, step=1.0)
p_l = st.sidebar.number_input("Product Length (L)", value=60.0, step=1.0)
p_h = st.sidebar.number_input("Product Height (H)", value=15.0, step=1.0)

# Checkbox สำหรับล็อคท่าแนวนอน (H-Up) เท่านั้น
force_horizontal = st.sidebar.checkbox("⚠️ Force Horizontal (H-up) for Heavy/Large Components", value=False, help="บังคับวางบอร์ดแนวนอนเท่านั้น สำหรับ PCBA ที่มีชิ้นส่วนหนักหรือสูง เพื่อป้องกันบอร์ดโก่งตัว")

st.sidebar.header("2. Tray Specification (mm)")
overall_w = st.sidebar.number_input("Tray Overall Width", value=375.0)
overall_l = st.sidebar.number_input("Tray Overall Length", value=260.0)
tray_margin = st.sidebar.number_input("Tray Edge Margin (Stacking Shoulder)", value=15.0, help="ระยะขอบรอบนอกสำหรับรับน้ำหนักถาดใบบน")

st.sidebar.header("3. Engineering Clearances")
c_wide = st.sidebar.slider("Wide Plane Clearance (>=30mm)", 5.0, 20.0, 14.0)
c_narrow = st.sidebar.slider("Narrow Plane Clearance (<30mm)", 5.0, 20.0, 11.0)
c_h_depth = st.sidebar.number_input("Vertical Clearance (Safety Margin)", value=12.0)

# ตั้งค่า Default เป็น Manual เพื่อกลยุทธ์การ Quote ราคาที่ปลอดภัย
handling = st.sidebar.radio("Assembly Handling Method", [
    "Manual (Need Finger Slots) - Default for Safe RFQ", 
    "Automation (Robotic/Vacuum)"
])

st.sidebar.header("4. DFM & Material Limits")
# [MODIFIED] เปลี่ยนตัวแปรให้สอดคล้องกับ Dynamic Web Pitch Logic
base_web_clearance = st.sidebar.number_input("Base Web Clearance (Minimum)", value=8.0, help="ระยะห่างช่องพื้นฐานก่อนชดเชยความลึก")
dynamic_web_factor = st.sidebar.slider("Dynamic Web Factor", 0.0, 3.0, 1.5, help="ตัวคูณชดเชยระยะห่างช่องตาม Draw Ratio (ป้องกันพลาสติกบาง)")
max_depth_ratio = st.sidebar.slider("Max Depth Ratio (Draw Ratio)", 1.0, 5.0, 2.5)
max_material_limit = st.sidebar.number_input("Max Material Limit (Total Height)", value=85.0)
draft_angle = st.sidebar.number_input("Draft Angle (Degrees)", value=3.0)

# --- CALCULATION ENGINE ---
def calculate_layout_params(pw_used, pl_used, ph_used, orientation_name):
    clearance_w = c_wide if pw_used >= 30 else c_narrow
    clearance_l = c_wide if pl_used >= 30 else c_narrow
    
# คำนวณระยะเว้นช่องไฟแบบ Dynamic ตามความลึก
    req_pitch = base_web_clearance + (current_ratio * dynamic_web_factor)
    
    # [NEW LOGIC] ถ้าต้องใช้มือคนหยิบ ให้บังคับระยะ Web Pitch ขั้นต่ำให้กว้างพอทำรอยเว้า Finger Scallop
    # ระยะนิ้วคนมาตรฐานมักจะต้องการความกว้างของผนังอย่างน้อย 15-18 mm เพื่อกัดรอยเว้าลงไป
    if "Manual" in handling:
        if req_pitch < 18.0:
            req_pitch = 18.0
            
    slot_h = ph_used + c_h_depth
    
    # คำนวณ Draft Angle Effect (ยิ่งลึก ปากยิ่งกว้าง)
    draft_expansion = 2 * (slot_h * math.tan(math.radians(draft_angle)))
    
    slot_w = pw_used + clearance_w + draft_expansion
    slot_l = pl_used + clearance_l + draft_expansion
    
    min_plane_dim = min(slot_w, slot_l)
    current_ratio = slot_h / min_plane_dim if min_plane_dim > 0 else 0
    
    # [NEW] หักพื้นที่ขอบออก (Stacking Shoulder) เพื่อหา Usable Area ที่แท้จริง
    usable_w = overall_w - (2 * tray_margin)
    usable_l = overall_l - (2 * tray_margin)
    
    # [NEW] คำนวณระยะเว้นช่องไฟแบบ Dynamic ตามความลึก (ป้องกันอาการ Webbing)
    req_pitch = base_web_clearance + (current_ratio * dynamic_web_factor)
    
    # Layout Calculation อ้างอิงจาก Pitch ที่ถูกชดเชยแล้ว
    slots_nw = math.floor((usable_w - req_pitch) / (slot_w + req_pitch))
    slots_nl = math.floor((usable_l - req_pitch) / (slot_l + req_pitch))
    
    # ป้องกันกรณีพื้นที่ใช้งานเล็กกว่าชิ้นงานจนค่าติดลบ
    slots_nw = max(0, slots_nw)
    slots_nl = max(0, slots_nl)
    total_slots = slots_nw * slots_nl
    
    # --- INTELLIGENT DFM & SCORING ---
    is_material_feasible = slot_h <= max_material_limit
    is_ratio_pass = current_ratio <= max_depth_ratio
    is_single_row = (slots_nw == 1 or slots_nl == 1)
    
    if total_slots == 0:
        status = "❌ DOES NOT FIT"
        score = 0
        note = "Layout exceeds usable area"
    elif not is_material_feasible:
        status = "❌ MATERIAL LIMIT"
        score = 0
        note = f"Height {slot_h:.1f} > {max_material_limit}mm"
    elif is_ratio_pass:
        status = "✅ PASS"
        score = 3  # ผลิตได้ชัวร์ (Grid)
        note = "Feasible (Closed Pocket)"
    elif is_single_row:
        status = "⚠️ WARNING (Rib Req.)"
        score = 2  # ผลิตได้ แต่ต้องทำ Ribs ช่วยค้ำ
        note = f"Ratio {current_ratio:.2f} > {max_depth_ratio} (Needs Rib Design)"
    else:
        status = "❌ DFM ERROR"
        score = 1  # ลึกเกินไป ขึ้นรูปยากมาก พลาสติกฉีกขาด
        note = f"Ratio {current_ratio:.2f} > {max_depth_ratio} (Too Deep)"

    # กระจาย Pitch ให้สมดุลซ้าย-ขวา บน-ล่าง สำหรับการวาด SVG ให้สวยงาม
    if total_slots > 0:
        used_w = slots_nw * slot_w
        used_l = slots_nl * slot_l
        pitch_w = (usable_w - used_w) / (slots_nw + 1)
        pitch_l = (usable_l - used_l) / (slots_nl + 1)
    else:
        pitch_w, pitch_l = 0, 0

    return {
        "NAME": orientation_name, "PW": pw_used, "PL": pl_used, "PH": ph_used,
        "SW": slot_w, "SL": slot_l, "SH": slot_h,
        "NW": slots_nw, "NL": slots_nl, "TOTAL": total_slots,
        "PITCH_W": pitch_w, "PITCH_L": pitch_l, "REQ_PITCH": req_pitch,
        "STATUS": status, "NOTE": note, "RATIO": current_ratio,
        "SCORE": score
    }

# Run 6-Way Analysis
dims = [p_w, p_l, p_h]
dim_names = ['W', 'L', 'H']
results = []
case_idx = 1
for i in range(3):
    h_val, h_nm = dims[i], dim_names[i]
    
    # ข้าม Loop ท่าที่แนวตั้ง (ตั้งด้วย W หรือ L) ถ้าถูกบังคับให้วางแนวนอน
    if force_horizontal and h_nm != 'H':
        continue
        
    rem_dims = [dims[j] for j in range(3) if j != i]
    rem_nms = [dim_names[j] for j in range(3) if j != i]
    results.append(calculate_layout_params(rem_dims[0], rem_dims[1], h_val, f"Case {case_idx}: {rem_nms[0]}x{rem_nms[1]}x{h_nm} (Z)"))
    case_idx += 1
    results.append(calculate_layout_params(rem_dims[1], rem_dims[0], h_val, f"Case {case_idx}: {rem_nms[1]}x{rem_nms[0]}x{h_nm} (Z)"))
    case_idx += 1

# SORTING LOGIC
practical_results = [r for r in results if r['SCORE'] >= 2]
practical_results.sort(key=lambda x: (x['TOTAL'], -x['RATIO']), reverse=True) 
results.sort(key=lambda x: (x['SCORE'], x['TOTAL']), reverse=True)

# --- SVG PLOTTING ---
def generate_svg_tray(res):
    color = "#16a34a" if res["SCORE"] == 3 else "#ca8a04" if res["SCORE"] == 2 else "#ef4444"
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {overall_w} {overall_l}" xmlns="http://www.w3.org/2000/svg" style="background-color: white; border: 3px solid {color}; border-radius: 8px;">'
    
    # วาด Overall Box
    svg += f'<rect width="100%" height="100%" fill="none" stroke="{color}" stroke-width="4" />'
    
    # วาด Usable Area Box
    svg += f'<rect x="{tray_margin}" y="{tray_margin}" width="{overall_w - 2*tray_margin}" height="{overall_l - 2*tray_margin}" fill="none" stroke="#6b7280" stroke-width="2" stroke-dasharray="5,5" />'
    
    if res["TOTAL"] > 0:
        for i in range(res["NW"]):
            for j in range(res["NL"]):
                x = tray_margin + res["PITCH_W"] + i * (res["SW"] + res["PITCH_W"])
                y = tray_margin + res["PITCH_L"] + j * (res["SL"] + res["PITCH_L"])
                svg += f'<rect x="{x}" y="{y}" width="{res["SW"]}" height="{res["SL"]}" fill="#f3f4f6" stroke="#9ca3af" stroke-width="1" />'
    svg += '</svg>'
    return svg

# --- DISPLAY ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🥇 Best Capacity Option")
    if practical_results:
        best = practical_results[0]
        st.markdown(f"### {best['STATUS']}")
        st.write(f"**{best['NAME']}**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Slots", f"{best['TOTAL']} Pcs")
        m2.metric("Tray Thick", f"{best['SH']:.1f} mm")
        m3.metric("Draw Ratio", f"{best['RATIO']:.2f}")
        st.write(generate_svg_tray(best), unsafe_allow_html=True)
    else:
        st.error("ไม่มีรูปแบบการวางที่ผ่านเกณฑ์ DFM หรือ ไม่พบรูปแบบแนวนอนที่ผลิตได้")

with col2:
    st.subheader("🥈 Alternative Option")
    if len(practical_results) > 1:
        runner_up = practical_results[1]
        st.markdown(f"### {runner_up['STATUS']}")
        st.write(f"**{runner_up['NAME']}**")
        st.write(f"Total Slots: {runner_up['TOTAL']} | Tray Thick: {runner_up['SH']:.1f} mm")
        st.write(generate_svg_tray(runner_up), unsafe_allow_html=True)
    else:
        st.write("ไม่มีทางเลือกสำรองที่เหมาะสม")

st.write("---")
st.subheader("📊 Full Analysis Table")
table_data = []
for r in results:
    table_data.append({
        "Status": r["STATUS"],
        "Case": r["NAME"],
        "Layout": f"{r['NW']}x{r['NL']}",
        "Tray Thick (mm)": f"{r['SH']:.1f}",
        "Total Slots": r["TOTAL"],
        "Draw Ratio": f"{r['RATIO']:.2f}",
        "Min Pitch Req (mm)": f"{r['REQ_PITCH']:.1f}",
        "Note": r["NOTE"]
    })
st.dataframe(table_data, use_container_width=True)
