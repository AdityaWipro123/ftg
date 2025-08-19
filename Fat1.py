# app.py
import math
import streamlit as st
import graphviz

st.set_page_config(page_title="Port Hole on Tube — Stress & Fatigue", layout="wide")


st.title("Port Hole on Tube — Fatigue FOS & Life")

# st.caption(
#     "Units: pressure p in bar; all stresses in kgf/mm². "
# )

# -----------------------------
# Helpers
# -----------------------------
def safe_div(a, b, fallback=float("nan")):
    try:
        return a / b if b != 0 else fallback
    except Exception:
        return fallback

def fmt(x, d=4):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"{x:.{d}f}"

# -----------------------------
# Layout: 3 input groups -> outputs
# -----------------------------
c_basic, c_mat, c_k, c_out = st.columns([0.85, 0.75, 0.5, 1.5])

# -----------------------------
# Basic Dimensional Inputs (typed)
# -----------------------------
with c_basic:
    st.subheader("Basic Dimensional Inputs")
    p = st.number_input("Pressure p (bar)", value=207.0, step=1.0, format="%.2f")
    D = st.number_input("Bore D (mm)", value=75.0, step=0.1, format="%.2f")
    Do = st.number_input("Tube outer dia Do (mm)", value=87.0, step=0.1, format="%.2f")
    d = st.number_input("Rod dia d (mm)", value=35.0, step=0.1, format="%.2f")
    dh = st.number_input("Port hole dia dh (mm)", value=9.0, step=0.1, format="%.2f")

# Derived thickness (as per your formula)
t = (Do - D) / 2.0

# -----------------------------
# Material Inputs (typed)
# -----------------------------
with c_mat:
    st.subheader("Material Inputs")
    Sut = st.number_input("Ultimate tensile strength Sut (kgf/mm²)", value=60.0, step=0.1, format="%.2f")
    Syt = st.number_input("Yield strength Syt (kgf/mm²)", value=50.0, step=0.1, format="%.2f")

# -----------------------------
# K-factors (sliders)
# -----------------------------
with c_k:
    st.subheader("K-factor Inputs")
    # Using broad practical ranges; adjust if you have specific bounds
    ka = st.slider("Surface factor ka", 0.00, 1.00, 0.75, 0.001)
    kb = st.slider("Size factor kb", 0.00, 1.00, 1.00, 0.001)
    kc = st.slider("Reliability factor kc", 0.00, 1.00, 0.814, 0.001)
    kd = st.slider("Temperature factor kd", 0.00, 1.00, 1.00, 0.001)
    ke = st.slider("Stress concentration factor ke", 0.00, 1.00, 1.00, 0.001)
    kh = st.slider("Surface hardening factor kh", 0.00, 2.00, 1.00, 0.001)
    kl = st.slider("Load factor kl", 0.00, 1.00, 0.85, 0.001)
    km = st.slider("Misc factor km (plating etc.)", 0.00, 1.00, 1.00, 0.001)

# -----------------------------
# Calculations (exactly as provided)
# -----------------------------

# Hoop stress Sh = p*(t + 0.57*D) / (100 * t) with t = (Do - D)/2
Sh = safe_div(p * (t + 0.57 * D), 100.0 * t)

# Longitudinal stress Sl = (p * D^2) / (100 * (Do^2 - D^2))
Sl = safe_div(p * (D**2), 100.0 * (Do**2 - D**2))

# Combined (von Mises biaxial membrane) Sc = sqrt(Sh^2 + Sl^2 - Sh*Sl)
Sc_term = Sh**2 + Sl**2 - Sh * Sl
Sc = math.sqrt(Sc_term) if Sc_term >= 0 else float("nan")

# Stress amplitude and mean (your convention)
Sa = safe_div(Sc, 2.0)
Sm = safe_div(Sc, 2.0)

# Endurance limit Se = 0.5*Ka*Kb*Kc*Kd*Ke*Kh*Kl*Km*Sut
Se = 0.5 * ka * kb * kc * kd * ke * kh * kl * km * Sut

# Permissible stress Sp = 1 / ( (1/Se) + (Sa / (Sm*Sut)) )
Sp = None
den_perm = safe_div(1.0, Se, None)
if den_perm is not None and Sm != 0 and Sut != 0:
    den2 = Sa / (Sm * Sut)
    denom = den_perm + den2
    Sp = safe_div(1.0, denom)

# Equivalent stress Sq = Sm / (1 - (Sa / Sut))
Sq = None
if Sut != 0:
    Sq = safe_div(Sm, (1.0 - (Sa / Sut)))

# Basquin slope B = (log10(Se) - log10(0.9*Sut)) / 3
B = None
if Se > 0 and 0.9 * Sut > 0:
    B = (math.log10(Se) - math.log10(0.9 * Sut)) / 3.0

# Basquin constant A = Se / (10^(6*B))
A = None
if B is not None:
    A = safe_div(Se, (10 ** (6.0 * B)))

# Static FOS = Sp / Sa
static_fos = None
if Sp is not None and Sa not in (None, 0):
    static_fos = Sp / Sa

# Fatigue FOS = Sq / Sa
fatigue_fos = None
if Sq is not None and Sa not in (None, 0):
    fatigue_fos = Sq / Sa

# Life Cycle N = (Sq / A)^(1/B)
life_cycles = None
if A not in (None, 0) and B not in (None, 0) and Sq not in (None,):
    try:
        life_cycles = (Sq / A) ** (1.0 / B)
    except Exception:
        life_cycles = float("nan")

# -----------------------------
# Outputs
# -----------------------------
with c_out:
    st.subheader("Outputs")
    st.markdown(
        """
        <style>
        .kcard{border:1px solid #e5e7eb;border-radius:12px;padding:12px;margin-bottom:8px;background:white}
        .kname{color:#64748b;font-size:12px}
        .kval{font-size:20px;font-weight:600}
        .kmini{color:#94a3b8;font-size:11px;margin-top:2px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    def card(name, value, mini=None, d=4):
        st.markdown(
            f"""
            <div class="kcard">
              <div class="kname">{name}</div>
              <div class="kval">{fmt(value, d)}</div>
              {f'<div class="kmini">{mini}</div>' if mini else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Intermediate
    card("Hoop stress Sh (kgf/mm²)", Sh,d=2)
    card("Longitudinal stress Sl (kgf/mm²)", Sl,d=2)
    card("Combined stress Sc (kgf/mm²)", Sc,d=2)
    card("Stress amplitude Sa (kgf/mm²)", Sa,d=2)
    card("Stress mean Sm (kgf/mm²)", Sm,d=2)
    card("Endurance limit Se (kgf/mm²)", Se,d=2)

    # Major
    card("Static FOS", static_fos, "Static FOS = Sp / Sa", d=2)
    card("Fatigue FOS", fatigue_fos, "Fatigue FOS = Sq / Sa", d=2)
    card("Life Cycles N", life_cycles, "N = (Sq / A)^(1/B)", d=0)

# -----------------------------
# Horizontal tree (Graphviz)
# -----------------------------
g = graphviz.Digraph(graph_attr={"rankdir": "LR", "splines": "spline"})
g.attr("node", shape="rectangle", style="rounded,filled", fillcolor="white", color="#CBD5E1")

g.node("basic", "Basic Dimensions\np, D, Do, d, dh\n(t = (Do - D)/2)")
g.node("mat", "Material\nSut, Syt")
g.node("kfac", "K-factors\nka, kb, kc, kd, ke, kh, kl, km")

g.node("out", "Outputs →\nSe, Static FOS, Fatigue FOS, Life N", fillcolor="#F8FAFC")

g.edge("basic", "out")
g.edge("mat", "out")
g.edge("kfac", "out")

st.graphviz_chart(g, use_container_width=True)

# -----------------------------
# Notes
# -----------------------------
# with st.expander("Formulae (as implemented)"):
#     st.markdown(r"""
# - \( t = \frac{D_o - D}{2} \)  
# - \( S_h = \dfrac{p\,(t + 0.57D)}{100\,t} \)  
# - \( S_l = \dfrac{p\,D^2}{100\,(D_o^2 - D^2)} \)  
# - \( S_c = \sqrt{S_h^2 + S_l^2 - S_h S_l} \)  
# - \( S_a = S_m = \dfrac{S_c}{2} \)  
# - \( S_e = 0.5\,k_a k_b k_c k_d k_e k_h k_l k_m\,S_{ut} \)  
# - \( S_p = \dfrac{1}{ \dfrac{1}{S_e} + \dfrac{S_a}{S_m S_{ut}} } \)  
# - \( S_q = \dfrac{S_m}{1 - \dfrac{S_a}{S_{ut}}} \)  
# - \( B = \dfrac{\log_{10}(S_e) - \log_{10}(0.9 S_{ut})}{3} \)  
# - \( A = \dfrac{S_e}{10^{6B}} \)  
# - Static FOS \(= \dfrac{S_p}{S_a} \)  
# - Fatigue FOS \(= \dfrac{S_q}{S_a} \)  
# - Life cycles \( N = \left(\dfrac{S_q}{A}\right)^{\frac{1}{B}} \)
#     """)

# st.success("Ready. Change any input/slider to see outputs update instantly.")
