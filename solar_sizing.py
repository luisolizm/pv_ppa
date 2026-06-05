import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import copy
import requests
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors as rl_color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

st.set_page_config(page_title="Sizing Tool",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}  # opcional
)

# ═════════════════════════════════════════════════════════════════════════════
# AUTENTICACIÓN — password session-based
# La contraseña se lee de st.secrets["APP_PASSWORD"] (archivo .streamlit/secrets.toml).
# Fallback a variable de entorno APP_PASSWORD para entornos sin secrets.toml.
# NUNCA hardcodear la contraseña en el código fuente.
# ═════════════════════════════════════════════════════════════════════════════
import os as _os
try:
    _APP_PASSWORD = st.secrets["APP_PASSWORD"]
except Exception:
    _APP_PASSWORD = _os.environ.get("APP_PASSWORD", "1410")

def _check_auth():
    """Muestra pantalla de login si no hay sesión activa. Detiene el render."""
    if st.session_state.get("authenticated"):
        return  # ya autenticado — continuar normalmente

    # Pantalla de login centrada
    st.markdown("""
<style>
  .login-wrap {
    max-width: 380px; margin: 8vh auto 0; padding: 36px 40px;
    background: #111318; border: 1px solid #1e2230; border-radius: 16px;
  }
  .login-title { font-size: 22px; font-weight: 700; color: #f1f5f9;
                 margin-bottom: 4px; text-align: center; }
  .login-sub   { font-size: 13px; color: #475569; text-align: center;
                 margin-bottom: 28px; }
</style>
<div class="login-wrap">
  <div class="login-title">⚡ Sizing Tool</div>
  <div class="login-sub">Ingresa la contraseña para continuar</div>
</div>
""", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        pwd = st.text_input("Contraseña", type="password",
                            placeholder="••••••••", label_visibility="collapsed",
                            key="_login_pwd")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if pwd == _APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    st.stop()   # detiene el resto del render hasta que haya sesión válida

_check_auth()


# Forzar dark mode
st.markdown("""
<style>
  /* ── Fuentes ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"], button, label, p, span, div,
  .stMarkdown, .stTextInput, .stNumberInput, .stSlider, .stRadio, .stCheckbox {
    font-family: 'Inter', sans-serif !important;
  }

  /* ── Fondo global oscuro ── */
  [data-testid="stAppViewContainer"] { background: #0a0c10; }
  .main { background: #0a0c10; }
  [data-testid="stSidebar"] {
    background: #0e1117 !important;
    border-right: 1px solid #1e2230 !important;
  }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }

  /* ── Ocultar iconos de colapso sidebar ── */
  [data-testid="collapsedControl"] span,
  [data-testid="stSidebarCollapseButton"] span,
  span.material-symbols-rounded,
  span.material-symbols-outlined {
    font-size:0!important; visibility:hidden!important;
    width:0!important; height:0!important;
  }

  /* ── Tipografia monoespaciada ── */
  .mono { font-family: 'JetBrains Mono', monospace !important; }

  /* ── Cabecera ── */
  .app-title { font-size:28px; font-weight:700; color:#f1f5f9; letter-spacing:-0.6px; }
  .app-sub   { font-size:13px; color:#64748b; margin-top:-4px; margin-bottom:1.5rem; }

  /* ── Section header ── */
  .section-header {
    font-size:11px; font-weight:600; color:#475569;
    text-transform:uppercase; letter-spacing:0.12em;
    margin:1.6rem 0 0.8rem; padding-bottom:6px;
    border-bottom:1px solid #1e2230;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] { background:#111318; border-radius:10px; padding:4px; gap:4px; }
  .stTabs [data-baseweb="tab"]      { background:transparent; border-radius:8px; color:#64748b; font-weight:500; font-size:14px; }
  .stTabs [aria-selected="true"]    { background:#f59e0b !important; color:#0a0c10 !important; font-weight:600 !important; }

  /* ── Cajas informativas ── */
  .info-box { background:#111318; border-left:3px solid #f59e0b; border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#94a3b8; margin-bottom:1rem; }
  .nasa-box { background:#0b1623; border-left:3px solid #3b82f6; border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#93c5fd; margin-bottom:1rem; }
  .warn-box { background:#111318; border-left:3px solid #f43f5e; border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#94a3b8; margin-bottom:1rem; }

  /* ── TOR Hero ── */
  .tor-hero {
    background: linear-gradient(135deg, #111318 0%, #0d0f15 100%);
    border:1px solid #1e2230; border-radius:14px;
    padding:20px 24px; margin-bottom:1.4rem;
  }
  .tor-hero .th-project { font-size:10px; color:#475569; text-transform:uppercase; letter-spacing:0.10em; margin-bottom:4px; }
  .tor-hero .th-meta    { font-size:12px; color:#64748b; margin-bottom:16px; }
  .tor-hero .th-grid    { display:grid; grid-template-columns:repeat(4,1fr); gap:14px 20px; }
  .tor-hero .th-item    { display:flex; flex-direction:column; }
  .tor-hero .th-label   { font-size:10px; color:#475569; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:3px; }
  .tor-hero .th-val     { font-size:20px; font-weight:700; color:#f59e0b; font-family:'JetBrains Mono',monospace; line-height:1.1; word-break:break-word; }
  .tor-hero .th-unit    { font-size:11px; color:#64748b; margin-top:3px; }

  /* ── Badges PR ── */
  .pr-badge  { display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:500; }
  .pr-green  { background:#052e16; color:#4ade80; border:1px solid #166534; }
  .pr-yellow { background:#1c1a04; color:#facc15; border:1px solid #713f12; }
  .pr-red    { background:#1f0a0a; color:#f87171; border:1px solid #7f1d1d; }

  /* ── Panel card ── */
  .panel-card           { background:#111318; border:1px solid #1e2230; border-radius:12px; padding:14px 18px; margin-bottom:1rem; }
  .panel-card .pc-title { font-size:10px; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px; }
  .panel-card .pc-grid  { display:grid; grid-template-columns:1fr 1fr; gap:6px 16px; }
  .panel-card .pc-item  { display:flex; flex-direction:column; }
  .panel-card .pc-label { font-size:10px; color:#475569; }
  .panel-card .pc-val   { font-size:14px; font-weight:600; color:#f59e0b; font-family:'JetBrains Mono',monospace; }

  /* ── Snap cards KPI ── */
  .snap-card {
    background:#111318; border:1px solid #1e2230; border-radius:12px;
    padding:16px 12px; text-align:center;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    min-height:110px;
  }
  .snap-card .sc-label { font-size:10px; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; line-height:1.3; }
  .snap-card .sc-val   { font-size:clamp(14px,1.4vw,22px); font-weight:700; font-family:'JetBrains Mono',monospace; word-break:break-word; overflow-wrap:anywhere; line-height:1.2; max-width:100%; color:#e2e8f0; }
  .snap-card .sc-sub   { font-size:10px; color:#475569; margin-top:4px; line-height:1.3; }

  /* ── st.metric ── */
  [data-testid="stMetric"] { background:#111318; border:1px solid #1e2230; border-radius:12px; padding:14px 12px !important; text-align:center; }
  [data-testid="stMetricValue"] { font-family:'JetBrains Mono',monospace !important; font-size:clamp(13px,1.3vw,20px) !important; font-weight:700 !important; word-break:break-word !important; overflow-wrap:anywhere !important; white-space:normal !important; line-height:1.2 !important; color:#e2e8f0 !important; }
  [data-testid="stMetricLabel"] { font-family:'Inter',sans-serif !important; font-size:11px !important; color:#475569 !important; text-transform:uppercase; letter-spacing:0.06em; }

  /* ── Sidebar inputs ── */
  [data-testid="stSidebar"] input[type="number"],
  [data-testid="stSidebar"] input[type="text"],
  [data-testid="stSidebar"] .stTextInput input,
  [data-testid="stSidebar"] .stNumberInput input {
    background-color:#0a0c10 !important; color:#e2e8f0 !important;
    border:1px solid #2d3748 !important; border-radius:6px !important;
  }
  [data-testid="stSidebar"] input:focus { border-color:#f59e0b !important; box-shadow:0 0 0 2px rgba(245,158,11,0.2) !important; outline:none !important; }
  [data-testid="stSidebar"] [data-baseweb="input"],
  [data-testid="stSidebar"] [data-baseweb="base-input"] { background-color:#0a0c10 !important; }
  [data-testid="stSidebar"] [data-baseweb="input"] input,
  [data-testid="stSidebar"] [data-baseweb="base-input"] input { color:#e2e8f0 !important; background-color:#0a0c10 !important; caret-color:#f59e0b !important; }
  [data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"],
  [data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"] { background-color:#111318 !important; color:#e2e8f0 !important; border-color:#2d3748 !important; }
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background-color:#0a0c10 !important; border-color:#2d3748 !important; color:#e2e8f0 !important; }
  [data-testid="stSidebar"] label { color:#cbd5e1 !important; }

  .stDataFrame { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)
# ── Constants ─────────────────────────────────────────────────────────────────
MONTHS     = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
MONTH_DAYS = [31,28,31,30,31,30,31,31,30,31,30,31]
DEFAULT_IRR      = [4.8,5.2,5.9,6.1,5.8,5.4,5.3,5.2,4.7,4.5,4.6,4.5]
NASA_START, NASA_END = 2005, 2024
# Factor de emisión del Sistema Eléctrico Nacional (SEN) mexicano.
# Fuente: SEMARNAT / CRE — Aviso Factor de Emisión SEN 2024, publicado 28-Feb-2025.
# Valor oficial: 0.444 tCO₂e/MWh = 0.444 kg CO₂e/kWh.
# Actualizar anualmente conforme al aviso SEMARNAT más reciente.
CO2_FACTOR_KG_KWH = 0.444   # kg CO₂e/kWh  (SEN 2024 · SEMARNAT/CRE · 28-Feb-2025)


PLOT_LAYOUT = dict(
    paper_bgcolor="#0f1117", plot_bgcolor="#13151f",
    font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
    xaxis=dict(gridcolor="#2a2d3a", linecolor="#2a2d3a", tickcolor="#2a2d3a"),
    yaxis=dict(gridcolor="#2a2d3a", linecolor="#2a2d3a", tickcolor="#2a2d3a"),
    margin=dict(l=10, r=10, t=30, b=10),
)
AMBER="#f59e0b"; TEAL="#14b8a6"; ROSE="#f43f5e"; BLUE="#3b82f6"; VIOLET="#8b5cf6"


# ── NASA POWER ────────────────────────────────────────────────────────────────
# ── NASA POWER (2005–2024) ────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE INPUTS — deben definirse antes de cualquier tab
# ═════════════════════════════════════════════════════════════════════════════

def _bisection_irr(cash_flows: list) -> float | None:
    """
    Calcula la TIR de una serie de flujos de caja por bisección numérica.
    cash_flows[0] debe ser la inversión inicial (negativa).
    Criterio de convergencia doble: intervalo < 1e-10 O |NPV| < 1e-9.
    Retorna la TIR en porcentaje (%), o None si no converge o no hay solución.
    """
    def _npv(rr: float) -> float:
        return sum(c / (1 + rr) ** t for t, c in enumerate(cash_flows))
    try:
        lo, hi = -0.99, 5.0
        npv_lo = _npv(lo)
        npv_hi = _npv(hi)
        if npv_lo * npv_hi > 0:
            return None          # Sin cambio de signo → sin TIR en el rango
        for _ in range(200):
            mid = (lo + hi) / 2
            fm  = _npv(mid)
            if (hi - lo) / 2 < 1e-10:
                return mid * 100
            if abs(fm) < 1e-9:
                return mid * 100
            if npv_lo * fm < 0:
                hi = mid
            else:
                lo = mid
                npv_lo = fm
        return ((lo + hi) / 2) * 100
    except Exception:
        return None


def _safe(value, fallback=0.0, min_val=None, max_val=None, label="valor"):
    """Sanitiza valor numérico: reemplaza NaN/inf por fallback y clampea al rango."""
    try:
        v = float(value)
        if not math.isfinite(v): return fallback
        if min_val is not None and v < min_val: return min_val
        if max_val is not None and v > max_val: return max_val
        return v
    except (TypeError, ValueError): return fallback


def _validate_recibo_inputs(monthly_cons, monthly_tar):
    if not monthly_cons or not monthly_tar: return False, "Datos de consumo/tarifa vacíos."
    if len(monthly_cons) != 12 or len(monthly_tar) != 12: return False, "Se requieren 12 meses de datos."
    if sum(monthly_cons) <= 0: return False, "El consumo anual es cero. Ingresa al menos un mes con consumo."
    if any(c < 0 for c in monthly_cons): return False, "El consumo no puede ser negativo."
    if any(t <= 0 for t in monthly_tar): return False, "La tarifa debe ser mayor a cero en todos los meses."
    return True, ""



@st.cache_data(ttl=7200, show_spinner=False)
def get_nasa_power_irradiance(lat: float, lon: float):
    """
    Devuelve una tupla (irr_media, irr_por_anio):
      irr_media   : list[12]  — promedio climatológico mensual (kWh/m²/día)
      irr_por_anio: dict[int, list[12]] — irradiancia mensual de cada año
                    {2005: [v_ene, v_feb, …, v_dic], 2006: …}
    Valores inválidos (< 0 o None) se sustituyen por el promedio del mes.
    """
    url = (
        "https://power.larc.nasa.gov/api/temporal/monthly/point"
        "?parameters=ALLSKY_SFC_SW_DWN&community=RE"
        f"&longitude={lon}&latitude={lat}&format=JSON"
        f"&start={NASA_START}&end={NASA_END}"
    )

    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        data = r.json()

        raw = (data.get("properties", {})
                   .get("parameter", {})
                   .get("ALLSKY_SFC_SW_DWN", {}))

        if not raw:
            raise ValueError("NASA POWER no devolvió datos.")

        # ── 1. Construir serie por año ────────────────────────────────────────
        irr_por_anio: dict[int, list] = {}   # {año: [None]*12}
        monthly_sum   = [0.0] * 12
        monthly_count = [0]   * 12

        for key, value in raw.items():
            if len(key) != 6:
                continue
            try:
                year      = int(key[:4])
                month_idx = int(key[4:6]) - 1
                if not (0 <= month_idx <= 11):
                    continue
                if value is None or value < 0:
                    continue
                irr_por_anio.setdefault(year, [None] * 12)
                irr_por_anio[year][month_idx] = float(value)
                monthly_sum[month_idx]   += value
                monthly_count[month_idx] += 1
            except (ValueError, IndexError, TypeError):
                continue

        # ── 2. Promedio climatológico mensual ────────────────────────────────
        irr_media = [
            round(monthly_sum[i] / monthly_count[i], 4) if monthly_count[i] > 0
            else DEFAULT_IRR[i]
            for i in range(12)
        ]

        # ── 3. Rellenar meses faltantes en cada año con el promedio del mes ──
        for year, meses in irr_por_anio.items():
            for i in range(12):
                if meses[i] is None:
                    meses[i] = irr_media[i]

        return irr_media, irr_por_anio

    except requests.exceptions.Timeout:
        raise Exception("⏱️ Timeout: NASA POWER tardó demasiado.")
    except requests.exceptions.ConnectionError:
        raise Exception("🌐 Sin conexión a internet.")
    except Exception as e:
        raise Exception(f"❌ Error NASA POWER: {str(e)[:100]}")


# ── P90 riguroso: percentil 10 de la distribución de generaciones anuales ─────
def compute_p90(irr_por_anio: dict, kwp: float, pr: float) -> tuple:
    """
    Simula la generación anual para cada año histórico y devuelve:
      (p50_real, p90_real, gen_por_anio)
      p50_real    : mediana de las generaciones anuales (kWh)
      p90_real    : percentil 10 de las generaciones anuales (kWh)
                    — el sistema supera este valor el 90% de los años —
      gen_por_anio: dict {año: generación_kWh}
    Si no hay datos históricos, devuelve None para ambos percentiles.
    """
    if not irr_por_anio:
        return None, None, {}

    gen_por_anio = {}
    for year, meses in sorted(irr_por_anio.items()):
        gen_anual = sum(
            kwp * meses[m] * pr * MONTH_DAYS[m]
            for m in range(12)
        )
        gen_por_anio[year] = gen_anual

    valores = sorted(gen_por_anio.values())
    p50_real = float(np.percentile(valores, 50))
    p90_real = float(np.percentile(valores, 10))   # percentil 10 = excedido 90% de años
    return p50_real, p90_real, gen_por_anio

# ── Funciones de cálculo cacheadas ───────────────────────────────────────────

@st.cache_data(show_spinner=False)
def calc_sizing_area(area_total: float, occ_factor: int,
                     panel_wp: int, panel_area: float,
                     irr_vals: tuple, effective_pr: float) -> dict:
    """Sizing por área: número de paneles, kWp y generación mensual."""
    n_panels  = int(math.floor(area_total * occ_factor / 100 / panel_area))
    kwp       = n_panels * panel_wp / 1000
    area_util = area_total * occ_factor / 100
    area_used = n_panels * panel_area
    monthly_gen = [round(kwp * irr_vals[m] * effective_pr * MONTH_DAYS[m], 1) for m in range(12)]
    return dict(n_panels=n_panels, kwp=kwp, area_util=area_util,
                area_used=area_used, monthly_gen=monthly_gen,
                annual_gen=sum(monthly_gen))

@st.cache_data(show_spinner=False)
def calc_sizing_recibo_detallado(monthly_cons: tuple, monthly_tarifas: tuple,
                                  solar_pct: int, sizing_strategy: str,
                                  panel_wp: int, panel_area: float,
                                  irr_vals: tuple, effective_pr: float,
                                  occ_factor: int) -> dict:
    """
    Sizing con consumos y tarifas mensuales reales (12 valores cada uno).
    Devuelve kWp, generación, ahorro real mes a mes y tarifa media ponderada.
    """
    target_m = [c * solar_pct / 100 for c in monthly_cons]
    kwp_por_mes = [
        target_m[m] / (irr_vals[m] * effective_pr * MONTH_DAYS[m])
        if irr_vals[m] > 0 else 0 for m in range(12)
    ]
    kwp_raw  = max(kwp_por_mes) if "Peor" in sizing_strategy else sum(kwp_por_mes) / 12
    n_panels = int(math.ceil(kwp_raw * 1000 / panel_wp))
    kwp      = n_panels * panel_wp / 1000
    area_used = n_panels * panel_area
    area_util = area_used / (occ_factor / 100) if occ_factor > 0 else area_used
    monthly_gen = [round(kwp * irr_vals[m] * effective_pr * MONTH_DAYS[m], 1) for m in range(12)]

    # Ahorro real mes a mes: energía cubierta × tarifa de ese mes
    energia_cubierta = [min(monthly_gen[m], monthly_cons[m]) for m in range(12)]
    ahorro_mensual   = [energia_cubierta[m] * monthly_tarifas[m] for m in range(12)]
    excedente        = [monthly_gen[m] - monthly_cons[m] for m in range(12)]
    cobertura_pct    = [
        min(100.0, monthly_gen[m] / monthly_cons[m] * 100) if monthly_cons[m] > 0 else 0.0
        for m in range(12)
    ]

    consumo_anual = sum(monthly_cons)
    gasto_actual  = sum(monthly_cons[m] * monthly_tarifas[m] for m in range(12))
    tarifa_media_pond = gasto_actual / consumo_anual if consumo_anual > 0 else 0

    return dict(
        n_panels=n_panels, kwp=kwp, area_util=area_util, area_used=area_used,
        monthly_gen=monthly_gen, annual_gen=sum(monthly_gen),
        monthly_cons=list(monthly_cons),
        energia_cubierta=energia_cubierta,
        ahorro_mensual=ahorro_mensual,
        ahorro_anual=sum(ahorro_mensual),
        excedente=excedente,
        cobertura_pct=cobertura_pct,
        cobertura_anual=sum(energia_cubierta) / consumo_anual * 100 if consumo_anual > 0 else 0,
        gasto_actual=gasto_actual,
        tarifa_media_pond=tarifa_media_pond,
        monthly_tarifas=list(monthly_tarifas),
    )


@st.cache_data(show_spinner=False)
def calc_sizing_recibo_kwp(monthly_cons: tuple, monthly_tarifas: tuple,
                            kwp_manual: float,
                            panel_wp: int, panel_area: float,
                            irr_vals: tuple, effective_pr: float,
                            occ_factor: int = 75) -> dict:
    """
    Sizing con kWp fijado manualmente por el usuario.
    Redondea al número entero de paneles más cercano y calcula
    cobertura, generación y ahorro reales mes a mes.
    occ_factor: porcentaje de ocupación del área disponible (%), configurable.
    FIX: antes usaba factor fijo del 75%; ahora usa el valor del usuario.
    """
    n_panels  = max(1, round(kwp_manual * 1000 / panel_wp))
    kwp       = n_panels * panel_wp / 1000
    area_used = n_panels * panel_area
    # FIX: área bruta requerida usa el occ_factor configurado por el usuario,
    # no el valor hardcodeado al 75%.
    occ_ratio = max(occ_factor, 1) / 100
    area_util = area_used / occ_ratio

    monthly_gen      = [round(kwp * irr_vals[m] * effective_pr * MONTH_DAYS[m], 1) for m in range(12)]
    energia_cubierta = [min(monthly_gen[m], monthly_cons[m]) for m in range(12)]
    ahorro_mensual   = [energia_cubierta[m] * monthly_tarifas[m] for m in range(12)]
    excedente        = [monthly_gen[m] - monthly_cons[m] for m in range(12)]
    cobertura_pct    = [
        min(100.0, monthly_gen[m] / monthly_cons[m] * 100) if monthly_cons[m] > 0 else 0.0
        for m in range(12)
    ]
    consumo_anual     = sum(monthly_cons)
    gasto_actual      = sum(monthly_cons[m] * monthly_tarifas[m] for m in range(12))
    tarifa_media_pond = gasto_actual / consumo_anual if consumo_anual > 0 else 0.0

    return dict(
        n_panels=n_panels, kwp=kwp, area_util=area_util, area_used=area_used,
        monthly_gen=monthly_gen, annual_gen=sum(monthly_gen),
        monthly_cons=list(monthly_cons),
        energia_cubierta=energia_cubierta,
        ahorro_mensual=ahorro_mensual,
        ahorro_anual=sum(ahorro_mensual),
        excedente=excedente,
        cobertura_pct=cobertura_pct,
        cobertura_anual=sum(energia_cubierta) / consumo_anual * 100 if consumo_anual > 0 else 0,
        gasto_actual=gasto_actual,
        tarifa_media_pond=tarifa_media_pond,
        monthly_tarifas=list(monthly_tarifas),
    )


@st.cache_data(show_spinner=False)
def calc_financial_model(annual_gen: float, kwp: float, inversion_usd: float,
                         tarifa_efectiva: float, inflation: float,
                         discount_rate: float, panel_degradation: float,
                         vida_util: int, usd_to_mxn: float,
                         om_pct: float = 1.0) -> dict:
    """Modelo financiero completo: VPN, TIR, payback, LCOE, flujos anuales.
    om_pct: porcentaje de la inversión MXN destinado a O&M anual (default 1.0 %).
    """
    years = list(range(1, vida_util + 1))
    r     = discount_rate / 100
    inv_mxn = inversion_usd * usd_to_mxn

    gen_proj      = [annual_gen * (1 - panel_degradation / 100) ** (y - 1) for y in years]
    tarifas_y     = [tarifa_efectiva * (1 + inflation / 100) ** (y - 1) for y in years]
    flujo_nominal = [gen_proj[i] * tarifas_y[i] for i in range(len(years))]
    # FIX: O&M ahora usa om_pct en vez de valor hardcodeado al 1%
    om_anual      = [inv_mxn * (om_pct / 100) * (1 + inflation / 100) ** (y - 1) for y in years]
    flujo_neto    = [flujo_nominal[i] - om_anual[i] for i in range(len(years))]
    factor_desc   = [1 / (1 + r) ** y for y in years]
    flujo_desc    = [flujo_neto[i] * factor_desc[i] for i in range(len(years))]

    acum_nominal, acum = [], -inv_mxn
    for fn in flujo_neto:
        acum += fn; acum_nominal.append(acum)
    acum_desc, acum = [], -inv_mxn
    for fd in flujo_desc:
        acum += fd; acum_desc.append(acum)

    vpn = acum_desc[-1]

    # TIR — función compartida a nivel de módulo (_bisection_irr)
    tir = _bisection_irr([-inv_mxn] + flujo_neto)

    # FIX: payback con interpolación lineal (antes devolvía el año entero, ahora da fracción)
    pb_simple = None
    for i, v in enumerate(acum_nominal):
        if v >= 0:
            prev = acum_nominal[i - 1] if i > 0 else -inv_mxn
            pb_simple = round(years[i] - 1 + (-prev) / (v - prev), 1)
            break

    pb_disc = None
    for i, v in enumerate(acum_desc):
        if v >= 0:
            prev = acum_desc[i - 1] if i > 0 else -inv_mxn
            pb_disc = round(years[i] - 1 + (-prev) / (v - prev), 1)
            break

    total_gen_desc  = sum(gen_proj[i] * factor_desc[i] for i in range(len(years)))
    total_cost_desc = inv_mxn + sum(om_anual[i] * factor_desc[i] for i in range(len(years)))
    lcoe = total_cost_desc / total_gen_desc if total_gen_desc > 0 else 0

    return dict(
        vpn=vpn, tir=tir, pb_simple=pb_simple, pb_disc=pb_disc, lcoe=lcoe,
        years=years, gen_proj=gen_proj, tarifas_y=tarifas_y,
        flujo_nominal=flujo_nominal, om_anual=om_anual, flujo_neto=flujo_neto,
        factor_desc=factor_desc, flujo_desc=flujo_desc,
        acum_nominal=acum_nominal, acum_desc=acum_desc, inv_mxn=inv_mxn,
    )


@st.cache_data(show_spinner=False)
def calc_ppa_result(gen1: float, inv_usd: float, precio_ppa: float,
                    plazo: int, wacc_pct: float, esc_ppa: float,
                    deg: float, om_pct: float, inf_om: float,
                    seg_pct: float, usd_mx: float, equity_pct: float,
                    tasa_deuda: float, plazo_deuda: int, con_fin: bool,
                    vida_util_total: int = 25) -> dict:
    """Resultado financiero PPA para un plazo dado — perspectiva equity.

    Los flujos fn_y son flujos de caja al accionista (FCFE): ingresos PPA menos
    O&M, seguro y servicio de deuda. El VPN y el payback descontado se calculan
    usando el costo del equity (Ke), no el WACC, para mantener consistencia entre
    la tasa de descuento y los flujos que se descuentan.

    Ke se estima con el modelo MM sin impuestos (Modigliani-Miller):
        Ke = WACC + (D/E) * (WACC - Kd)
    Cuando no hay financiamiento (con_fin=False o deuda=0), Ke = WACC.

    vida_util_total: vida útil del sistema (años). Se usa para calcular el valor
    residual al final del contrato PPA si plazo < vida_util_total.
    """
    inv_mxn    = inv_usd * usd_mx
    equity_mxn = inv_mxn * (equity_pct / 100)
    deuda_mxn  = inv_mxn - equity_mxn
    if con_fin and tasa_deuda > 0 and plazo_deuda > 0 and deuda_mxn > 0:
        r_d = tasa_deuda / 100
        serv_deuda = deuda_mxn * r_d / (1 - (1 + r_d) ** (-plazo_deuda))
    else:
        serv_deuda = 0.0; deuda_mxn = 0.0; equity_mxn = inv_mxn

    r = wacc_pct / 100   # WACC — se usa sólo para referencia y valor residual sin deuda

    # ── Costo del equity (Ke) ─────────────────────────────────────────────────
    # fn_y son flujos post-deuda (FCFE). Deben descontarse con Ke, no con WACC.
    # Ke = WACC + (D/E) * (WACC - Kd)  [MM sin impuestos]
    # Cuando equity_mxn == 0 (caso degenerado) se usa WACC como fallback.
    if equity_mxn > 0 and deuda_mxn > 0:
        ke = r + (deuda_mxn / equity_mxn) * (r - r_d)
        # Acotamos Ke al rango [WACC, 3×WACC] para evitar valores explosivos
        # con estructuras de capital muy apalancadas.
        ke = max(r, min(ke, 3 * r)) if r > 0 else r
    else:
        ke = r   # sin deuda: Ke = WACC (estructura 100 % equity)

    years  = list(range(1, plazo + 1))
    gen_y  = [gen1 * (1 - deg / 100) ** i for i in range(plazo)]
    prec_y = [precio_ppa * (1 + esc_ppa / 100) ** i for i in range(plazo)]
    ing_y  = [gen_y[i] * prec_y[i] for i in range(plazo)]
    om_y   = [inv_mxn * om_pct  / 100 * (1 + inf_om / 100) ** i for i in range(plazo)]
    seg_y  = [inv_mxn * seg_pct / 100 * (1 + inf_om / 100) ** i for i in range(plazo)]
    deu_y  = [serv_deuda if y <= plazo_deuda else 0.0 for y in years]
    fn_y   = [ing_y[i] - om_y[i] - seg_y[i] - deu_y[i] for i in range(plazo)]
    # FIX: se descuenta con Ke (costo del equity) en vez de WACC,
    # ya que fn_y son flujos post-deuda (FCFE).
    fd_y   = [fn_y[i] / (1 + ke) ** years[i] for i in range(plazo)]

    # Valor residual del sistema al final del contrato PPA
    # Si el contrato es más corto que la vida útil, el activo sigue generando valor.
    # Se estima como VPN de los flujos futuros post-contrato usando una anuidad con
    # crecimiento (fórmula de Gordon) que incorpora tanto el escalador PPA como la
    # degradación anual del panel — evita sobreestimar el valor al asumir flujo constante.
    anios_restantes = max(0, vida_util_total - plazo)
    if anios_restantes > 0 and ke > 0:
        gen_post  = gen_y[-1] * (1 - deg / 100)       # generación año plazo+1
        prec_post = prec_y[-1] * (1 + esc_ppa / 100)  # precio PPA escalado
        om_post   = om_y[-1]  * (1 + inf_om / 100)    # O&M escalado
        seg_post  = seg_y[-1] * (1 + inf_om / 100)
        fn_post   = gen_post * prec_post - om_post - seg_post  # noqa: F841

        # Tasa de crecimiento neta del flujo post-contrato:
        # el ingreso crece con (escalador_ppa - degradación), los costos con inf_om.
        g_ingreso = (esc_ppa / 100) - (deg / 100)   # puede ser negativo si deg > esc_ppa
        g_costos  = inf_om / 100
        # NOTA: cuando g_ingreso < 0 (degradación supera el escalador PPA), los ingresos
        # post-contrato decrecen año a año. _gordon_pv lo maneja correctamente via suma
        # finita; el valor residual puede resultar negativo o bajo, lo cual es matemáticamente
        # válido y conservador. No se clampea a cero para no ocultar proyectos no viables.

        # Anuidad con crecimiento compuesto (Gordon generalizado):
        # PV = F1 * [(1 - ((1+g)/(1+ke))^n) / (ke - g)]   si ke ≠ g
        # PV = F1 * n / (1+ke)                              si ke ≈ g  (límite exacto)
        # Calculamos cada componente (ingresos y costos) por separado para
        # mayor precisión cuando fn_post puede ser negativo.
        def _gordon_pv(f1: float, g: float, n: int, discount: float) -> float:
            """VPN de una anuidad con crecimiento g durante n períodos, traída a hoy.
            Usa la suma exacta de n términos en todos los casos para evitar
            divergencia cuando g >= discount (escalador > Ke).
            La fórmula cerrada de Gordon diverge cuando g >= r, por lo que
            siempre calculamos la suma finita directamente.
            """
            if n <= 0:
                return 0.0
            # Suma finita exacta: PV = sum_{t=1}^{n} f1*(1+g)^(t-1) / (1+ke)^t
            # = f1/(1+ke) * sum_{t=0}^{n-1} ((1+g)/(1+ke))^t
            ratio = (1 + g) / (1 + discount)
            if abs(ratio - 1.0) < 1e-9:
                return f1 * n / (1 + discount)
            return f1 / (1 + discount) * (1 - ratio ** n) / (1 - ratio)

        # FIX: el valor residual también usa Ke para consistencia con fd_y.
        pv_ingresos = _gordon_pv(gen_post * prec_post, g_ingreso, anios_restantes, ke)
        pv_costos   = _gordon_pv(om_post + seg_post,   g_costos,  anios_restantes, ke)
        # _gordon_pv devuelve el VPN de los flujos post-contrato al instante t=0
        # suponiendo que el primer flujo cae en t=1. Como los flujos post-contrato
        # empiezan en t=plazo+1, se descuenta `plazo` períodos adicionales con Ke.
        valor_residual = (pv_ingresos - pv_costos) / (1 + ke) ** plazo
    else:
        valor_residual = 0.0

    vpn = -equity_mxn + sum(fd_y) + valor_residual

    # TIR — función compartida a nivel de módulo (_bisection_irr)
    tir = _bisection_irr([-equity_mxn] + fn_y)

    # Payback simple — acumulado sobre flujos nominales
    pb = None
    acum_pb = -equity_mxn
    for i, fn in enumerate(fn_y):
        prev_acum = acum_pb
        acum_pb  += fn
        if acum_pb >= 0:
            pb = round(years[i] - 1 + (-prev_acum) / (acum_pb - prev_acum), 1)
            break

    # Payback descontado — acumulado sobre flujos descontados (fd_y)
    pb_disc = None
    acum_disc = -equity_mxn
    for i, fd in enumerate(fd_y):
        prev_disc = acum_disc
        acum_disc += fd
        if acum_disc >= 0:
            pb_disc = round(years[i] - 1 + (-prev_disc) / (acum_disc - prev_disc), 1)
            break

    return dict(vpn=vpn, tir=tir, pb=pb, pb_disc=pb_disc, ing_total=sum(ing_y),
                fn_y=fn_y, fd_y=fd_y, ing_y=ing_y, om_y=om_y,
                seg_y=seg_y, gen_y=gen_y, prec_y=prec_y, deu_y=deu_y,
                equity_mxn=equity_mxn, inv_mxn=inv_mxn, years=years,
                valor_residual=valor_residual,
                ke_pct=ke * 100,        # Ke usado para descontar fd_y (% anual)
                wacc_pct=wacc_pct)      # WACC de referencia del usuario (%)


@st.cache_data(show_spinner=False)
def calc_precio_minimo(gen1: float, inv_usd: float, plazo: int,
                       wacc_pct: float, esc_ppa: float, deg: float,
                       om_pct: float, inf_om: float, seg_pct: float,
                       usd_mx: float, equity_pct: float,
                       tasa_deuda: float, plazo_deuda: int, con_fin: bool,
                       vida_util_total: int = 25):
    """Precio mínimo PPA (VPN=0) por bisección. Cacheado."""
    lo, hi = 0.01, 20.0
    def vpn_at(p):
        return calc_ppa_result(gen1, inv_usd, p, plazo, wacc_pct, esc_ppa,
                               deg, om_pct, inf_om, seg_pct, usd_mx,
                               equity_pct, tasa_deuda, plazo_deuda, con_fin,
                               vida_util_total)["vpn"]
    if vpn_at(hi) < 0: return None
    for _ in range(80):
        mid = (lo+hi)/2
        if vpn_at(mid) >= 0: hi = mid
        else: lo = mid
    return round((lo+hi)/2, 4)

@st.cache_data(show_spinner=False)
def calc_precio_hurdle(gen1: float, inv_usd: float, plazo: int,
                       wacc_pct: float, spread_pct: float,
                       esc_ppa: float, deg: float,
                       om_pct: float, inf_om: float, seg_pct: float,
                       usd_mx: float, equity_pct: float,
                       tasa_deuda: float, plazo_deuda: int, con_fin: bool,
                       vida_util_total: int = 25):
    """Precio PPA donde TIR equity = WACC + spread (hurdle rate).
    Usa bisección sobre la función TIR. Retorna None si no existe solución.
    """
    tir_objetivo = wacc_pct + spread_pct
    def tir_at(p):
        r = calc_ppa_result(gen1, inv_usd, p, plazo, wacc_pct, esc_ppa,
                            deg, om_pct, inf_om, seg_pct, usd_mx,
                            equity_pct, tasa_deuda, plazo_deuda, con_fin,
                            vida_util_total)
        return r["tir"] if r["tir"] is not None else -999.0
    lo, hi = 0.01, 20.0
    # Verificar que el rango es válido
    if tir_at(hi) < tir_objetivo: return None
    if tir_at(lo) > tir_objetivo: return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if tir_at(mid) >= tir_objetivo: hi = mid
        else: lo = mid
    return round((lo + hi) / 2, 4)


# ─────────────────────────────────────────────────────────────────────────────
# WORD — Generación de caso de negocio
# Invoca scripts Node.js (docx-js) pasando datos como JSON.
# ─────────────────────────────────────────────────────────────────────────────
import json as _json, subprocess as _subprocess, tempfile as _tempfile

def _get_logo_b64() -> str | None:
    """Retorna el logo en base64 si existe logo.png junto al script."""
    import os as _os, base64 as _b64
    _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.png")
    if _os.path.exists(_p):
        with open(_p, "rb") as _f:
            return _b64.b64encode(_f.read()).decode()
    return None


def _find_node() -> str:
    """Encuentra el ejecutable de Node.js en Windows y Unix."""
    import shutil as _shutil, os as _os
    node = _shutil.which("node")
    if node:
        return node
    _candidates = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        _os.path.expandvars(r"%APPDATA%\npm\node.exe"),
        _os.path.expandvars(r"%ProgramFiles%\nodejs\node.exe"),
    ]
    for _c in _candidates:
        if _os.path.exists(_c):
            return _c
    raise RuntimeError(
        "Node.js no encontrado. Instálalo desde https://nodejs.org "
        "y asegura que 'node' este en el PATH del entorno donde corre Streamlit. "
        "Prueba: abrir la terminal donde lanzas 'streamlit run' y ejecutar 'node --version'."
    )


def _run_word_script(script_path: str, data: dict) -> bytes:
    """Escribe data como JSON, ejecuta el script Node y retorna los bytes del .docx."""
    import os as _os
    _tmp       = _tempfile.gettempdir()
    _json_path = _os.path.join(_tmp, "sz_word_data.json")
    _out       = _os.path.join(_tmp, "sz_word_output.docx")

    with open(_json_path, "w", encoding="utf-8") as _jf:
        _json.dump(data, _jf, ensure_ascii=False, default=str)

    if _os.path.exists(_out):
        _os.remove(_out)

    _node = _find_node()
    _env  = {**_os.environ, "WORD_DATA": _json_path, "WORD_OUT": _out}

    res = _subprocess.run(
        [_node, script_path],
        capture_output=True, text=True, timeout=90, env=_env,
    )
    if res.returncode != 0 or not _os.path.exists(_out):
        _detail = (res.stderr or res.stdout or "sin salida")[:800]
        raise RuntimeError(f"Node.js error (rc={res.returncode}): {_detail}")
    with open(_out, "rb") as _f:
        return _f.read()


def _esc_turnkey(fm: dict, vida_util: int, wacc: float,
                 kwp: float, inversion_mxn: float, inflacion_cfe: float,
                 p90_real, annual_gen: float) -> dict:
    """Construye los tres escenarios de sensibilidad para Turnkey."""
    import datetime as _dt

    def _run(capex_factor, inf_factor, gen_base):
        _inv_mxn_s = inversion_mxn * capex_factor
        _tar_s     = fm["tarifas_y"][0] * 1.0  # tarifa año 1 base
        _inf_s     = (inflacion_cfe + inf_factor)
        _gen_s     = gen_base
        _fm_s = calc_financial_model(
            _gen_s, kwp, _inv_mxn_s / 17.0,  # reconvertir a USD aprox (solo para la función)
            _tar_s, _inf_s, wacc,
            fm.get("panel_degradation", 0.5), vida_util,
            17.0, fm.get("om_pct", 1.0)
        )
        return _fm_s

    gen_p90 = p90_real if p90_real else annual_gen * 0.92
    gen_best = annual_gen * 1.05

    def _fmt(s):
        _tir = f"{s['tir']:.1f}%" if s['tir'] else "N/A"
        _vpn = f"${s['vpn']/1e6:.2f}M MXN"
        _pb  = f"{s['pb_simple']:.1f}a" if s['pb_simple'] else f">{vida_util}a"
        _pbd = f"{s['pb_disc']:.1f}a"  if s['pb_disc']  else f">{vida_util}a"
        _lco = f"${s['lcoe']:.2f}/kWh"
        return dict(tir=_tir, vpn=_vpn, pb=_pb, pb_disc=_pbd, lcoe=_lco)

    base_s  = _fmt(fm)
    best_fm = _run(0.90, +3.0, gen_best)
    worst_fm= _run(1.15, -2.0, gen_p90)

    return {
        "base":  {**_fmt(fm),  "nota": f"CAPEX base · Inflación CFE {inflacion_cfe:.1f}% · Gen P50"},
        "best":  {**_fmt(best_fm),  "nota": f"CAPEX -10% · Inflación CFE +3pts · Gen +5%"},
        "worst": {**_fmt(worst_fm), "nota": f"CAPEX +15% · Inflación CFE -2pts · Gen P90"},
    }


def _esc_ppa(resultados: dict, plazo_obj: int, ppa_cache_kwargs: dict,
             ppa_precio_manual: float, ppa_spread_hurdle: float,
             ppa_usar_valor_residual: bool, vida_util: int) -> dict:
    """Construye escenarios Best/Base/Worst para PPA sobre el plazo objetivo."""

    def _run_esc(precio_factor, capex_factor, wacc_delta, esc_delta):
        _kw = dict(ppa_cache_kwargs)
        _kw["inv_usd"]  = _kw["inv_usd"]  * capex_factor
        _kw["wacc_pct"] = _kw["wacc_pct"] + wacc_delta
        _kw["esc_ppa"]  = max(0.0, _kw["esc_ppa"] + esc_delta)
        _vu = vida_util if ppa_usar_valor_residual else plazo_obj
        _kw["vida_util_total"] = _vu
        _precio = ppa_precio_manual * precio_factor
        res = calc_ppa_result(precio_ppa=_precio, plazo=plazo_obj, **_kw)
        _tir = f"{res['tir']:.1f}%" if res['tir'] else "N/A"
        _vpn = f"${res['vpn']/1e6:.2f}M MXN"
        _pb  = f"{res['pb']:.1f}a" if res['pb'] else f">{plazo_obj}a"
        return dict(tir=_tir, vpn=_vpn, pb=_pb)

    ro = resultados[plazo_obj]
    base_tir = f"{ro['tir']:.1f}%" if ro['tir'] else "N/A"
    base_vpn = f"${ro['vpn']/1e6:.2f}M MXN"
    base_pb  = f"{ro['pb']:.1f}a" if ro['pb'] else f">{plazo_obj}a"

    best  = _run_esc(1.10, 0.90, -2.0, +1.0)
    worst = _run_esc(0.85, 1.15, +2.0, -1.0)

    wacc_b = ppa_cache_kwargs["wacc_pct"]
    esc_b  = ppa_cache_kwargs["esc_ppa"]

    return {
        "base":  {"tir": base_tir, "vpn": base_vpn, "pb": base_pb,
                  "nota": f"CAPEX base · Precio ${ppa_precio_manual:.4f} · WACC {wacc_b:.1f}% · Esc. {esc_b:.1f}%"},
        "best":  {**best,  "nota": f"CAPEX -10% · Precio +10% · WACC -2pts · Esc. +1pt"},
        "worst": {**worst, "nota": f"CAPEX +15% · Precio -15% · WACC +2pts · Esc. -1pt"},
    }


# ── Generadores de imágenes para el Word ──────────────────────────────────────
import base64 as _b64

def _gen_chart_b64(irr_vals: list, monthly_gen: list, kwp: float) -> str | None:
    """
    PNG base64: barras de generación mensual (MWh) + línea GHI NASA POWER.
    Retorna None si matplotlib no está disponible o hay error.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        months = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        gen_mwh = [v / 1000 for v in monthly_gen]
        x = np.arange(12)

        fig, ax1 = plt.subplots(figsize=(7.8, 2.7))
        fig.patch.set_facecolor("white")
        ax1.set_facecolor("#F8FAFC")

        ax1.bar(x, gen_mwh, color="#F59E0B", alpha=0.88, width=0.55, zorder=3, label="Generación (MWh)")
        ax1.set_xticks(x); ax1.set_xticklabels(months, fontsize=9)
        ax1.set_ylabel("Generación (MWh)", fontsize=9, color="#374151")
        ax1.tick_params(axis="y", colors="#374151", labelsize=8)
        ax1.set_ylim(0, max(gen_mwh) * 1.45)
        ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)
        ax1.spines["left"].set_color("#E5E7EB"); ax1.spines["bottom"].set_color("#E5E7EB")
        ax1.yaxis.grid(True, color="#E5E7EB", zorder=0); ax1.set_axisbelow(True)

        ax2 = ax1.twinx()
        ax2.plot(x, irr_vals, color="#14B8A6", linewidth=2.2, marker="o", markersize=5, zorder=4, label="GHI (kWh/m²/día)")
        ax2.set_ylabel("GHI (kWh/m²/día)", fontsize=9, color="#14B8A6")
        ax2.tick_params(axis="y", colors="#14B8A6", labelsize=8)
        ax2.set_ylim(0, max(irr_vals) * 1.6)
        ax2.spines["top"].set_visible(False); ax2.spines["right"].set_color("#14B8A6")

        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8, framealpha=0.92, edgecolor="#E5E7EB")
        fig.text(0.01, -0.04, f"Sistema {kwp:.0f} kWp  ·  Fuente: NASA POWER 2005–2024  ·  PR configurado por usuario",
                 fontsize=7.5, color="#9CA3AF", ha="left")

        fig.tight_layout(pad=0.5)
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0); plt.close(fig)
        return _b64.b64encode(buf.read()).decode()
    except Exception:
        return None


def _gen_coverage_chart_b64(monthly_cons: list, monthly_gen: list, kwp: float) -> str | None:
    """
    PNG base64: barras apiladas (solar cubierto + complemento CFE) + línea generación total.
    Solo se llama cuando hay datos reales de recibo (consumo_anual > 0).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        months = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        consumo   = [float(v) for v in monthly_cons]
        gen_total = [float(v) for v in monthly_gen]
        cubierto  = [min(consumo[i], gen_total[i]) for i in range(12)]
        no_cub    = [consumo[i] - cubierto[i] for i in range(12)]
        cob_anual = sum(cubierto) / sum(consumo) * 100 if sum(consumo) > 0 else 0

        x = np.arange(12)
        fig, ax = plt.subplots(figsize=(7.8, 2.9))
        fig.patch.set_facecolor("white"); ax.set_facecolor("#F8FAFC")

        ax.bar(x, cubierto, color="#F59E0B", width=0.58, zorder=3, label="Cubierto solar")
        ax.bar(x, no_cub,   color="#374151", width=0.58, bottom=cubierto, zorder=3, label="Consumo CFE")
        ax.plot(x, gen_total, color="#14B8A6", linewidth=2.0, linestyle="--",
                marker="o", markersize=5, zorder=5, label="Generación total")

        ax.set_xticks(x); ax.set_xticklabels(months, fontsize=9)
        ax.set_ylabel("kWh", fontsize=9, color="#374151")
        ax.tick_params(axis="y", colors="#374151", labelsize=8)
        ax.set_ylim(0, max(max(consumo), max(gen_total)) * 1.38)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#E5E7EB"); ax.spines["bottom"].set_color("#E5E7EB")
        ax.yaxis.grid(True, color="#E5E7EB", zorder=0, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.92, edgecolor="#E5E7EB", ncol=3)
        ax.set_title(f"Generación vs Consumo Mensual  ·  Cobertura anual estimada: {cob_anual:.0f}%",
                     fontsize=9, color="#374151", loc="left", pad=6)
        fig.text(0.01, -0.04,
                 f"Sistema {kwp:.0f} kWp  ·  Fuente consumo: recibos CFE ingresados  ·  Generación: NASA POWER 2005–2024",
                 fontsize=7.5, color="#9CA3AF", ha="left")

        fig.tight_layout(pad=0.5)
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0); plt.close(fig)
        return _b64.b64encode(buf.read()).decode()
    except Exception:
        return None


def _gen_map_b64(lat: float, lon: float, location_label: str) -> str | None:
    """
    PNG base64: tarjeta de ubicación con pin (sin tiles externos).
    Retorna None si matplotlib no está disponible o hay error.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(3.6, 2.4))
        fig.patch.set_facecolor("#EFF6FF"); ax.set_facecolor("#DBEAFE")
        ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
        ax.set_aspect("equal"); ax.axis("off")

        shadow = plt.Circle((0.06, -0.08), 0.30, color="#93C5FD", alpha=0.4, zorder=2)
        ax.add_patch(shadow)
        pin = plt.Circle((0, 0.10), 0.30, color="#F59E0B", zorder=4)
        ax.add_patch(pin)
        ax.plot([0, 0], [-0.65, -0.20], color="#F59E0B", linewidth=5, zorder=3, solid_capstyle="round")
        ax.plot(0, 0.10, "o", color="white", markersize=11, zorder=5)

        ax.text(0, -0.82, f"{lat:.4f}°N, {lon:.4f}°W",
                ha="center", va="top", fontsize=8.5, color="#1E40AF", fontweight="bold")
        label = location_label if len(location_label) <= 28 else location_label[:26] + "…"
        ax.text(0, 1.10, label, ha="center", va="top", fontsize=7.5, color="#374151", style="italic")
        ax.text(0, -1.05, "UBICACIÓN DEL PROYECTO",
                ha="center", va="top", fontsize=6.5, color="#6B7280", fontweight="bold")

        fig.tight_layout(pad=0.2)
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#EFF6FF")
        buf.seek(0); plt.close(fig)
        return _b64.b64encode(buf.read()).decode()
    except Exception:
        return None


def build_word_turnkey(
    proj_loc, lat, lon, fecha,
    kwp, n_panels, panel_wp, panel_eff_declared, panel_largo_mm, panel_ancho_mm, panel_peso_kg,
    area_used, inversion_usd, inversion_mxn, usd_to_mxn, costo_kwp,
    ahorro1, co2_saved_t, hsp_anual, annual_gen, p50, p90_real,
    pr_pct, panel_degradation, vida_util, wacc, inflacion_cfe,
    tarifa_efectiva, om_pct_sidebar,
    vpn, tir, pb_simple, pb_disc, lcoe,
    fm: dict,
    consumo_anual, cobertura_pct,
    # Parámetros para las gráficas (opcionales hacia atrás):
    irr_vals: list = None,
    monthly_gen: list = None,
    monthly_cons: list = None,
) -> bytes:
    import os as _os
    escenarios = _esc_turnkey(
        fm, vida_util, wacc, kwp, inversion_mxn, inflacion_cfe,
        p90_real, annual_gen
    )

    # Generar imágenes para el documento
    chart_b64    = _gen_chart_b64(irr_vals, monthly_gen, kwp) \
                   if irr_vals and monthly_gen else None
    coverage_b64 = _gen_coverage_chart_b64(monthly_cons, monthly_gen, kwp) \
                   if monthly_cons and monthly_gen and consumo_anual and consumo_anual > 0 else None
    map_b64      = _gen_map_b64(lat, lon, proj_loc)

    data = {
        "logo_b64":        _get_logo_b64(),
        "fecha":           fecha,
        "ubicacion":       proj_loc,
        "lat":             lat, "lon": lon,
        "kwp":             kwp, "n_panels": n_panels,
        "panel_wp":        panel_wp,
        "panel_eff":       panel_eff_declared,
        "panel_largo":     panel_largo_mm,
        "panel_ancho":     panel_ancho_mm,
        "panel_peso":      panel_peso_kg,
        "area_usada":      area_used,
        "inversion_usd":   int(inversion_usd),
        "inversion_mxn":   int(inversion_mxn),
        "usd_to_mxn":      usd_to_mxn,
        "costo_kwp":       costo_kwp,
        "ahorro1":         ahorro1,
        "co2_t":           co2_saved_t,
        "co2_factor":      CO2_FACTOR_KG_KWH,
        "hsp":             hsp_anual,
        "gen_p50":         p50,
        "gen_p90":         p90_real,
        "pr_pct":          pr_pct,
        "degradacion":     panel_degradation,
        "vida_util":       vida_util,
        "wacc":            wacc,
        "inflacion_cfe":   inflacion_cfe,
        "tarifa_efectiva": tarifa_efectiva,
        "om_pct":          om_pct_sidebar,
        "consumo_anual":   consumo_anual if consumo_anual else 0,
        "cobertura_pct":   cobertura_pct if cobertura_pct else 0,
        "vpn":             vpn,
        "tir_str":         f"{tir:.1f}%" if tir else "N/A",
        "pb_simple":       f"{pb_simple:.1f}" if pb_simple else None,
        "pb_disc":         f"{pb_disc:.1f}" if pb_disc else None,
        "lcoe":            lcoe,
        "escenarios":      escenarios,
        # Imágenes embebidas:
        "chart_b64":       chart_b64,
        "coverage_b64":    coverage_b64,
        "map_b64":         map_b64,
    }
    _script = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "word_gen", "gen_turnkey.js")
    return _run_word_script(_script, data)


def build_word_ppa(
    proj_loc, lat, lon, fecha,
    kwp, n_panels, inversion_usd, inversion_mxn, usd_to_mxn,
    ppa_gen_anual, gen_base_label, hsp_anual, co2_saved_t, pr_pct,
    ppa_degradacion, vida_util,
    ppa_wacc, ppa_spread_hurdle, hurdle_label,
    ppa_inflacion_tarifa, ppa_inflacion_cfe,
    ppa_om_pct, ppa_seguros_pct,
    ppa_financiamiento, ppa_equity_pct, ppa_tasa_deuda, ppa_plazo_deuda,
    ppa_usar_valor_residual, valor_residual_nota,
    ppa_precio_manual, ppa_tarifa_cliente, descuento_vs_cfe,
    ppa_plazos, ppa_plazo_minimo, resultados,
    ahorro_total, ppa_cache_kwargs,
) -> bytes:
    import os as _os
    # Construir lista de datos por plazo
    plazos_data = []
    for pl in ppa_plazos:
        r = resultados[pl]
        plazos_data.append({
            "pl": pl,
            "pm": r.get("pm"),
            "ph": r.get("ph"),
            "ph_label": hurdle_label,
            "precio_manual": ppa_precio_manual,
            "vpn": r["vpn"],
            "tir": r["tir"],
            "pb": r["pb"],
            "pb_disc": r.get("pb_disc"),
            "vr": r.get("valor_residual", 0),
            "ing_total": r["ing_total"],
        })
    ro = resultados[ppa_plazo_minimo]
    escenarios = _esc_ppa(
        resultados, ppa_plazo_minimo, ppa_cache_kwargs,
        ppa_precio_manual, ppa_spread_hurdle, ppa_usar_valor_residual, vida_util
    )
    data = {
        "logo_b64":          _get_logo_b64(),
        "fecha":             fecha,
        "ubicacion":         proj_loc,
        "lat":               lat, "lon": lon,
        "kwp":               kwp, "n_panels": n_panels,
        "inversion_usd":     int(inversion_usd),
        "inversion_mxn":     int(inversion_mxn),
        "usd_to_mxn":        usd_to_mxn,
        "gen_anual":         ppa_gen_anual,
        "gen_base_label":    gen_base_label,
        "hsp":               hsp_anual,
        "co2_t":             co2_saved_t,
        "co2_factor":        CO2_FACTOR_KG_KWH,
        "pr_pct":            pr_pct,
        "degradacion":       ppa_degradacion,
        "vida_util":         vida_util,
        "wacc":              ppa_wacc,
        "spread":            ppa_spread_hurdle,
        "hurdle_label":      hurdle_label,
        "esc_ppa":           ppa_inflacion_tarifa,
        "inflacion_cfe":     ppa_inflacion_cfe,
        "om_pct":            ppa_om_pct,
        "seg_pct":           ppa_seguros_pct,
        "con_fin":           ppa_financiamiento,
        "equity_pct":        ppa_equity_pct,
        "tasa_deuda":        ppa_tasa_deuda,
        "plazo_deuda":       ppa_plazo_deuda,
        "usar_vr":           ppa_usar_valor_residual,
        "valor_residual_nota": valor_residual_nota,
        "precio_manual":     ppa_precio_manual,
        "tarifa_cliente":    ppa_tarifa_cliente,
        "descuento_vs_cfe":  descuento_vs_cfe,
        "ahorro_total":      ahorro_total,
        "plazos":            plazos_data,
        "plazo_obj":         {
            "pl":      ppa_plazo_minimo,
            "pm":      ro.get("pm"),
            "ph":      ro.get("ph"),
            "vpn":     ro["vpn"],
            "tir":     ro["tir"],
            "pb":      ro["pb"],
            "pb_disc": ro.get("pb_disc"),
            "vr":      ro.get("valor_residual", 0),
            "ing_total": ro["ing_total"],
        },
        "escenarios": escenarios,
    }
    _script = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "word_gen", "gen_ppa.js")
    return _run_word_script(_script, data)


def build_tor_text(proj_name, proj_date, proj_loc, proj_notes,
                   panel_wp, panel_eff, panel_largo_mm, panel_ancho_mm, panel_peso_kg,
                   panel_area, n_panels, kwp,
                   pr_pct, irr_vals, monthly_gen, annual_gen,
                   p50, p90, co2_saved,
                   inversion, ahorro1, payback,
                   gen_por_anio=None):
    lines = [
        "═══════════════════════════════════════════════════════════",
        f"  TÉRMINOS DE REFERENCIA — PRE-SIZING FOTOVOLTAICO",
        "═══════════════════════════════════════════════════════════",
        f"  Proyecto  : {proj_name}",
        f"  Fecha     : {proj_date}",
        f"  Ubicación : {proj_loc}",
        f"  Fuente irr: NASA POWER climatología {NASA_START}–{NASA_END}",
        "",
        "",
        "─── PARÁMETROS DEL PANEL (referencia) ──────────────────────",
        f"  Potencia pico (Pmax) : {panel_wp} Wp",
        f"  Eficiencia           : {panel_eff:.1f} %",
        f"  Dimensiones          : {panel_largo_mm} × {panel_ancho_mm} mm",
        f"  Área unitaria        : {panel_area:.4f} m²",
        f"  Peso                 : {panel_peso_kg} kg",
        f"  Carga estructural    : {n_panels * panel_peso_kg * 1.35:,.0f} kg  ({n_panels * panel_peso_kg * 1.35 * 9.8 / 1000:.2f} kN)  ({n_panels * panel_peso_kg * 1.35 * 9.8 / 1000 / max(n_panels * panel_area, 0.01):.3f} kN/m² sobre área instalada)  [factor ×1.35 montura+BOS]",
        "",
        "─── RESULTADOS DEL SIZING ──────────────────────────────────",
        f"  Paneles estimados    : {n_panels} unidades",
        f"  Capacidad pico       : {kwp:.2f} kWp",
        f"  PR asumido           : {pr_pct:.1f} %",
        f"  Generación P50 (irr. media)  : {p50:,.0f} kWh/año",
        f"  Generación P90       : {f'{p90:,.0f} kWh/año  (percentil 10 · {len(gen_por_anio)} años NASA POWER {NASA_START}–{NASA_END})' if p90 else 'No disponible — cargar datos NASA POWER'}",
        f"  CO₂ evitado/año      : {co2_saved/1000:,.2f} t  (factor {CO2_FACTOR_KG_KWH} kg CO₂e/kWh · SEN 2024 · SEMARNAT/CRE 28-Feb-2025)",
        "",
        "─── IRRADIANCIA MENSUAL (kWh/m²/día) ──────────────────────",
    ]
    for i, m in enumerate(MONTHS):
        lines.append(f"  {m:>3} : {irr_vals[i]:.2f}   →   Gen P50: {monthly_gen[i]:>7,.0f} kWh")
    lines += [
        f"  {'TOTAL':>3}        →   Gen P50: {annual_gen:>7,.0f} kWh/año",
        "",
    ]
    if proj_notes.strip():
        lines += ["─── NOTAS / ALCANCE ────────────────────────────────────────",
                  f"  {proj_notes}", ""]
    lines += [
        "─── ESPECIFICACIONES TÉCNICAS REQUERIDAS EN COTIZACIÓN ─────",
        "  MÓDULOS FOTOVOLTAICOS:",
        "  • Certificación IEC 61215 (calificación de diseño) · IEC 61730 (seguridad) · UL 61730 si aplica",
        "  • Clase de aplicación A · Tensión de sistema ≥ 1000 V DC",
        "  • Eficiencia mínima ≥ 21% (tecnología TOPCon/HJT actuales)",
        "  • Degradación: ≤ 2% año 1 · ≤ 0.4%/año años 2–25 (TOPCon) / ≤ 0.5%/año (PERC)",
        "  • Resistencia mecánica: carga frontal ≥ 5400 Pa (IEC 61215)",
        "  • Garantía de producto ≥ 12 años · Potencia lineal ≥ 25 años (P90 ≥ 80% Pmax)",
        "  • IP67 mínimo en caja de conexiones",
        "  • IEC 62716 resistencia a amoniaco — exigible en zonas agrícolas / ganaderas",
        "  • IEC 61701 categoría 6 resistencia a niebla salina — exigible en zonas costeras",
        "",
        "  INVERSORES:",
        "  • Certificación IEC 62109-1/-2 (seguridad) · Anti-islanding IEEE 1547 / NOM-001-SEDE",
        "  • THD de corriente ≤ 3% a potencia nominal (IEEE 519)",
        "  • IP66 mínimo · IP67 recomendado para intemperie",
        "  • Protección contra arco eléctrico DC (AFCI) — NEC 690.11",
        "  • Rapid Shutdown conforme NEC 690.12 (aplica en techos de edificio con acceso de emergencia)",
        "  • Eficiencia ≥ 98% Euro o CEC a potencia nominal",
        "  • Garantía mínima 5 años (extendible a 10–20 años)",
        "  • Sistemas >500 kWp: justificar topología string / centralizado / optimizadores",
        "    según uniformidad de superficie, orientaciones y nivel de sombreado",
        "",
        "  ESTRUCTURA Y MONTAJE:",
        "  • Aluminio 6005-T5 o acero galvanizado ASTM A653 (ZF275 mínimo)",
        "  • Diseño estructural conforme ASCE 7 / MDOC-CFE (viento, sismo, nieve si aplica)",
        "  • Resistencia a corrosión: niebla salina ≥ 1000 h (ISO 9227)",
        "  • Certificación de anclajes por ingeniero estructural acreditado (DRO o Perito)",
        "",
        "  SISTEMA ELÉCTRICO Y PROTECCIONES:",
        "  • Cableado DC: H1Z2Z2-K o equivalente (IEC 62930) · Tensión ≥ 1500 V",
        "  • Protecciones AC conformes NOM-001-SEDE / NEC 690",
        "  • Puesta a tierra conforme NOM-022-STPS y NEC 690.47",
        "  • Seccionadores y fusibles certificados UL 4703 / IEC 60269",
        "",
        "  MONITOREO:",
        "  • Datalogger con acceso remoto SCADA o plataforma cloud · SLA ≥ 99%",
        "  • Resolución de registro ≤ 15 min · Protocolo Modbus TCP o SunSpec",
        "  • Variables mínimas: potencia AC/DC, energía acumulada, V/I por MPPT,",
        "    temperatura de módulo, irradiancia (piranómetro clase 2), alarmas",
        "  • Exportación de datos en CSV o API REST",
        "",
        "  VERIFICACIONES E INSPECCIONES REQUERIDAS:",
        "  a) Pre-Puesta en Marcha (antes de energizar):",
        "    – Polaridad, continuidad y aislamiento DC ≥ 1 MΩ a 500 V (IEC 62446-1 · IEC 61557-2)",
        "    – Inspección visual de montaje, torque y sellado de conectores MC4",
        "    – Continuidad de puesta a tierra (< 1 Ω) y revisión de protecciones AC",
        "  b) Puesta en Marcha (commissioning):",
        "    – Curvas I-V por string vs STC ±3% (IEC 62446-1)",
        "    – Termografía IR de módulos y conexiones bajo carga (IEC TS 62446-3)",
        "    – Verificación anti-islanding y protecciones de reconexión (IEEE 1547)",
        "    – Prueba de potencia y PR inicial (tolerancia ±3%)",
        "    – Validación de monitoreo con registro mínimo 48 h",
        "  c) Inspecciones Periódicas:",
        "    – Limpieza semestral o según análisis de soiling",
        "    – Termografía IR anual de módulos, inversores y cableado (IEC TS 62446-3)",
        "    – Prueba de aislamiento DC anual (IEC 62446-1)",
        "    – Análisis de rendimiento vs P90 (PR objetivo ≥ 75%) (IEC 61724-1)",
        "    – Revisión anual de firmware de inversores y datalogger",
        "",
        "  ENTREGABLES OBLIGATORIOS DEL PROVEEDOR:",
        "  • Simulación PVSyst / Helioscope (P50 y P90) con:",
        "    – Análisis de sombras 3D (horizon profile + obstáculos cercanos)",
        "    – Estudio de soiling (pérdida por suciedad según zona climática)",
        "    – Desglose de pérdidas del sistema (PR explicado por componente)",
        "  • Planos eléctricos y estructurales firmados por DRO o Perito acreditado",
        "  • Memoria de cálculo estructural",
        "  • Protocolo de commissioning firmado (curvas I-V, termografía, aislamiento DC, PR)",
        "  • Dictamen UVIE (Unidad de Verificación de Instalaciones Eléctricas) conforme",
        "    NOM-001-SEDE — obligatorio para contrato CFE en mayoría de estados.",
        "    Nota: puede gestionarlo el EPC o el cliente; tiene costo independiente.",
        "  • Inspección de obra municipal / STPS si aplica (instalaciones industriales)",
        "  • Trámite de interconexión CFE (Pequeña Escala o Generación Distribuida)",
        "  • Permiso CRE si aplica (> 0.5 MW)",
        "  • Manual de O&M con plan de inspecciones periódicas",
        "  • Garantía de ejecución EPC ≥ 2 años post-puesta en marcha",
        "    (financiamientos bancarios exigen mínimo 3 años)",
        "  • Seguro de Responsabilidad Civil vigente durante la obra",
        "  • Performance bond / fianza de cumplimiento ≥ 10% del contrato",
        "    (obligatorio para proyectos > 100 kWp o con financiamiento bancario)",
        "",
        "─── CONSIDERACIONES GENERALES ──────────────────────────────",
        "  • Los valores son estimados de pre-sizing (±15%).",
        "  • El P90 se calcula como percentil 10 de la generación simulada",
        f"    con {len(gen_por_anio) if gen_por_anio else 'N/A'} años de irradiancia real NASA POWER ({NASA_START}–{NASA_END}).",
        "  • La ingeniería detallada y la simulación definitiva son responsabilidad del proveedor.",
        "  • Verificar disponibilidad y capacidad de red CFE en el punto de interconexión.",
        "═══════════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)


# ── Helpers PDF ───────────────────────────────────────────────────────────────
# Solo usamos rl_colors (reportlab.lib.colors)
_DARK   = rl_color.HexColor("#0f1117")
_PANEL  = rl_color.HexColor("#1a1d27")
_AMBER  = rl_color.HexColor("#f59e0b")
_TEAL   = rl_color.HexColor("#14b8a6")
_ROSE   = rl_color.HexColor("#f43f5e")
_GREY   = rl_color.HexColor("#6b7280")
_WHITE  = rl_color.HexColor("#f9fafb")
_LIGHT  = rl_color.HexColor("#d1d5db")
_BG2    = rl_color.HexColor("#13151f")


def _pdf_styles():
    base = getSampleStyleSheet()
    def S(name, **kw):
        return ParagraphStyle(name, **{"fontName": "Helvetica", "textColor": _LIGHT,
                                       "fontSize": 9, "leading": 13, **kw})
    return {
        "title":    S("title",   fontName="Helvetica-Bold", fontSize=18, textColor=_WHITE,
                      spaceAfter=2, alignment=TA_LEFT),
        "subtitle": S("sub",     fontSize=9,  textColor=_GREY,  spaceAfter=14),
        "section":  S("sec",     fontName="Helvetica-Bold", fontSize=7, textColor=_GREY,
                      spaceAfter=4, spaceBefore=14,
                      borderPadding=(0, 0, 4, 0)),
        "normal":   S("norm",    fontSize=9,  textColor=_LIGHT, leading=14),
        "kpi_val":  S("kpiv",    fontName="Helvetica-Bold", fontSize=15, textColor=_AMBER,
                      alignment=TA_CENTER, leading=18),
        "kpi_lbl":  S("kpil",    fontSize=7,  textColor=_GREY,  alignment=TA_CENTER),
        "kpi_sub":  S("kpis",    fontSize=7,  textColor=_GREY,  alignment=TA_CENTER),
        "footer":   S("foot",    fontSize=7,  textColor=_GREY,  alignment=TA_CENTER),
        "th":       S("th",      fontName="Helvetica-Bold", fontSize=8, textColor=_AMBER,
                      alignment=TA_CENTER),
        "td":       S("td",      fontSize=8,  textColor=_LIGHT, alignment=TA_CENTER),
        "td_l":     S("tdl",     fontSize=8,  textColor=_LIGHT, alignment=TA_LEFT),
        "note":     S("note",    fontSize=7.5, textColor=_GREY, leading=11),
    }


def _table_style(header_rows=1):
    return TableStyle([
        ("BACKGROUND",   (0, 0), (-1, header_rows - 1), _PANEL),
        ("BACKGROUND",   (0, header_rows), (-1, -1),    _BG2),
        ("ROWBACKGROUNDS",(0, header_rows), (-1, -1),   [_BG2, _PANEL]),
        ("TEXTCOLOR",    (0, 0), (-1, -1),              _LIGHT),
        ("FONTNAME",     (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1),              8),
        ("ALIGN",        (0, 0), (-1, -1),              "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1),              "MIDDLE"),
        ("ROWHEIGHT",    (0, 0), (-1, -1),              16),
        ("GRID",         (0, 0), (-1, -1),              0.4, rl_color.HexColor("#2a2d3a")),
        ("TOPPADDING",   (0, 0), (-1, -1),              4),
        ("BOTTOMPADDING",(0, 0), (-1, -1),              4),
        ("LEFTPADDING",  (0, 0), (-1, -1),              6),
        ("RIGHTPADDING", (0, 0), (-1, -1),              6),
    ])


def _kpi_table(items, styles, col_w=None):
    """items = [(label, value, sub), ...]  — genera fila de KPI cards."""
    n = len(items)
    W = letter[0] - 3.6 * cm
    cw = col_w or [W / n] * n
    rows = [
        [Paragraph(v,   styles["kpi_val"]) for _, v, _ in items],
        [Paragraph(l,   styles["kpi_lbl"]) for l, _, _ in items],
        [Paragraph(s,   styles["kpi_sub"]) for _, _, s in items],
    ]
    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _PANEL),
        ("GRID",          (0, 0), (-1, -1), 0.4, rl_color.HexColor("#2a2d3a")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    return Table(rows, colWidths=cw, style=ts)


def _hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=rl_color.HexColor("#2a2d3a"), spaceAfter=6, spaceBefore=2)


def _on_page(canvas, doc):
    """Footer en cada página."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_GREY)
    w, _ = letter
    canvas.drawCentredString(w / 2, 1.0 * cm,
        f"Sizing Tool · Documento generado automáticamente · Página {doc.page}")
    canvas.restoreState()


def build_pdf_sizing(
    proj_loc, lat, lon,
    panel_wp, panel_eff_declared, panel_largo_mm, panel_ancho_mm, panel_peso_kg, panel_area,
    n_panels, kwp, pr_pct, irr_vals, monthly_gen, annual_gen,
    p50, p90, co2_saved,
    inversion_usd, usd_to_mxn, ahorro1, payback,
    vpn, tir, lcoe, pb_disc,
    tarifa_efectiva, inflation, discount_rate, vida_util, om_pct,
    sizing_mode_label="—",
) -> bytes:
    """Genera el PDF de Pre-Sizing / TOR y devuelve bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.8*cm,
    )
    S = _pdf_styles()
    story = []

    # ── Encabezado ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Sizing Tool", S["title"]))
    story.append(Paragraph(
        f"Pre-Sizing Fotovoltaico &nbsp;·&nbsp; {proj_loc} &nbsp;·&nbsp; ({lat:.4f}, {lon:.4f})",
        S["subtitle"]))
    story.append(_hr())

    # ── KPIs principales ────────────────────────────────────────────────────────
    story.append(Paragraph("RESULTADOS DEL SISTEMA", S["section"]))
    story.append(_kpi_table([
        ("Capacidad pico",    f"{kwp:.2f} kWp",           f"{n_panels} paneles × {panel_wp} Wp"),
        ("Generación P50",    f"{p50/1000:.1f} MWh/año",  "Mediana histórica"),
        ("Generación P90",    f"{p90/1000:.1f} MWh/año" if p90 else "—", "Percentil 10"),
        ("CO&#8322; evitado", f"{co2_saved/1000:,.2f} t/a",f"Factor {CO2_FACTOR_KG_KWH} kg CO₂e/kWh · SEN 2024"),
    ], S))
    story.append(Spacer(1, 6))

    # ── Panel técnico ──────────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("PARÁMETROS DEL PANEL", S["section"]))
    panel_rows = [
        [Paragraph("Parámetro", S["th"]), Paragraph("Valor", S["th"])],
        [Paragraph("Potencia pico (Pmax)", S["td_l"]),  Paragraph(f"{panel_wp} Wp", S["td"])],
        [Paragraph("Eficiencia declarada", S["td_l"]),  Paragraph(f"{panel_eff_declared:.1f}%", S["td"])],
        [Paragraph("Dimensiones", S["td_l"]),           Paragraph(f"{panel_largo_mm} × {panel_ancho_mm} mm", S["td"])],
        [Paragraph("Area unitaria", S["td_l"]),         Paragraph(f"{panel_area:.4f} m²", S["td"])],
        [Paragraph("Peso unitario panel", S["td_l"]),   Paragraph(f"{panel_peso_kg} kg", S["td"])],
        [Paragraph("Carga total (x1.35)", S["td_l"]),
         Paragraph(f"{n_panels * panel_peso_kg * 1.35:,.0f} kg  |  "
                   f"{n_panels * panel_peso_kg * 1.35 * 9.8 / 1000:,.2f} kN", S["td"])],
        [Paragraph("Carga por m² instalado", S["td_l"]),
         Paragraph(f"{n_panels * panel_peso_kg * 1.35 * 9.8 / 1000 / max(n_panels * panel_area, 0.01):.3f} kN/m²  "
                   f"[factor x1.35 montura+BOS]", S["td"])],
        [Paragraph("Performance Ratio (PR)", S["td_l"]),Paragraph(f"{pr_pct:.1f}%", S["td"])],
        [Paragraph("Modo de dimensionamiento", S["td_l"]), Paragraph(sizing_mode_label, S["td"])],
    ]
    W = letter[0] - 3.6*cm
    story.append(Table(panel_rows, colWidths=[W*0.6, W*0.4], style=_table_style()))
    story.append(Spacer(1, 8))

    # ── Irradiancia + Generación mensual ───────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("IRRADIANCIA Y GENERACIÓN MENSUAL", S["section"]))
    hdr = [Paragraph(m, S["th"]) for m in MONTHS]
    irr_row = [Paragraph(f"{v:.2f}", S["td"]) for v in irr_vals]
    gen_row = [Paragraph(f"{v/1000:.1f}", S["td"]) for v in monthly_gen]
    lbl_col_w = 2.2*cm
    data_w = (W - lbl_col_w) / 12
    irr_table = Table(
        [[Paragraph("", S["th"])] + hdr,
         [Paragraph("kWh/m²/día", S["td_l"])] + irr_row,
         [Paragraph("Gen. MWh/mes", S["td_l"])] + gen_row],
        colWidths=[lbl_col_w] + [data_w]*12,
        style=_table_style(),
    )
    story.append(irr_table)
    story.append(Paragraph(
        f"Total generación anual P50: {annual_gen:,.0f} kWh/año  ·  Fuente: NASA POWER {NASA_START}–{NASA_END}",
        S["note"]))
    story.append(Spacer(1, 8))

    # ── Parámetros financieros ─────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("PARÁMETROS FINANCIEROS", S["section"]))
    fin_rows = [
        [Paragraph("Parámetro", S["th"]), Paragraph("Valor", S["th"]),
         Paragraph("Parámetro", S["th"]), Paragraph("Valor", S["th"])],
        [Paragraph("Tarifa efectiva", S["td_l"]),  Paragraph(f"${tarifa_efectiva:.3f}/kWh", S["td"]),
         Paragraph("Inflación tarifa", S["td_l"]), Paragraph(f"{inflation:.1f}%/año", S["td"])],
        [Paragraph("Tasa de descuento", S["td_l"]),Paragraph(f"{discount_rate:.1f}%", S["td"]),
         Paragraph("O&M anual", S["td_l"]),        Paragraph(f"{om_pct:.1f}% inv.", S["td"])],
        [Paragraph("Vida útil", S["td_l"]),        Paragraph(f"{vida_util} años", S["td"]),
         Paragraph("TIR", S["td_l"]),              Paragraph(f"{tir:.1f}%" if tir else "—", S["td"])],
    ]
    story.append(Table(fin_rows, colWidths=[W*0.3, W*0.2, W*0.3, W*0.2], style=_table_style()))
    story.append(Spacer(1, 8))

    # ── Especificaciones técnicas y certificaciones ────────────────────────────
    story.append(_hr())
    story.append(Paragraph("ESPECIFICACIONES TÉCNICAS Y CERTIFICACIONES REQUERIDAS", S["section"]))

    specs = [
        ("MÓDULOS FV",         "IEC 61215 (calificación de diseño) · IEC 61730 (seguridad) · UL 61730 si aplica"),
        ("Efic. / Degradación","Eficiencia ≥ 21% · Degradación: ≤ 2% año 1; ≤ 0.4%/año (TOPCon) / ≤ 0.5%/año (PERC)"),
        ("Clase / IP",         "Clase A · ≥ 1000 V DC · IP67 en caja de conexiones"),
        ("Carga mecánica",     "Frontal ≥ 5400 Pa (IEC 61215)"),
        ("Garantías módulo",   "Producto ≥ 12 años · Potencia lineal ≥ 25 años (P90 ≥ 80% Pmax)"),
        ("Amoniaco / Salina",  "IEC 62716 (zonas agrícolas) · IEC 61701 Cat.6 (zonas costeras) — condicional"),
        ("INVERSORES",         "IEC 62109-1/-2 · Anti-islanding IEEE 1547 / NOM-001-SEDE · THD ≤ 3% (IEEE 519)"),
        ("IP / Protecciones",  "IP66 mínimo · AFCI NEC 690.11 · Rapid Shutdown NEC 690.12 (techos)"),
        ("Eficiencia inversor","≥ 98% Euro o CEC a potencia nominal"),
        ("Garantía inversor",  "Mínimo 5 años · extendible a 10–20 años"),
        (">500 kWp topología", "Justificar string / centralizado / optimizadores según sombra y orientación"),
        ("ESTRUCTURA",         "Aluminio 6005-T5 o acero ASTM A653 ≥ ZF275 · Niebla salina ≥ 1000 h (ISO 9227)"),
        ("Diseño estructural", "ASCE 7 / MDOC-CFE (viento, sismo) · Firmado por DRO o Perito acreditado"),
        ("CABLEADO DC",        "H1Z2Z2-K o equiv. IEC 62930 · Tensión ≥ 1500 V"),
        ("PROTECCIONES AC",    "NOM-001-SEDE / NEC 690 · Puesta a tierra NOM-022-STPS y NEC 690.47"),
        ("MONITOREO",          "Datalogger SCADA/cloud · Resolución ≤ 15 min · Modbus TCP o SunSpec · SLA ≥ 99%"),
        ("Variables monitor.", "Potencia AC/DC, energía acumulada, V/I por MPPT, temp. módulo, irradiancia (piranómetro clase 2), alarmas"),
    ]
    from reportlab.platypus import Table as RLTable
    W_page = letter[0] - 3.6*cm
    spec_data = [[Paragraph("Ítem", S["th"]), Paragraph("Requisito", S["th"])]]
    for item, req in specs:
        spec_data.append([Paragraph(item, S["td_l"]), Paragraph(req, S["td_l"])])
    spec_tbl = RLTable(spec_data, colWidths=[W_page*0.28, W_page*0.72])
    spec_tbl.setStyle(_table_style(header_rows=1))
    story.append(spec_tbl)
    story.append(Spacer(1, 8))

    # ── Verificaciones e inspecciones ──────────────────────────────────────────
    story.append(Paragraph("VERIFICACIONES E INSPECCIONES REQUERIDAS", S["section"]))
    insp_data = [
        [Paragraph("Fase", S["th"]), Paragraph("Verificación / Inspección", S["th"]), Paragraph("Norma de referencia", S["th"])],
        [Paragraph("Pre-puesta en marcha", S["td_l"]),
         Paragraph("Polaridad, continuidad y aislamiento DC ≥ 1 MΩ a 500 V", S["td_l"]),
         Paragraph("IEC 62446-1 · IEC 61557-2", S["td"])],
        [Paragraph("Pre-puesta en marcha", S["td_l"]),
         Paragraph("Inspección visual montaje, torque conectores MC4, sellado", S["td_l"]),
         Paragraph("IEC 62446-1", S["td"])],
        [Paragraph("Pre-puesta en marcha", S["td_l"]),
         Paragraph("Continuidad puesta a tierra (< 1 Ω) y protecciones AC", S["td_l"]),
         Paragraph("NOM-001-SEDE · NEC 690.47", S["td"])],
        [Paragraph("Commissioning", S["td_l"]),
         Paragraph("Curvas I-V por string vs STC (tolerancia ± 3%)", S["td_l"]),
         Paragraph("IEC 62446-1", S["td"])],
        [Paragraph("Commissioning", S["td_l"]),
         Paragraph("Termografía IR de módulos y conexiones bajo carga", S["td_l"]),
         Paragraph("IEC TS 62446-3", S["td"])],
        [Paragraph("Commissioning", S["td_l"]),
         Paragraph("Anti-islanding y protecciones de reconexión", S["td_l"]),
         Paragraph("IEEE 1547 · NOM-001-SEDE", S["td"])],
        [Paragraph("Commissioning", S["td_l"]),
         Paragraph("Validación monitoreo con registro mínimo 48 h", S["td_l"]),
         Paragraph("IEC 62446-2", S["td"])],
        [Paragraph("Anual", S["td_l"]),
         Paragraph("Termografía IR módulos, inversores y cableado", S["td_l"]),
         Paragraph("IEC TS 62446-3", S["td"])],
        [Paragraph("Anual", S["td_l"]),
         Paragraph("Prueba de aislamiento DC y revisión de estructura/anclajes", S["td_l"]),
         Paragraph("IEC 62446-1", S["td"])],
        [Paragraph("Anual", S["td_l"]),
         Paragraph("Análisis de rendimiento vs P90 (PR objetivo ≥ 75%)", S["td_l"]),
         Paragraph("IEC 61724-1", S["td"])],
        [Paragraph("Semestral", S["td_l"]),
         Paragraph("Limpieza de módulos y revisión de firmware inversores", S["td_l"]),
         Paragraph("Manual fabricante", S["td"])],
    ]
    W_page2 = letter[0] - 3.6*cm
    insp_tbl = RLTable(insp_data, colWidths=[W_page2*0.22, W_page2*0.52, W_page2*0.26])
    insp_tbl.setStyle(_table_style(header_rows=1))
    story.append(insp_tbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph("ENTREGABLES OBLIGATORIOS DEL PROVEEDOR", S["section"]))
    entregables = [
        "Simulación PVSyst / Helioscope (P50 y P90) con sombras 3D, estudio de soiling y desglose de pérdidas",
        "Planos eléctricos y estructurales firmados por DRO o Perito acreditado",
        "Memoria de cálculo estructural del sistema de montaje",
        "Dictamen UVIE (NOM-001-SEDE) — requerido para contrato CFE en mayoría de estados",
        "Inspección municipal / STPS si aplica (uso industrial o comercial mayor)",
        "Trámite de interconexión CFE (Pequeña Escala o GD) · Permiso CRE si > 0.5 MW",
        "Garantía de ejecución EPC ≥ 2 años post-puesta en marcha (financiamientos exigen 3 años)",
        "Seguro de Responsabilidad Civil vigente durante la obra",
        "Performance bond / fianza de cumplimiento ≥ 10% del contrato (obligatorio > 100 kWp)",
        "Manual de O&M con plan de inspecciones periódicas",
        "Protocolo de commissioning firmado: curvas I-V, termografía IR, aislamiento DC, PR",
    ]
    for e in entregables:
        story.append(Paragraph(f"• {e}", S["note"]))
        story.append(Spacer(1, 2))
    story.append(Spacer(1, 8))

    # ── Consideraciones ────────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("CONSIDERACIONES GENERALES", S["section"]))
    notas = [
        "Los valores son estimados de pre-sizing (±15%). El proveedor deberá realizar diseño detallado con software especializado (PVSyst, Helioscope, etc.).",
        f"El P90 representa el percentil 10 de la distribución de generaciones anuales simuladas con {NASA_END - NASA_START + 1} años de irradiancia real NASA POWER ({NASA_START}–{NASA_END}).",
        "Verificar disponibilidad de red y trámites CFE / CRE antes de proceder.",
        f"Factor de emisión CO₂ de referencia: {CO2_FACTOR_KG_KWH} kg CO₂e/kWh — Factor de Emisión del SEN 2024 (SEMARNAT/CRE, aviso 28-Feb-2025). Actualizar con el aviso anual más reciente.",
    ]
    for n in notas:
        story.append(Paragraph(f"• {n}", S["note"]))
        story.append(Spacer(1, 3))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def build_pdf_ppa(
    proj_loc, ppa_kwp, ppa_gen_anual, ppa_inversion_usd, usd_to_mxn,
    ppa_wacc, ppa_inflacion_tarifa, ppa_degradacion, ppa_om_pct,
    ppa_seguros_pct, ppa_tarifa_cliente, ppa_inflacion_cfe,
    ppa_precio_manual, ppa_plazo_minimo, ppa_plazos,
    resultados, descuento_vs_cfe,
    ro,                    # resultados[ppa_plazo_minimo]
    ahorro_total, ahorro_y, cfe_y, pago_ppa, pago_cfe,
    pm_obj, viable,
) -> bytes:
    """Genera el PDF del análisis PPA y devuelve bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.8*cm,
    )
    S = _pdf_styles()
    story = []
    W = letter[0] - 3.6*cm

    # ── Encabezado ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Sizing Tool", S["title"]))
    story.append(Paragraph(
        f"Análisis PPA · Venta al Cliente &nbsp;·&nbsp; {proj_loc} &nbsp;·&nbsp; "
        f"Plazo objetivo: {ppa_plazo_minimo} años",
        S["subtitle"]))
    story.append(_hr())

    # ── KPIs hero ──────────────────────────────────────────────────────────────
    story.append(Paragraph("RESUMEN EJECUTIVO", S["section"]))
    pm_str  = f"${pm_obj:.4f}/kWh" if pm_obj else "No viable"
    viable_color = "#4ade80" if viable else "#f43f5e"
    story.append(_kpi_table([
        ("Precio PPA año 1",     f"${ppa_precio_manual:.4f}/kWh", "Evaluado"),
        ("Precio minimo viable", pm_str,                           f"VPN=0 a {ppa_plazo_minimo}a"),
        ("Descuento vs CFE hoy", f"{descuento_vs_cfe:+.1f}%",     "precio PPA vs tarifa"),
        ("Ahorro total cliente", f"${ahorro_total:,.0f}",          f"MXN en {ppa_plazo_minimo} años"),
    ], S))
    story.append(Spacer(1, 6))
    story.append(_kpi_table([
        ("VPN a WACC",         f"${ro['vpn_wacc']:,.0f} MXN",     f"WACC {ppa_wacc:.1f}%"),
        ("VPN a hurdle rate",   f"${ro['vpn_hurdle']:,.0f} MXN",   f"WACC+{ppa_spread_hurdle:.0f}% = {ppa_wacc+ppa_spread_hurdle:.1f}%"),
        ("TIR equity",         f"{ro['tir']:.1f}%" if ro["tir"] else "—", "sobre capital propio"),
        ("Payback simple",     f"{ro['pb']} años" if ro["pb"] else f">{ppa_plazo_minimo}a", "nominal s/descontar"),
        ("Payback descontado",  f"{ro['pb_disc']} años" if ro.get("pb_disc") else f">{ppa_plazo_minimo}a", f"Ke {ro.get('ke_pct', ppa_wacc):.1f}%"),
        ("Valor residual",     f"${ro.get('valor_residual',0):,.0f} MXN",
                               f"{max(0,25-ppa_plazo_minimo)}a restantes"),
    ], S))
    story.append(Spacer(1, 8))

    # ── Comparativo de plazos ─────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("COMPARATIVO DE PLAZOS", S["section"]))
    plazos_hdr = [Paragraph("Métrica", S["th"])] + [Paragraph(f"{pl}a", S["th"]) for pl in ppa_plazos]
    metricas = [
        (f"VPN WACC {ppa_wacc:.1f}%",   lambda r: f"${r['vpn_wacc']:,.0f}"),
        (f"VPN hurdle {ppa_wacc+ppa_spread_hurdle:.1f}%", lambda r: f"${r['vpn_hurdle']:,.0f}"),
        ("TIR equity",      lambda r: f"{r['tir']:.1f}%" if r["tir"] else "N/A"),
        ("Payback simple",  lambda r: f"{r['pb']}" if r["pb"] else f">{ppa_plazo_minimo}a"),
        ("Payback desc.",    lambda r: f"{r['pb_disc']}" if r.get("pb_disc") else f">{ppa_plazo_minimo}a"),
        ("Ingreso total",   lambda r: f"${r['ing_total']:,.0f}"),
        ("Precio minimo",   lambda r: f"${r['pm']:.4f}" if r.get("pm") else "N/V"),
        ("Valor residual",  lambda r: f"${r.get('valor_residual',0):,.0f}"),
    ]
    plazos_rows = [plazos_hdr]
    for label, fn in metricas:
        row = [Paragraph(label, S["td_l"])] + [Paragraph(fn(resultados[pl]), S["td"]) for pl in ppa_plazos]
        plazos_rows.append(row)
    col_w_pl = [W * 0.28] + [W * 0.72 / len(ppa_plazos)] * len(ppa_plazos)
    story.append(Table(plazos_rows, colWidths=col_w_pl, style=_table_style()))
    story.append(Spacer(1, 8))

    # ── Parámetros del modelo ──────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("PARÁMETROS DEL MODELO", S["section"]))
    param_rows = [
        [Paragraph("Parámetro", S["th"]), Paragraph("Valor", S["th"]),
         Paragraph("Parámetro", S["th"]), Paragraph("Valor", S["th"])],
        [Paragraph("Capacidad sistema", S["td_l"]),    Paragraph(f"{ppa_kwp:.1f} kWp", S["td"]),
         Paragraph("Generación año 1", S["td_l"]),     Paragraph(f"{ppa_gen_anual:,.0f} kWh", S["td"])],
        [Paragraph("Inversión total", S["td_l"]),      Paragraph(f"${ppa_inversion_usd:,.0f} USD", S["td"]),
         Paragraph("Tipo de cambio", S["td_l"]),       Paragraph(f"${usd_to_mxn:.2f} MXN/USD", S["td"])],
        [Paragraph("WACC", S["td_l"]),                 Paragraph(f"{ppa_wacc:.1f}%", S["td"]),
         Paragraph("Escalador PPA", S["td_l"]),        Paragraph(f"{ppa_inflacion_tarifa:.1f}%/año", S["td"])],
        [Paragraph("Degradacion paneles", S["td_l"]), Paragraph(f"{ppa_degradacion:.2f}%/año", S["td"]),
         Paragraph("O&M anual", S["td_l"]),            Paragraph(f"{ppa_om_pct:.1f}% inv.", S["td"])],
        [Paragraph("Seguros", S["td_l"]),              Paragraph(f"{ppa_seguros_pct:.2f}% inv.", S["td"]),
         Paragraph("Tarifa CFE cliente", S["td_l"]),  Paragraph(f"${ppa_tarifa_cliente:.4f}/kWh", S["td"])],
        [Paragraph("Inflacion CFE", S["td_l"]),        Paragraph(f"{ppa_inflacion_cfe:.1f}%/año", S["td"]),
         Paragraph("Inflacion O&M", S["td_l"]),        Paragraph("—", S["td"])],
    ]
    story.append(Table(param_rows, colWidths=[W*0.3, W*0.2, W*0.3, W*0.2], style=_table_style()))
    story.append(Spacer(1, 8))

    # ── Tabla flujos anuales (plazo objetivo) ──────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph(
        f"FLUJOS ANUALES — PLAZO {ppa_plazo_minimo} AÑOS", S["section"]))
    flujo_hdr = [
        Paragraph("Año", S["th"]),
        Paragraph("Gen. (MWh)", S["th"]),
        Paragraph("Precio PPA", S["th"]),
        Paragraph("Ingreso PPA", S["th"]),
        Paragraph("CFE equiv.", S["th"]),
        Paragraph("Ahorro cliente", S["th"]),
        Paragraph("Flujo neto", S["th"]),
    ]
    flujo_rows = [flujo_hdr]
    gen_cl  = ro["gen_y"]
    prec_cl = ro["prec_y"]
    for i in range(ppa_plazo_minimo):
        fn_v = ro["fn_y"][i]
        fn_color = "#4ade80" if fn_v >= 0 else "#f87171"
        flujo_rows.append([
            Paragraph(str(ro["years"][i]), S["td"]),
            Paragraph(f"{gen_cl[i]/1000:.2f}", S["td"]),
            Paragraph(f"${prec_cl[i]:.4f}", S["td"]),
            Paragraph(f"${pago_ppa[i]:,.0f}", S["td"]),
            Paragraph(f"${cfe_y[i]:.4f}", S["td"]),
            Paragraph(f"${ahorro_y[i]:,.0f}", S["td"]),
            Paragraph(f'<font color="{fn_color}">${fn_v:,.0f}</font>', S["td"]),
        ])
    col_w_fl = [W*0.07, W*0.12, W*0.12, W*0.16, W*0.12, W*0.20, W*0.21]
    story.append(Table(flujo_rows, colWidths=col_w_fl, style=_table_style()))
    story.append(Spacer(1, 8))

    # ── Nota final ─────────────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("NOTAS Y DESCARGOS", S["section"]))
    notas_ppa = [
        "Este documento es una estimación financiera de pre-venta. Los valores reales dependerán del desempeño del sistema, condiciones climáticas y acuerdos contractuales definitivos.",
        "El valor residual se calcula usando anuidad con crecimiento compuesto (fórmula de Gordon) incorporando la degradación anual del panel y el escalador PPA.",
        "El precio mínimo viable (VPN=0) se calcula por bisección con 80 iteraciones sobre la función de VPN.",
        "Se recomienda contratar una auditoría energética y simulación detallada (PVSyst/Helioscope) antes de firmar el contrato PPA.",
    ]
    for n in notas_ppa:
        story.append(Paragraph(f"• {n}", S["note"]))
        story.append(Spacer(1, 3))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ── Session state initialization ──────────────────────────────────────────────
if "nasa_irradiance" not in st.session_state:
    st.session_state.nasa_irradiance = DEFAULT_IRR.copy()

if "nasa_irr_por_anio" not in st.session_state:
    st.session_state.nasa_irr_por_anio = {}   # vacío → P90 no disponible sin NASA

if "nasa_source_label" not in st.session_state:
    st.session_state.nasa_source_label = None



## ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    import os as _os, base64 as _b64
    _logo_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.png")
    if _os.path.exists(_logo_path):
        with open(_logo_path, "rb") as _lf:
            _logo_b64 = _b64.b64encode(_lf.read()).decode()
        st.markdown(f'<img src="data:image/png;base64,{_logo_b64}" style="width:100%;max-width:275px;margin-bottom:8px;">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:20px;font-weight:700;color:#f59e0b;padding:8px 0 12px;">⚡ Sizing Tool</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### PARÁMETROS CLAVE")
    st.markdown("---")

    # ── Ubicación con Mapa (solo coordenadas en sidebar) ─────────────────────
    st.markdown("#### Ubicación")
    st.markdown(f"""
    <style>
        div[key="lat_input"] input,
        div[key="lon_input"] input {{
            background-color: #000000 !important;
            color: #ffffff !important;
        }}
    </style>
""", unsafe_allow_html=True)
    col_lat, col_lon = st.columns(2)
    lat = col_lat.number_input("Latitud", -90.0, 90.0, 19.4326, format="%.8f", key="lat_input")
    lon = col_lon.number_input("Longitud", -180.0, 180.0, -99.1332, format="%.8f", key="lon_input")

    st.caption(f"📍 Coordenadas actuales: **{lat:.4f}**, **{lon:.4f}**")

    # Botón único para NASA POWER
    if st.button("🌍 Obtener irradiancia NASA POWER (2005–2024)", 
                 type="primary", 
                 use_container_width=True, 
                 key="nasa_button"):
        with st.spinner("Consultando datos de NASA POWER..."):
            try:
                irr_media, irr_por_anio = get_nasa_power_irradiance(lat, lon)
                st.session_state.nasa_irradiance   = irr_media
                st.session_state.nasa_irr_por_anio = irr_por_anio
                st.session_state.nasa_source_label = f"({lat:.4f}, {lon:.4f})"
                n_anios = len(irr_por_anio)
                st.success(f"✅ Datos de NASA POWER cargados — {n_anios} años históricos ({NASA_START}–{NASA_END})")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.nasa_irradiance   = DEFAULT_IRR.copy()
                st.session_state.nasa_irr_por_anio = {}
                st.session_state.nasa_source_label = None

    lbl = st.session_state.get("nasa_source_label", None)
    st.caption(f"Fuente: NASA POWER (2005–2024) · {lbl}" if lbl else "Valores por defecto: CDMX")

    st.markdown("---")

    # ── Ficha técnica del panel ───────────────────────────────────────────────
    st.markdown("#### 📋 Panel (datos básicos)")
    panel_wp           = st.number_input("Potencia pico Pmax (Wp)", 100, 900, 650, 5)
    panel_eff_declared = st.number_input("Eficiencia (%)", 10.0, 26.0, 24.1, 0.01)
    panel_largo_mm     = st.number_input("Largo (mm)", 1000, 2500, 2382, 1)
    panel_ancho_mm     = st.number_input("Ancho (mm)", 700, 1300, 1134, 1)
    panel_peso_kg      = st.number_input("Peso (kg)", 5.0, 40.0, 32.7, .1)

    st.markdown("---")

    # ── PR del Sistema ───────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Performance Ratio (PR) del sistema")

    st.markdown("""
    <div style="font-size:13px; color:#9ca3af; margin-bottom:10px;">
        PR global del sistema (incluye inversor, cableado, suciedad, mismatch, temperatura, etc.)
    </div>
    """, unsafe_allow_html=True)

    effective_pr = st.slider(
        "Performance Ratio (PR)",
        min_value=0.60,
        max_value=0.95,
        value=0.7,
        step=0.01,
        format="%.2f"
    )

    pr_pct = effective_pr * 100

    if pr_pct >= 82:
        badge_class = "pr-green"
        badge_text = "● Excelente"
    elif pr_pct >= 75:
        badge_class = "pr-yellow"
        badge_text = "● Bueno"
    else:
        badge_class = "pr-red"
        badge_text = "● Bajo — revisar diseño"

    st.markdown(f"""
    <div class="pr-badge {badge_class}" style="margin:10px 0 8px 0;">
        {badge_text} — PR {pr_pct:.1f}%
    </div>
    """, unsafe_allow_html=True)

    st.caption("Valor típico residencial en México: 0.75 – 0.82")

    # Degradación anual
    st.markdown("---")
    panel_degradation = st.slider("Degradación anual (%/año)", 0.3, 1.0, 0.5, 0.1, key="degradacion_anual")

    st.markdown("---")
    st.markdown("#### 💰 Referencia financiera")
    tarifa    = st.slider("Tarifa ref. área (MXN/kWh)", 1.0, 8.0, 2.80, 0.10, key="tarifa",
                          help="Usada en modo 'Por área'. En modo recibo CFE se usa la tarifa del recibo.")
    inflation = st.slider("Inflación tarifa anual (%)", 0.0, 8.0, 3.0, 0.5, key="inflation")
    discount_rate = st.slider("Tasa de descuento (%)", 0.0, 30.0, 15.0, 0.5, key="discount_rate",
                              help="Tasa usada para evaluación")
    usd_to_mxn    = st.slider("Tipo de Cambio (MXN por USD)", 16.0, 22.0, 17.50, 0.1, key="usd_to_mxn",
                              help="Tipo de cambio para evaluación financiera")
    vida_util = st.slider("Vida útil (años)", 10, 30, 25, 1, key="vida_util")
    costo_kwp = st.slider("Costo ref. instalación (USD/kWp)", 500, 2000, 1000, 50, key="costo_kwp")
    om_pct_sidebar = st.slider("O&M anual (% inversión MXN)", 0.5, 3.0, 1.0, 0.1, key="om_pct_sidebar",
                               help="Operación y mantenimiento anual como % de la inversión en MXN")

    st.markdown("---")
    st.markdown(f"<div style='font-size:11px;color:#4b5563;'>v3.0 · NASA POWER {NASA_START}–{NASA_END} · México</div>",
                unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# Derived panel values (se calculan después del sidebar)
# ═════════════════════════════════════════════════════════════════════════════
panel_largo_m  = panel_largo_mm / 1000
panel_ancho_m  = panel_ancho_mm / 1000
panel_area     = panel_largo_m * panel_ancho_m
panel_eff_calc = (panel_wp / (panel_area * 1000)) * 100
eff_delta      = panel_eff_calc - panel_eff_declared
eff_ok         = abs(eff_delta) <= 0.5
eff_color      = "#14b8a6" if eff_ok else "#f43f5e"
eff_note       = "✓" if eff_ok else f"{'↑' if eff_delta>0 else '↓'}{abs(eff_delta):.1f}% vs declarada"


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="app-title">Sizing Tool</div>', unsafe_allow_html=True)


tab1, tab3, tab_sol = st.tabs(["  ☀️ Turnkey Solar", "  📄 PPA Solar", "  🌞 Recurso Solar 8760h"])
active_irr         = st.session_state.nasa_irradiance
active_irr_por_anio = st.session_state.nasa_irr_por_anio


def irr_source_banner():
    lbl = st.session_state.nasa_source_label
    if lbl:
        st.markdown(
            f'<div class="nasa-box">🌍 NASA POWER · Climatología {NASA_START}–{NASA_END} · {lbl} · Editable</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="info-box">Valores por defecto CDMX. Busca coordenada en el sidebar para modificar el sitio.</div>',
            unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS VISUALIZACIÓN 8760h — usados en Tab 1 (modo CSV) y Tab 6
# ═════════════════════════════════════════════════════════════════════════════

def build_heatmap_fig(values_8760: list, title: str, unit: str, colorscale: str = "YlOrRd") -> go.Figure:
    """Construye heatmap 24h × 365d desde una serie de 8760 valores."""
    n = min(len(values_8760), 8760)
    padded = list(values_8760[:n]) + [0.0] * (8760 - n)
    mat = np.array(padded[:8760]).reshape(365, 24)
    lay = copy.deepcopy(PLOT_LAYOUT)
    fig = go.Figure(go.Heatmap(
        z=mat,
        x=[f"{h:02d}h" for h in range(24)],
        y=[f"Día {d+1}" for d in range(365)],
        colorscale=colorscale,
        colorbar=dict(title=unit, tickfont=dict(size=9)),
        hovertemplate="Día %{y} · %{x}<br>" + f"{title}: %{{z:.1f}} {unit}<extra></extra>",
    ))
    lay.update({"height": 340, "title": dict(text=title, font=dict(size=12)),
                "xaxis": dict(title="Hora del día", tickfont=dict(size=8)),
                "yaxis": dict(title="", showticklabels=False),
                "margin": dict(l=10, r=60, t=40, b=40)})
    fig.update_layout(**lay)
    return fig


def duration_curve_fig(values_8760: list, label: str, color: str, unit: str = "kW") -> go.Figure:
    """Curva de duración (load duration curve) de una serie 8760h."""
    sorted_vals = sorted(values_8760, reverse=True)
    hours = list(range(1, len(sorted_vals) + 1))
    lay = copy.deepcopy(PLOT_LAYOUT)
    fig = go.Figure(go.Scatter(
        x=hours, y=sorted_vals, mode="lines", name=label,
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.10)",
    ))
    lay.update({"height": 280,
                "xaxis": dict(title="Horas/año (mayor a menor)", gridcolor="#1e2230"),
                "yaxis": dict(title=unit, gridcolor="#1e2230"),
                "margin": dict(l=10, r=10, t=30, b=40)})
    fig.update_layout(**lay)
    return fig


# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES — 8760h (TMY, PV, financiero)
# Definidas aquí para estar disponibles en todos los tabs.
# ═════════════════════════════════════════════════════════════════════════════
def get_nasa_hourly(lat: float, lon: float, year: int = 2023) -> tuple[pd.DataFrame | None, str]:
    """
    Descarga datos horarios NASA POWER para un año dado.
    Parámetros: ALLSKY_SFC_SW_DWN (W/m²), T2M (°C), WS2M (m/s).
    Devuelve (DataFrame 8760 filas, mensaje_error).
    API hourly disponible desde 2001.
    """
    params = "ALLSKY_SFC_SW_DWN,T2M,WS2M"
    url = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        f"?parameters={params}&community=RE"
        f"&longitude={lon}&latitude={lat}&format=JSON"
        f"&start={year}0101&end={year}1231"
    )
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        raw = (data.get("properties", {})
                   .get("parameter", {}))
        if not raw:
            return None, "NASA POWER no devolvió datos horarios."

        irr_raw  = raw.get("ALLSKY_SFC_SW_DWN", {})
        temp_raw = raw.get("T2M", {})
        wind_raw = raw.get("WS2M", {})

        rows = []
        for key in sorted(irr_raw.keys()):
            if len(key) != 10:   # YYYYMMDDHH
                continue
            try:
                dt_str = f"{key[:4]}-{key[4:6]}-{key[6:8]} {key[8:10]}:00"
                irr  = float(irr_raw.get(key, 0))
                temp = float(temp_raw.get(key, 20))
                wind = float(wind_raw.get(key, 0))
                # NASA usa -999 para datos inválidos
                if irr  < 0: irr  = 0.0
                if temp < -50: temp = 20.0
                if wind < 0: wind = 0.0
                rows.append({"datetime": dt_str,
                             "irradiance_Wm2": irr,
                             "temp_C": temp,
                             "wind_ms": wind})
            except (ValueError, TypeError):
                continue

        if not rows:
            return None, "No se pudieron parsear los datos horarios."

        df = pd.DataFrame(rows)
        df["datetime"] = pd.to_datetime(df["datetime"])

        # Asegurar exactamente 8760 horas (año no bisiesto)
        df = df.head(8760).reset_index(drop=True)
        if len(df) < 8000:
            return None, f"Solo se obtuvieron {len(df)} horas. Verifica coordenadas."

        return df, ""

    except requests.exceptions.Timeout:
        return None, "⏱️ Timeout: NASA POWER tardó demasiado. Intenta de nuevo."
    except requests.exceptions.ConnectionError:
        return None, "🌐 Sin conexión. Verifica tu internet."
    except Exception as e:
        return None, f"❌ Error NASA POWER: {str(e)[:120]}"



def get_nasa_monthly_temp(lat: float, lon: float) -> tuple[list, str]:
    """
    Descarga temperatura media mensual (T2M) de NASA POWER 2005-2024.
    Devuelve (lista 12 valores °C, mensaje).
    Reutiliza el mismo endpoint mensual que get_nasa_power_irradiance().
    """
    url = (
        "https://power.larc.nasa.gov/api/temporal/monthly/point"
        "?parameters=T2M&community=RE"
        f"&longitude={lon}&latitude={lat}&format=JSON"
        f"&start={NASA_START}&end={NASA_END}"
    )
    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        raw = (r.json().get("properties", {})
                       .get("parameter", {})
                       .get("T2M", {}))
        if not raw:
            return [20.0]*12, "Sin datos de temperatura — usando 20°C fijo."

        monthly_sum   = [0.0]*12
        monthly_count = [0]*12
        for key, val in raw.items():
            if len(key) != 6: continue
            try:
                m_idx = int(key[4:6]) - 1
                if 0 <= m_idx <= 11 and val is not None and val > -100:
                    monthly_sum[m_idx]   += float(val)
                    monthly_count[m_idx] += 1
            except (ValueError, TypeError):
                continue

        temp_media = [
            round(monthly_sum[i]/monthly_count[i], 2) if monthly_count[i] > 0 else 20.0
            for i in range(12)
        ]
        return temp_media, f"Temperatura media mensual 2005-2024 · Media anual: {sum(temp_media)/12:.1f}°C"
    except Exception as e:
        return [20.0]*12, f"Error temperatura NASA: {str(e)[:80]} — usando 20°C."



def build_tmy_8760(
    lat: float,
    lon: float,
    irr_media_mensual: tuple,   # 12 valores climatológicos 2005-2024 (kWh/m²/día)
    temp_media_mensual: tuple = None,   # 12 valores °C promedio mensual (opcional)
    year_ref: int = 2023,       # año para obtener perfil intradiario de forma
) -> tuple[pd.DataFrame | None, str]:
    """
    Construye un perfil horario TMY (Typical Meteorological Year) de 8760h
    combinando dos fuentes de NASA POWER:

    1. MAGNITUD MENSUAL: promedio climatológico 2005-2024 ya calculado por
       get_nasa_power_irradiance() — 20 años, estadísticamente robusto.

    2. FORMA INTRADIARIA: distribución horaria de un año de referencia obtenida
       de la API horaria NASA POWER — captura la curva solar real del sitio.

    Metodología (equivalente a TMY simplificado NREL/SAM):
      Para cada mes m:
        factor_m = irr_media_mensual[m] * 1000/24 / mean(irr_horaria_año_ref[mes_m])
        irr_tmy[h] = irr_horaria_año_ref[h] * factor_m   (para h ∈ mes_m)

    Esto garantiza que:
      - La irradiancia integrada mensual coincide con el P50 de 20 años
      - La forma de la curva solar (ascenso/descenso, horas pico) es realista
      - La temperatura usa el promedio mensual si se proporciona

    Devuelve (DataFrame 8760h, mensaje_error).
    """
    MONTH_DAYS_TMY = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # ── 1. Obtener perfil intradiario del año de referencia ─────────────────
    df_ref, err = get_nasa_hourly(lat, lon, year_ref)
    if err or df_ref is None:
        return None, f"No se pudo obtener perfil horario de referencia: {err}"

    irr_ref = df_ref["irradiance_Wm2"].values  # W/m²
    temp_ref = df_ref["temp_C"].values
    wind_ref = df_ref["wind_ms"].values

    # ── 2. Escalar mes a mes para que la magnitud coincida con el P50 20a ──
    tmy_irr  = irr_ref.copy().astype(float)
    tmy_temp = temp_ref.copy().astype(float)

    hour_cursor = 0
    for m in range(12):
        n_hours = MONTH_DAYS_TMY[m] * 24
        h_start = hour_cursor
        h_end   = min(hour_cursor + n_hours, len(irr_ref))
        h_slice = slice(h_start, h_end)

        # Media de la irradiancia horaria del mes de referencia (W/m²)
        irr_slice = irr_ref[h_slice]
        mean_ref_wm2 = irr_slice.mean()  # W/m² media horaria del mes

        # Target: convertir irr_media_mensual[m] (kWh/m²/día) a W/m² media horaria
        # kWh/m²/día = Wh/m²/día / 1000
        # W/m² media 24h = kWh/m²/día * 1000 / 24
        target_wm2 = irr_media_mensual[m] * 1000 / 24

        # Factor de escala
        if mean_ref_wm2 > 1.0:   # evitar división por cero en meses sin sol
            factor = target_wm2 / mean_ref_wm2
        else:
            factor = 1.0

        tmy_irr[h_slice] = np.clip(irr_ref[h_slice] * factor, 0, 1500)

        # Temperatura: si se proporcionan promedios mensuales climatológicos, centrar
        if temp_media_mensual is not None:
            t_offset = temp_media_mensual[m] - temp_ref[h_slice].mean()
            tmy_temp[h_slice] = temp_ref[h_slice] + t_offset

        hour_cursor = h_end

    # ── 3. Construir DataFrame TMY ──────────────────────────────────────────
    # Generar timestamps para un año no bisiesto (2023)
    ts = pd.date_range(f"{year_ref}-01-01 00:00", periods=len(tmy_irr), freq="h")
    n  = min(len(tmy_irr), 8760)

    df_tmy = pd.DataFrame({
        "datetime":        ts[:n],
        "irradiance_Wm2":  tmy_irr[:n].round(2),
        "temp_C":          tmy_temp[:n].round(2),
        "wind_ms":         wind_ref[:n].round(2),
    })

    # Verificación: energía total debe estar cerca del esperado
    irr_total_kwh_m2 = df_tmy["irradiance_Wm2"].sum() / 1000   # kWh/m²/año
    irr_expected     = sum(irr_media_mensual[m] * MONTH_DAYS_TMY[m] for m in range(12))
    error_pct        = abs(irr_total_kwh_m2 - irr_expected) / max(irr_expected, 1) * 100

    meta = (f"TMY 8760h construido · Irrad. total: {irr_total_kwh_m2:.0f} kWh/m²/año "
            f"(esperado {irr_expected:.0f}, error {error_pct:.1f}%) · "
            f"Temp. media: {df_tmy['temp_C'].mean():.1f}°C · "
            f"Fuente climatológica: NASA POWER 2005–2024")

    return df_tmy, meta




def simulate_pv_8760(
    irr_8760: tuple,      # W/m²  por hora
    temp_8760: tuple,     # °C por hora
    kwp: float,
    pr_base: float,       # PR base (0-1)
    panel_temp_coeff: float = -0.004,  # %/°C pérdida por temperatura (típico -0.4%/°C)
    t_ref: float = 25.0,              # Temperatura STC
    t_noct: float = 45.0,             # NOCT del panel
) -> tuple:
    """
    Simula generación PV hora a hora con corrección de temperatura.
    Fórmula estándar IEC 61724:
      T_cell = T_amb + (NOCT-20)/800 * G
      PR_efectivo = PR_base * (1 + coeff*(T_cell - T_ref))
      P_hora = kwp * (G/1000) * PR_efectivo
    PR clampado a [0, PR_base]: 0 es el límite físico correcto (potencia nunca negativa);
    PR_base es el techo ya que el coeff térmico solo penaliza (coeff < 0).
    Devuelve tuple de 8760 valores en kW.
    """
    gen = []
    for i in range(len(irr_8760)):
        g    = max(0.0, irr_8760[i])          # W/m²
        t    = temp_8760[i]
        t_cell = t + (t_noct - 20) / 800 * g   # temperatura de celda
        pr_eff = pr_base * (1 + panel_temp_coeff * (t_cell - t_ref))
        # Límite inferior 0.0 (física real): el panel nunca genera energía negativa.
        # El límite anterior de 0.5 era arbitrario y subestimaba pérdidas en climas extremos.
        pr_eff = max(0.0, min(pr_eff, pr_base))
        p_kw   = kwp * (g / 1000) * pr_eff
        gen.append(round(p_kw, 4))
    return tuple(gen)



def financial_8760(
    grid_import_kwh: float,
    tarifa_mxn_kwh: float,
    inflation_pct: float,
    capex_usd: float,
    usd_to_mxn: float,
    discount_rate_pct: float,
    vida_util: int,
    om_pct: float,
    panel_degradation_pct: float,
    baseline_cost_mxn: float,      # gasto CFE sin proyecto (año 1)
) -> dict:
    """
    Modelo financiero para proyectos PV 8760h.
    Ahorro = baseline_cost - costo_red_con_proyecto (con inflación y degradación).
    """
    r       = discount_rate_pct / 100
    inf     = inflation_pct / 100
    inv_mxn = capex_usd * usd_to_mxn
    deg     = panel_degradation_pct / 100

    years   = list(range(1, vida_util + 1))
    costo_red_y1 = grid_import_kwh * tarifa_mxn_kwh

    ahorro_y = []
    om_y     = []
    fn_y     = []
    fd_y     = []

    for y in years:
        # Degradación compuesta año a año (modelo IEC 61724 / NREL):
        # factor = (1 - deg)^(y-1)  — no lineal, porque cada año degrada sobre el anterior.
        factor_deg  = max(0.0, (1 - deg) ** (y - 1))
        # Ahorro: baseline CFE - costo red con proyecto (ambos con inflación)
        base_y = baseline_cost_mxn * (1 + inf) ** (y - 1)
        red_y  = costo_red_y1 * factor_deg * (1 + inf) ** (y - 1)
        ahorro = base_y - red_y
        om     = inv_mxn * (om_pct / 100) * (1 + inf) ** (y - 1)
        fn     = ahorro - om
        fd     = fn / (1 + r) ** y
        ahorro_y.append(ahorro)
        om_y.append(om)
        fn_y.append(fn)
        fd_y.append(fd)

    vpn = -inv_mxn + sum(fd_y)

    # TIR — función compartida a nivel de módulo (_bisection_irr)
    tir = _bisection_irr([-inv_mxn] + fn_y)

    acum = -inv_mxn
    pb_s = None
    for i, fn in enumerate(fn_y):
        prev = acum; acum += fn
        if acum >= 0 and pb_s is None:
            pb_s = round(years[i] - 1 + (-prev) / (acum - prev), 1)

    acum_d = -inv_mxn
    pb_d   = None
    acum_desc_list = []
    for i, fd in enumerate(fd_y):
        prev = acum_d; acum_d += fd
        acum_desc_list.append(acum_d)
        if acum_d >= 0 and pb_d is None:
            pb_d = round(years[i] - 1 + (-prev) / (acum_d - prev), 1)

    acum_nom = []
    run = -inv_mxn
    for fn in fn_y:
        run += fn; acum_nom.append(run)

    # LCOE: costo nivelado por kWh ahorrado.
    # Degradación exponencial (1-deg)^(y-1) — consistente con factor_deg en el loop.
    pv_kwh = sum(
        (grid_import_kwh * max(0.0, (1 - deg) ** (y - 1))) / (1 + r) ** y
        for y in years
    )
    pv_cost = inv_mxn + sum(om_y[i] / (1+r)**years[i] for i in range(len(years)))
    lcoe = pv_cost / pv_kwh if pv_kwh > 0 else 0

    return dict(
        vpn=round(vpn, 0), tir=tir, pb_simple=pb_s, pb_disc=pb_d, lcoe=round(lcoe, 4),
        capex_mxn=round(inv_mxn, 0),
        years=years, ahorro_y=ahorro_y, om_y=om_y,
        fn_y=fn_y, fd_y=fd_y,
        acum_nom=acum_nom, acum_desc=acum_desc_list,
    )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRE-SIZING / TOR
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    col_p, col_r = st.columns([1, 1.8], gap="large")

    with col_p:
        # ── Datos del proyecto ─────────────────────────────────────────────────
        st.markdown('<div class="section-header">Datos del proyecto</div>', unsafe_allow_html=True)
        proj_loc  = st.text_input("Ubicación / dirección", value=f"{lat:.4f}, {lon:.4f}")

        # ── Mapa de ubicación ─────────────────────────────────────────────────
        st.markdown('<div class="section-header">Mapa de ubicación</div>', unsafe_allow_html=True)
        fig_map = go.Figure(go.Scattermapbox(
            lat=[lat], lon=[lon],
            mode="markers",
            marker=dict(size=14, color=AMBER, opacity=0.95),
            text=["Ubicación del proyecto"],
            hovertemplate="<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        ))
        fig_map.update_layout(
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=lat, lon=lon),
                zoom=11,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=220,
            paper_bgcolor="#0a0c10",
            plot_bgcolor="#ffffff",
            showlegend=False,
        )
        st.plotly_chart(fig_map, use_container_width=True, config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["toImage", "select2d", "lasso2d"],
            "scrollZoom": True,
        })

        # ── Modo de dimensionamiento ───────────────────────────────────────────
        st.markdown('<div class="section-header">Modo de dimensionamiento</div>', unsafe_allow_html=True)
        sizing_mode = st.radio(
            "Método de sizing",
            ["📐 Por área disponible", "🧾 Por datos del recibo CFE"],
            horizontal=False,
            help="'Por área': calcula cuántos paneles caben en el espacio disponible. 'Por recibo': dimensiona con el consumo mensual real de tus facturas CFE."
        )
        uso_area    = sizing_mode == "📐 Por área disponible"

        if uso_area:
            # ── Área disponible ────────────────────────────────────────────────
            st.markdown('<div class="section-header">Área disponible</div>', unsafe_allow_html=True)
            area_total = st.number_input("Área total disponible (m²)", 10.0, 50000.0, 200.0, 10.0)
            occ_factor = st.slider("Factor de ocupación (%)", 40, 95, 75, 5,
                help="% del área realmente aprovechable (sin obstáculos, accesos, bordes de seguridad)")
        else:
            # ── Datos del recibo CFE — histórico mensual ──────────────────────
            st.markdown('<div class="section-header">Histórico mensual (12 meses)</div>', unsafe_allow_html=True)
            st.markdown('<div class="nasa-box">📅 Ingresa el consumo y tarifa de cada mes. El importe se calcula automáticamente. Puedes obtener los datos de tus recibos bimestrales (divide entre 2) o del portal CFE.</div>', unsafe_allow_html=True)

            uso_historico = True  # único modo disponible

            # Defaults razonables
            cons_default = [500.0, 480.0, 460.0, 450.0, 470.0, 550.0,
                            600.0, 580.0, 510.0, 470.0, 460.0, 520.0]
            tar_default  = [2.80] * 12

            st.markdown('<div class="section-header">Consumo y tarifa mensual</div>', unsafe_allow_html=True)
            st.caption("Edita Consumo y Tarifa — el Importe se recalcula automáticamente.")

            # Construir df base
            # ── Tabla editable: solo Consumo y Tarifa son editables ──────────
            # El Importe se recalcula automáticamente cada render.
            df_input = pd.DataFrame({
                "Mes":              MONTHS,
                "Consumo (kWh)":    cons_default,
                "Tarifa (MXN/kWh)": tar_default,
            })

            df_edit = st.data_editor(
                df_input,
                column_config={
                    "Mes":              st.column_config.TextColumn(disabled=True),
                    "Consumo (kWh)":    st.column_config.NumberColumn(
                        min_value=0.0, max_value=12_000_000.0, step=10.0, format="%.0f"),
                    "Tarifa (MXN/kWh)": st.column_config.NumberColumn(
                        min_value=0.0, max_value=50.0, step=0.0001, format="%.4f",
                        help="Precio medio pagado ese mes"),
                },
                hide_index=True, use_container_width=True, key="hist_mensual",
                num_rows="fixed",
            )

            cons_edit = [float(v) for v in df_edit["Consumo (kWh)"].tolist()]
            tar_edit  = [float(v) for v in df_edit["Tarifa (MXN/kWh)"].tolist()]
            imp_calc  = [round(cons_edit[i] * tar_edit[i], 0) for i in range(12)]

            # Mostrar tabla con importe calculado (read-only, siempre actualizada)
            df_show = pd.DataFrame({
                "Mes":              MONTHS,
                "Consumo (kWh)":    [f"{v:,.0f}" for v in cons_edit],
                "Tarifa (MXN/kWh)": [f"${v:.3f}" for v in tar_edit],
                "Importe (MXN)":    [f"${v:,.0f}" for v in imp_calc],
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            st.caption("↑ Importe = Consumo × Tarifa (actualizado automáticamente)")

            monthly_cons_input = tuple(cons_edit)
            monthly_tar_input  = tuple(tar_edit)

            # Resumen rápido
            consumo_anual_hist = sum(monthly_cons_input)
            gasto_anual_hist   = sum(imp_calc)
            tar_media_hist     = gasto_anual_hist / consumo_anual_hist if consumo_anual_hist > 0 else 0
            mes_max_idx        = monthly_cons_input.index(max(monthly_cons_input))
            mes_min_idx        = monthly_cons_input.index(min(monthly_cons_input))
            st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px;">
  <div class="snap-card" style="min-height:72px;padding:10px 8px;">
    <div class="sc-label">Consumo anual</div>
    <div class="sc-val" style="font-size:clamp(12px,1.1vw,16px);">{consumo_anual_hist:,.0f}</div>
    <div class="sc-sub">kWh/año</div>
  </div>
  <div class="snap-card" style="min-height:72px;padding:10px 8px;">
    <div class="sc-label">Gasto anual CFE</div>
    <div class="sc-val" style="font-size:clamp(12px,1.1vw,16px);">${gasto_anual_hist:,.0f}</div>
    <div class="sc-sub">MXN/año</div>
  </div>
  <div class="snap-card" style="min-height:72px;padding:10px 8px;">
    <div class="sc-label">Tarifa media real</div>
    <div class="sc-val" style="color:#f59e0b;font-size:clamp(12px,1.1vw,16px);">${tar_media_hist:.3f}</div>
    <div class="sc-sub">MXN/kWh ponderada</div>
  </div>
  <div class="snap-card" style="min-height:72px;padding:10px 8px;">
    <div class="sc-label">Mes pico / valle</div>
    <div class="sc-val" style="font-size:clamp(11px,1vw,14px);">{MONTHS[mes_max_idx]} / {MONTHS[mes_min_idx]}</div>
    <div class="sc-sub">{max(monthly_cons_input):,.0f} / {min(monthly_cons_input):,.0f} kWh</div>
  </div>
</div>
""", unsafe_allow_html=True)


            # ── Slider kWp manual ──────────────────────────────────────────────
            st.markdown('<div class="section-header">Tamaño del sistema</div>', unsafe_allow_html=True)

            # Referencia: kWp para ~80% cobertura con irradiancia media
            _irr_prom = sum(active_irr) / 12 if sum(active_irr) > 0 else 5.0
            _kwp_ref  = consumo_anual_hist * 0.80 / (_irr_prom * effective_pr * 365)
            _kwp_ref  = max(1.0, _kwp_ref)
            _kwp_max  = max(20.0, round(_kwp_ref * 2.5 / 5) * 5)

            kwp_manual = st.slider(
                "Capacidad del sistema (kWp)",
                min_value=1.0, max_value=float(_kwp_max),
                value=float(max(1.0, round(_kwp_ref / 5) * 5)),
                step=0.5,
                help="Mueve para explorar la cobertura solar. El sistema se redondea al número entero de paneles.",
                key="kwp_slider_recibo",
            )
            # Preview instantáneo — kWp y cobertura con fórmula correcta (capeada por mes)
            _n_prev   = max(1, round(kwp_manual * 1000 / panel_wp))
            _kwp_prev = _n_prev * panel_wp / 1000
            _gen_prev = [_kwp_prev * active_irr[m] * effective_pr * MONTH_DAYS[m] for m in range(12)]
            # Cobertura correcta: min(gen, consumo) mes a mes / consumo total
            # No usar gen_total/consumo_total — sobreestima cuando hay excedentes mensuales
            _cob_prev = (sum(min(_gen_prev[m], monthly_cons_input[m]) for m in range(12))
                         / max(consumo_anual_hist, 1) * 100)
            _cc = "#4ade80" if _cob_prev >= 80 else ("#facc15" if _cob_prev >= 50 else "#f87171")
            st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:6px 0 4px;">
  <div class="snap-card" style="min-height:72px;">
    <div class="sc-label">Paneles</div>
    <div class="sc-val" style="font-size:16px;color:#f1f5f9;">{_n_prev}</div>
    <div class="sc-sub">{panel_wp} Wp c/u</div>
  </div>
  <div class="snap-card" style="min-height:72px;">
    <div class="sc-label">kWp instalados</div>
    <div class="sc-val" style="font-size:16px;color:#f1f5f9;">{_kwp_prev:.1f}</div>
    <div class="sc-sub">kWp</div>
  </div>
  <div class="snap-card" style="min-height:72px;">
    <div class="sc-label">Cobertura anual</div>
    <div class="sc-val" style="font-size:16px;color:{_cc};">{_cob_prev:.1f}%</div>
    <div class="sc-sub">del consumo total</div>
  </div>
</div>
""", unsafe_allow_html=True)

            area_total      = 0.0
            occ_factor      = 75
            solar_pct       = 80          # legacy — no usado en este modo
            sizing_strategy = "Promedio anual (económico)"  # legacy

        # ── Irradiancia (siempre visible) ──────────────────────────────────────
        st.markdown('<div class="section-header">Irradiancia mensual (kWh/m²/día)</div>',
                    unsafe_allow_html=True)
        irr_source_banner()
        irr_df1 = pd.DataFrame({"Mes": MONTHS, "Irradiancia (kWh/m²/día)": active_irr})
        irr_ed1 = st.data_editor(irr_df1, column_config={
            "Mes": st.column_config.TextColumn(disabled=True),
            "Irradiancia (kWh/m²/día)": st.column_config.NumberColumn(
                min_value=0.0, max_value=10.0, step=0.0001, format="%.4f"),
        }, hide_index=True, use_container_width=True, key="irr1")
        irr_vals = irr_ed1["Irradiancia (kWh/m²/día)"].tolist()

    # ── Calculations — todo cacheado ───────────────────────────────────────────
    with col_r:

        irr_tuple = tuple(irr_vals)

        # ── MODO 8760h: simulación horaria completa ───────────────────────────
        if uso_area:
            sz = calc_sizing_area(area_total, occ_factor, panel_wp, panel_area,
                                  irr_tuple, effective_pr)
            monthly_cons_ref = None
            monthly_tar_ref  = None
            tarifa_efectiva  = tarifa
            uso_historico_r  = False
        else:
            uso_historico_r = uso_historico
            if uso_historico:
                _ok_r, _msg_r = _validate_recibo_inputs(monthly_cons_input, monthly_tar_input)
                if not _ok_r:
                    st.error(f"⚠️ Datos de recibo inválidos: {_msg_r}")
                    st.stop()
                sz = calc_sizing_recibo_kwp(
                    monthly_cons_input, monthly_tar_input,
                    max(kwp_manual, 0.5),
                    panel_wp, panel_area,
                    irr_tuple, effective_pr,
                    occ_factor=occ_factor)  # FIX: pasar factor de ocupación del usuario
                monthly_cons_ref = sz["monthly_cons"]
                monthly_tar_ref  = sz["monthly_tarifas"]
                tarifa_efectiva  = sz["tarifa_media_pond"]


        n_panels   = sz["n_panels"]
        kwp        = sz["kwp"]
        area_util  = sz["area_util"]
        area_used  = sz["area_used"]
        monthly_gen = sz["monthly_gen"]
        annual_gen  = sz["annual_gen"]

        daily_avg   = annual_gen / 365
        co2_saved   = annual_gen * CO2_FACTOR_KG_KWH   # kg/año  (factor SEN SENER/CENACE)
        co2_saved_t = co2_saved / 1000     # toneladas/año
        # HSP promedio anual: promedio de los valores mensuales de irradiancia
        hsp_anual   = sum(irr_vals) / 12   # kWh/m²/día promedio anual
        if hsp_anual >= 5.5:
            hsp_nota = "✅ Excelente recurso solar (≥ 5.5 kWh/m²/día · referencia IEA/NREL)"
            hsp_color = "#4ade80"
        elif hsp_anual >= 4.5:
            hsp_nota = "🟡 Buen recurso solar (4.5–5.5 kWh/m²/día)"
            hsp_color = "#facc15"
        else:
            hsp_nota = "🔴 Recurso solar bajo (< 4.5 kWh/m²/día · validar viabilidad)"
            hsp_color = "#f87171"
        inversion_usd = kwp * costo_kwp
        inversion     = inversion_usd  # mantener alias USD para compatibilidad con TOR
        inversion_mxn = inversion_usd * usd_to_mxn
        # En modo histórico el ahorro real ya está calculado con tarifas mensuales reales
        if not uso_area and uso_historico_r and "ahorro_anual" in sz:
            ahorro1 = sz["ahorro_anual"]
        else:
            ahorro1 = annual_gen * tarifa_efectiva
        # FIX Bug 1: payback calculado en MXN/MXN → resultado en años (antes era USD/MXN)
        payback = inversion_mxn / ahorro1 if ahorro1 > 0 else 999
        tarifa_efectiva = _safe(tarifa_efectiva, fallback=2.80, min_val=0.01, label="tarifa efectiva")

        # ── P50 / P90 riguroso con serie interanual NASA POWER ────────────────
        # Si el usuario no ha cargado datos NASA, no hay serie histórica y
        # se muestra un aviso en lugar de un número inventado.
        p50_real, p90_real, gen_por_anio = compute_p90(
            active_irr_por_anio, kwp, effective_pr
        )
        has_p90 = p50_real is not None
        # Para el TOR usamos P50 = generación con irr media editada
        p50 = annual_gen
        p90 = p90_real if has_p90 else None

        # ── TOR HERO — resultados en encabezado ───────────────────────────────
        area_label = f"{area_used:.0f} m² de {area_util:.0f} útiles" if uso_area else f"{area_used:.0f} m² estimados"
        st.markdown(f"""
<div class="tor-hero">
  <div class="th-project">📋 PRE-SIZING • {"ÁREA DISPONIBLE" if uso_area else "RECIBO CFE"}</div>
  <div class="th-meta">
    {proj_loc} &nbsp;·&nbsp; <span class="pr-badge pr-green">● PR {pr_pct:.1f}%</span>
    {"" if uso_area else f"&nbsp;·&nbsp; Tarifa media: <b>${tarifa_efectiva:.3f}/kWh</b>"}
  </div>
  <div class="th-grid">
    <div class="th-item">
      <span class="th-label">CAPACIDAD PICO</span>
      <span class="th-val">{kwp:,.1f}</span>
      <span class="th-unit">kWp</span>
    </div>
    <div class="th-item">
      <span class="th-label">PANELES</span>
      <span class="th-val">{n_panels:,.0f}</span>
      <span class="th-unit">unidades • {panel_wp} Wp</span>
    </div>
    <div class="th-item">
      <span class="th-label">GENERACIÓN AÑO 1</span>
      <span class="th-val">{p50/1000:,.1f}</span>
      <span class="th-unit">MWh/año</span>
    </div>
    <div class="th-item">
      <span class="th-label">GENERACIÓN P90</span>
      <span class="th-val">{"—" if not has_p90 else f"{p90/1000:,.1f}"}</span>
      <span class="th-unit">{"Carga NASA" if not has_p90 else "MWh/año"}</span>
    </div>
    <div class="th-item">
      <span class="th-label">{"ÁREA UTILIZADA" if uso_area else "COBERTURA SOLAR"}</span>
      <span class="th-val">{"" if uso_area else f"{sz.get('cobertura_anual', 0):.1f}" if monthly_cons_ref else "—"}{f"{area_used:,.1f}" if uso_area else ""}</span>
      <span class="th-unit">{"m²" if uso_area else "% del consumo · min(gen,cons) por mes"}</span>
    </div>
    <div class="th-item">
      <span class="th-label">INVERSIÓN REF.</span>
      <span class="th-val">${inversion:,.0f}</span>
      <span class="th-unit">USD · ≈ ${inversion_mxn:,.0f} MXN</span>
    </div>
    <div class="th-item">
      <span class="th-label">AHORRO AÑO 1</span>
      <span class="th-val">${ahorro1:,.0f}</span>
      <span class="th-unit">MXN · tarifa ${tarifa_efectiva:.3f}/kWh</span>
    </div>
    <div class="th-item">
      <span class="th-label">PAYBACK SIMPLE</span>
      <span class="th-val">{payback:.1f}</span>
      <span class="th-unit">años · nominal<br><span style="font-size:9px;color:#475569;">Ver modelo financiero ↓ para payback descontado</span></span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── ALERTA REGULATORIA para Generación Distribuida ─────────────────────
        if kwp > 699:
            st.error("⚠️ **Proyecto mayor a 699 kWp** — supera el límite típico de Generación Distribuida en México.")
        if uso_area:
            max_kwp_gd = 699
            area_max_gd = max_kwp_gd * 1000 / panel_wp * panel_area / (occ_factor / 100)
            st.caption(f"📏 Área máx. para GD (<700 kWp): **{area_max_gd:,.0f} m²** (con {occ_factor}% ocupación)")
        else:
            consumo_anual_ref = sum(monthly_cons_ref) if monthly_cons_ref else 0
            cobertura_pct = annual_gen / max(consumo_anual_ref, 1) * 100
            st.caption(f"📊 Consumo anual estimado: **{consumo_anual_ref:,.0f} kWh** · Cobertura: **{cobertura_pct:.1f}%** · Tarifa media: **${tarifa_efectiva:.3f}/kWh**")
        # ── Panel activo (mini card) ────────────────────────────────────────────
        st.markdown(f"""
<div class="panel-card">
  <div class="pc-title">📋 Panel de referencia</div>
  <div class="pc-grid">
    <div class="pc-item"><span class="pc-label">Potencia</span>
      <span class="pc-val">{panel_wp} Wp</span></div>
    <div class="pc-item"><span class="pc-label">Eficiencia calc.</span>
      <span class="pc-val" style="color:{eff_color}">{panel_eff_calc:.2f}%
        <span style="font-size:10px;color:{eff_color}">{eff_note}</span></span></div>
    <div class="pc-item"><span class="pc-label">Dimensiones</span>
      <span class="pc-val">{panel_largo_mm}×{panel_ancho_mm} mm</span></div>
    <div class="pc-item"><span class="pc-label">Área unitaria</span>
      <span class="pc-val">{panel_area:.4f} m²</span></div>
    <div class="pc-item"><span class="pc-label">Peso</span>
      <span class="pc-val">{panel_peso_kg} kg</span></div>
    <div class="pc-item"><span class="pc-label">Densidad potencia</span>
      <span class="pc-val">{panel_wp/panel_area:.0f} Wp/m²</span></div>
  </div>
  <div style="border-top:1px solid #2a2d3a;margin-top:10px;padding-top:10px;">
    <div class="pc-title" style="margin-bottom:8px;">⚖️ Carga estructural estimada</div>
    <div class="pc-grid">
      <div class="pc-item">
        <span class="pc-label">Carga total (×1.35)</span>
        <span class="pc-val" style="color:#f87171;">{n_panels * panel_peso_kg * 1.35:,.0f} kg</span>
      </div>
      <div class="pc-item">
        <span class="pc-label">Carga total</span>
        <span class="pc-val" style="color:#f87171;">{n_panels * panel_peso_kg * 1.35 * 9.8 / 1000:,.2f} kN</span>
      </div>
      <div class="pc-item">
        <span class="pc-label">Carga por m² instalado</span>
        <span class="pc-val" style="color:#f87171;">{n_panels * panel_peso_kg * 1.35 * 9.8 / 1000 / max(n_panels * panel_area, 0.01):.3f} kN/m²</span>
      </div>
      <div class="pc-item">
        <span class="pc-label">Factor extra aplicado</span>
        <span class="pc-val" style="color:#9ca3af;">+35% montura/BOS</span>
      </div>
    </div>
  </div>

  <!-- HSP promedio anual -->
  <div style="border-top:1px solid #1e2230;margin-top:10px;padding-top:10px;">
    <div class="pc-title" style="margin-bottom:8px;">☀️ Recurso solar del sitio</div>
    <div class="pc-grid">
      <div class="pc-item">
        <span class="pc-label">HSP promedio anual</span>
        <span class="pc-val" style="color:{hsp_color};">{hsp_anual:.2f} kWh/m²/día</span>
      </div>
      <div class="pc-item">
        <span class="pc-label">Evaluación</span>
        <span class="pc-val" style="font-size:11px;color:{hsp_color};font-family:Inter,sans-serif;">{hsp_nota}</span>
      </div>
    </div>
  </div>

  <!-- CO2 -->
  <div style="border-top:1px solid #1e2230;margin-top:10px;padding-top:10px;">
    <div class="pc-title" style="margin-bottom:8px;">🌿 Impacto ambiental año 1</div>
    <div class="pc-grid">
      <div class="pc-item">
        <span class="pc-label">CO₂ evitado</span>
        <span class="pc-val" style="color:#4ade80;">{co2_saved_t:,.2f} ton/año</span>
      </div>
      <div class="pc-item">
        <span class="pc-label">Factor de emisión utilizado</span>
        <span class="pc-val" style="font-size:11px;color:#64748b;font-family:Inter,sans-serif;">{CO2_FACTOR_KG_KWH} kg CO₂e/kWh · SEN 2024 · SEMARNAT/CRE 28-Feb-2025</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── Si modo recibo: mostrar comparativa consumo vs generación ───────────
        if not uso_area and monthly_cons_ref:
            st.markdown('<div class="section-header">Generación vs Consumo mensual</div>', unsafe_allow_html=True)

            # Usar datos detallados si están disponibles
            if uso_historico_r and "ahorro_mensual" in sz:
                excedente_m = sz["excedente"]
                coverage_m  = sz["cobertura_pct"]
                ahorro_m    = sz["ahorro_mensual"]
                energy_cov  = sz["energia_cubierta"]
            else:
                excedente_m = [monthly_gen[m] - monthly_cons_ref[m] for m in range(12)]
                coverage_m  = [min(100, monthly_gen[m] / max(monthly_cons_ref[m], 1) * 100) for m in range(12)]
                tar_mes     = monthly_tar_ref if monthly_tar_ref else [tarifa_efectiva]*12
                ahorro_m    = [min(monthly_gen[m], monthly_cons_ref[m]) * tar_mes[m] for m in range(12)]
                energy_cov  = [min(monthly_gen[m], monthly_cons_ref[m]) for m in range(12)]

            fig_cv = go.Figure()
            fig_cv.add_trace(go.Bar(x=MONTHS, y=monthly_cons_ref, name="Consumo",
                marker_color="#374151",
                hovertemplate="<b>%{x}</b><br>Consumo: %{y:,.0f} kWh<extra></extra>"))
            fig_cv.add_trace(go.Bar(x=MONTHS, y=energy_cov, name="Cubierto solar",
                marker_color=AMBER,
                hovertemplate="<b>%{x}</b><br>Cubierto: %{y:,.0f} kWh<extra></extra>"))
            fig_cv.add_trace(go.Scatter(x=MONTHS, y=monthly_gen, mode="lines+markers",
                name="Generación total", line=dict(color=TEAL, width=2, dash="dot"),
                marker=dict(size=6, color=TEAL),
                hovertemplate="<b>%{x}</b><br>Generación: %{y:,.0f} kWh<extra></extra>"))
            lyt_cv = copy.deepcopy(PLOT_LAYOUT)
            lyt_cv.update({"height": 270, "barmode": "overlay",
                           "yaxis": dict(title="kWh", gridcolor="#2a2d3a"),
                           "legend": dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
                           "margin": dict(l=20, r=20, t=30, b=40)})
            fig_cv.update_layout(**lyt_cv)
            st.plotly_chart(fig_cv, use_container_width=True)

            # ── Resumen de ahorro por mes (reemplaza gráfica de tarifa) ──────────
            if uso_historico_r and monthly_tar_ref:
                st.markdown('<div class="section-header">Ahorro mensual estimado</div>', unsafe_allow_html=True)
                ahorro_html = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:0.75rem;">'
                for i, m in enumerate(MONTHS):
                    color = "#4ade80" if ahorro_m[i] > 0 else "#f87171"
                    ahorro_html += f"""
  <div style="background:#111318;border:0.5px solid #1e2230;border-radius:10px;padding:8px 6px;text-align:center;">
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">{m}</div>
    <div style="font-size:13px;font-weight:600;color:{color};font-family:'JetBrains Mono',monospace;">${ahorro_m[i]:,.0f}</div>
    <div style="font-size:9px;color:#475569;margin-top:2px;">${monthly_tar_ref[i]:.3f}/kWh</div>
  </div>"""
                ahorro_html += '</div>'
                ahorro_html += f"""<div style="display:flex;justify-content:flex-end;font-size:12px;color:#94a3b8;margin-top:2px;">
  Ahorro anual total: <span style="color:#4ade80;font-weight:600;margin-left:6px;">${sum(ahorro_m):,.0f} MXN</span>
</div>"""
                st.markdown(ahorro_html, unsafe_allow_html=True)

            # ── Tabla mensual ──────────────────────────────────────────────────
            st.markdown('<div class="section-header">Tabla mensual detallada</div>', unsafe_allow_html=True)
            tar_display = monthly_tar_ref if monthly_tar_ref else [tarifa_efectiva]*12
            df_tabla = pd.DataFrame({
                "Mes":               MONTHS,
                "Consumo (kWh)":    [f"{v:,.0f}" for v in monthly_cons_ref],
                "Generación (kWh)": [f"{v:,.0f}" for v in monthly_gen],
                "Cubierto (kWh)":   [f"{v:,.0f}" for v in energy_cov],
                "Cobertura (%)":    [f"{v:.1f}%" for v in coverage_m],
                "Excedente (kWh)":  [f"+{v:,.0f}" if v >= 0 else f"{v:,.0f}" for v in excedente_m],
                "Tarifa ($/kWh)":   [f"${t:.3f}" for t in tar_display],
                "Ahorro (MXN)":     [f"${v:,.0f}" for v in ahorro_m],
            })
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)

            # cobertura_anual = Σ min(gen_mes, cons_mes) / Σ cons_mes × 100
            # Fórmula correcta: no cuenta excedente que va a red como cobertura del consumo
            cobertura_anual = sz.get("cobertura_anual",
                sum(energy_cov) / max(sum(monthly_cons_ref), 1) * 100)
            st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px;">
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Consumo anual</div>
    <div class="sc-val" style="font-size:14px;">{sum(monthly_cons_ref):,.0f}</div>
    <div class="sc-sub">kWh/año</div>
  </div>
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Cobertura solar</div>
    <div class="sc-val" style="color:#f59e0b;font-size:14px;">{cobertura_anual:.1f}%</div>
    <div class="sc-sub">del consumo anual</div>
  </div>
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Ahorro anual</div>
    <div class="sc-val" style="color:#4ade80;font-size:14px;">${sum(ahorro_m):,.0f}</div>
    <div class="sc-sub">MXN/año</div>
  </div>
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Tarifa media real</div>
    <div class="sc-val" style="font-size:14px;">${tarifa_efectiva:.3f}</div>
    <div class="sc-sub">MXN/kWh ponderada</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── Gráfica Mensual + Variabilidad interanual ─────────────────────────
        st.markdown('<div class="section-header">Generación mensual estimada</div>',
                    unsafe_allow_html=True)

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=MONTHS, y=monthly_gen,
            name="Generación P50 (irr. media)",
            marker_color=AMBER, opacity=0.95,
            hovertemplate="<b>%{x}</b><br>P50: %{y:,.0f} kWh<extra></extra>"
        ))
        fig1.add_trace(go.Scatter(
            x=MONTHS, y=irr_vals,
            mode="lines+markers",
            name="Irradiancia NASA (2005–2024)",
            yaxis="y2",
            line=dict(color=ROSE, width=3, dash="dot"),
            marker=dict(size=7, color=ROSE, line=dict(width=1.5, color="white")),
            hovertemplate="<b>%{x}</b><br>Irradiancia: %{y:.4f} kWh/m²/día<extra></extra>"
        ))
        layout1 = copy.deepcopy(PLOT_LAYOUT)
        layout1.update({
            "height": 380, "barmode": "group",
            "title": dict(text="Generación Mensual (P50 con irradiancia media)", font=dict(size=15)),
            "yaxis":  dict(title="kWh generados", gridcolor="#2a2d3a", tickformat=",", rangemode="tozero"),
            "yaxis2": dict(title="Irradiancia (kWh/m²/día)", overlaying="y", side="right",
                           range=[0, max(irr_vals) * 1.25],
                           tickfont=dict(color=ROSE), tickformat=".2f"),
            "legend": dict(orientation="h", y=-0.22, x=0.5, xanchor="center", yanchor="top",
                           font=dict(size=13), bgcolor="rgba(0,0,0,0)",
                           bordercolor="#2a2d3a", borderwidth=1),
            "margin": dict(l=20, r=80, t=60, b=100),
            "hovermode": "x unified",
        })
        fig1.update_layout(**layout1)
        st.plotly_chart(fig1, use_container_width=True)

        # ── Distribución interanual + P90 real ────────────────────────────────
        if has_p90:
            st.markdown('<div class="section-header">Variabilidad interanual · P90 riguroso</div>',
                        unsafe_allow_html=True)
            n_anios = len(gen_por_anio)

            # Aviso metodológico
            st.markdown(
                f'<div class="nasa-box">🔬 P90 calculado como percentil 10 de la generación anual '
                f'simulada con los {n_anios} años de irradiancia real NASA POWER '
                f'({NASA_START}–{NASA_END}). '
                f'El sistema supera el P90 el 90% de los años históricos.</div>',
                unsafe_allow_html=True)

            anios  = list(gen_por_anio.keys())
            gen_v  = [gen_por_anio[y] / 1000 for y in anios]   # MWh
            p50_mwh = p50_real / 1000
            p90_mwh = p90_real / 1000

            # Colores: rojo si el año está por debajo del P90, ámbar si debajo del P50
            bar_colors = [
                ROSE  if v < p90_mwh else
                AMBER if v < p50_mwh else
                TEAL
                for v in gen_v
            ]

            fig_p90 = go.Figure()

            # Barras con bordes suaves y hover enriquecido
            fig_p90.add_trace(go.Bar(
                x=anios, y=gen_v,
                name="Generación anual",
                marker=dict(
                    color=bar_colors,
                    line=dict(color="rgba(0,0,0,0)", width=0),
                    cornerradius=4,
                ),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Generación: <b>%{y:,.1f} MWh</b><extra></extra>"
                ),
                showlegend=False,
            ))

            # Línea P50 — sin anotación flotante
            fig_p90.add_hline(
                y=p50_mwh,
                line_color=AMBER,
                line_dash="dash",
                line_width=1.8,
            )

            # Línea P90 — sin anotación flotante
            fig_p90.add_hline(
                y=p90_mwh,
                line_color=ROSE,
                line_dash="dot",
                line_width=1.8,
            )

            layout_p90 = copy.deepcopy(PLOT_LAYOUT)
            layout_p90.update({
                "height": 360,
                "yaxis": dict(
                    title="MWh/año",
                    gridcolor="#1e2130",
                    zeroline=False,
                    tickfont=dict(size=11),
                ),
                "xaxis": dict(
                    tickmode="linear",
                    dtick=1,
                    gridcolor="rgba(0,0,0,0)",
                    tickfont=dict(size=11),
                    tickangle=-45,
                ),
                "bargap": 0.25,
                "legend": dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                               bgcolor="rgba(0,0,0,0)"),
                "margin": dict(l=20, r=20, t=20, b=60),
                "hovermode": "x unified",
            })
            fig_p90.update_layout(**layout_p90)
            st.plotly_chart(fig_p90, use_container_width=True)

            # Leyenda manual debajo de la gráfica (limpia, sin anotaciones encima)
            st.markdown(f"""
<div style="display:flex; gap:28px; justify-content:center; flex-wrap:wrap;
            margin-top:-8px; margin-bottom:12px; font-size:12px; color:#9ca3af;">
  <span style="display:flex; align-items:center; gap:7px;">
    <span style="display:inline-block; width:26px; height:2px;
                 background:repeating-linear-gradient(90deg,{AMBER} 0,{AMBER} 6px,transparent 6px,transparent 10px);"></span>
    P50 = {p50_mwh:,.1f} MWh &nbsp;·&nbsp; mediana histórica
  </span>
  <span style="display:flex; align-items:center; gap:7px;">
    <span style="display:inline-block; width:26px; height:2px;
                 background:repeating-linear-gradient(90deg,{ROSE} 0,{ROSE} 4px,transparent 4px,transparent 7px);"></span>
    P90 = {p90_mwh:,.1f} MWh &nbsp;·&nbsp; superado el 90% de los años
  </span>
  <span style="display:flex; align-items:center; gap:7px;">
    <span style="display:inline-block; width:12px; height:12px; border-radius:3px; background:{TEAL};"></span>
    Por encima del P50
  </span>
  <span style="display:flex; align-items:center; gap:7px;">
    <span style="display:inline-block; width:12px; height:12px; border-radius:3px; background:{AMBER};"></span>
    Entre P90 y P50
  </span>
  <span style="display:flex; align-items:center; gap:7px;">
    <span style="display:inline-block; width:12px; height:12px; border-radius:3px; background:{ROSE};"></span>
    Por debajo del P90
  </span>
</div>
""", unsafe_allow_html=True)

            # Métricas compactas P90
            mp1, mp2, mp3, mp4 = st.columns(4)
            mp1.metric("P50",        f"{p50_mwh:,.1f} MWh")
            mp2.metric("P90", f"{p90_mwh:,.1f} MWh",
                       f"{(p90_real/p50_real - 1)*100:+.1f}% vs P50")
            mp3.metric("Mejor año",  f"{max(gen_v):,.1f} MWh")
            mp4.metric("Peor año",   f"{min(gen_v):,.1f} MWh")
        else:
            st.info("ℹ️ Carga datos de NASA POWER desde el sidebar para calcular el P90 riguroso con variabilidad interanual.")


    # ── Modelo financiero — cacheado ──────────────────────────────────────
    # Si P90 está disponible se usa como base conservadora (recomendado);
    # si no, se cae a P50 (generación con irradiancia media).
    gen_para_fm = p90_real if has_p90 else annual_gen
    fm_base_label = "P90" if has_p90 else "P50"
    fm = calc_financial_model(
        gen_para_fm, kwp, float(inversion),
        tarifa_efectiva, inflation, discount_rate,
        panel_degradation, vida_util, usd_to_mxn,
        om_pct=om_pct_sidebar
    )
    years         = fm["years"]
    gen_proj      = fm["gen_proj"]
    tarifas_y     = fm["tarifas_y"]
    flujo_nominal = fm["flujo_nominal"]
    om_anual      = fm["om_anual"]
    flujo_neto    = fm["flujo_neto"]
    factor_desc   = fm["factor_desc"]
    flujo_desc    = fm["flujo_desc"]
    acum_nominal  = fm["acum_nominal"]
    acum_desc     = fm["acum_desc"]
    inversion_mxn = fm["inv_mxn"]
    vpn           = fm["vpn"]
    tir           = fm["tir"]
    tir_str       = f"{tir:.1f}%" if tir is not None else "N/A"
    pb_simple     = fm["pb_simple"]
    pb_simple_str = f"{pb_simple:.1f} años" if pb_simple else f">{vida_util} años"
    pb_disc       = fm["pb_disc"]
    pb_disc_str   = f"{pb_disc:.1f} años" if pb_disc else f">{vida_util} años"
    lcoe          = fm["lcoe"]

    # ── 2. KPIs principales ───────────────────────────────────────────────
    kc = "#4ade80" if vpn > 0 else "#f87171"

    st.markdown(f"""
<div style="margin-bottom:0.5rem">
  <div class="section-header">Modelo financiero · {vida_util} años · base {fm_base_label}</div>
</div>
<div style="display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-bottom:12px;">

  <div class="snap-card">
    <div class="sc-label">VPN</div>
    <div class="sc-val" style="color:{kc};">${vpn:,.0f}</div>
    <div class="sc-sub">MXN</div>
  </div>

  <div class="snap-card">
    <div class="sc-label">TIR</div>
    <div class="sc-val" style="color:#22d3ee;">{tir_str}</div>
    <div class="sc-sub">vs {discount_rate}% WACC</div>
  </div>

  <div class="snap-card">
    <div class="sc-label">LCOE</div>
    <div class="sc-val" style="color:{VIOLET};">${lcoe:.2f}</div>
    <div class="sc-sub">MXN/kWh generado</div>
  </div>

  <div class="snap-card">
    <div class="sc-label">Payback simple</div>
    <div class="sc-val" style="color:#f9fafb;">{pb_simple_str}</div>
    <div class="sc-sub">flujos nominales</div>
  </div>

  <div class="snap-card">
    <div class="sc-label">Payback descontado</div>
    <div class="sc-val" style="color:#f9fafb;">{pb_disc_str}</div>
    <div class="sc-sub">flujos descontados</div>
  </div>

  <div class="snap-card">
    <div class="sc-label">O&amp;M año 1</div>
    <div class="sc-val" style="color:#6b7280;">${om_anual[0]:,.0f}</div>
    <div class="sc-sub">MXN (est. {om_pct_sidebar:.1f}% inv.)</div>
  </div>

</div>
""", unsafe_allow_html=True)

    # ── Gráficas en dos columnas — fila 1 ─────────────────────────────────
    fm_col1, fm_col2 = st.columns(2, gap="medium")

    with fm_col1:
        st.markdown('<div class="section-header">Flujos de efectivo anuales</div>',
                    unsafe_allow_html=True)
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(
            x=years, y=flujo_neto,
            name="Flujo neto nominal",
            marker_color=AMBER, opacity=0.9,
            hovertemplate="<b>Año %{x}</b><br>Flujo neto: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_cf.add_trace(go.Bar(
            x=years, y=flujo_desc,
            name="Flujo descontado",
            marker_color=TEAL, opacity=0.85,
            hovertemplate="<b>Año %{x}</b><br>Flujo desc.: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_cf.add_trace(go.Scatter(
            x=years, y=om_anual,
            name="O&M anual",
            mode="lines+markers",
            line=dict(color=ROSE, width=2, dash="dot"),
            marker=dict(size=5, color=ROSE),
            hovertemplate="<b>Año %{x}</b><br>O&M: $%{y:,.0f} MXN<extra></extra>",
        ))
        lay_cf = copy.deepcopy(PLOT_LAYOUT)
        lay_cf.update({
            "height": 360, "barmode": "group",
            "yaxis": dict(title="MXN", gridcolor="#1e2230", tickformat=","),
            "xaxis": dict(title="Año", tickmode="linear", dtick=max(1, vida_util // 10), gridcolor="#1e2230"),
            "legend": dict(orientation="h", y=1.12, x=0.5, xanchor="center", bgcolor="rgba(0,0,0,0)"),
            "margin": dict(l=10, r=10, t=50, b=40),
            "hovermode": "x unified",
        })
        fig_cf.update_layout(**lay_cf)
        st.plotly_chart(fig_cf, use_container_width=True)

    with fm_col2:
        st.markdown('<div class="section-header">VPN acumulado y payback</div>',
                    unsafe_allow_html=True)
        fig_vpn = go.Figure()
        fig_vpn.add_trace(go.Scatter(
            x=[0] + years, y=[-inversion_mxn] + acum_desc,
            name="VPN acumulado (desc.)",
            mode="lines+markers",
            line=dict(color=TEAL, width=3),
            marker=dict(size=6, color=TEAL),
            fill="tozeroy",
            fillcolor="rgba(20,184,166,0.08)",
            hovertemplate="<b>Año %{x}</b><br>VPN acum.: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_vpn.add_trace(go.Scatter(
            x=[0] + years, y=[-inversion_mxn] + acum_nominal,
            name="Acum. nominal",
            mode="lines",
            line=dict(color=AMBER, width=2, dash="dash"),
            hovertemplate="<b>Año %{x}</b><br>Acum. nominal: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_vpn.add_hline(y=0, line_color="#475569", line_dash="solid", line_width=1)
        if pb_disc:
            fig_vpn.add_vline(x=pb_disc, line_color=TEAL, line_dash="dot", line_width=1.5,
                              annotation_text=f"PB desc. {pb_disc:.1f}a",
                              annotation_font=dict(color=TEAL, size=10))
        if pb_simple and pb_simple != pb_disc:
            fig_vpn.add_vline(x=pb_simple, line_color=AMBER, line_dash="dot", line_width=1.5,
                              annotation_text=f"PB simple {pb_simple:.1f}a",
                              annotation_font=dict(color=AMBER, size=10),
                              annotation_position="bottom right")
        lay_vpn = copy.deepcopy(PLOT_LAYOUT)
        lay_vpn.update({
            "height": 320,
            "yaxis": dict(title="MXN acumulados", gridcolor="#1e2230", tickformat=","),
            "xaxis": dict(title="Año", tickmode="linear", dtick=max(1, vida_util // 10), gridcolor="#1e2230"),
            "legend": dict(orientation="h", y=1.12, x=0.5, xanchor="center", bgcolor="rgba(0,0,0,0)"),
            "margin": dict(l=10, r=10, t=50, b=40),
            "hovermode": "x unified",
        })
        fig_vpn.update_layout(**lay_vpn)
        st.plotly_chart(fig_vpn, use_container_width=True)

    # ── Gráfica sensibilidad + tabla — fila 2 ─────────────────────────────
    fm_col3, fm_col4 = st.columns([1, 1.4], gap="medium")

    with fm_col3:
        st.markdown('<div class="section-header">Sensibilidad VPN vs WACC</div>',
                    unsafe_allow_html=True)
        tasas_sens = [i * 0.5 for i in range(0, 61)]
        vpn_sens   = []
        for t_s in tasas_sens:
            r_s = t_s / 100
            fd_s = [flujo_neto[i] / (1 + r_s) ** years[i] for i in range(len(years))]
            vpn_sens.append(-inversion_mxn + sum(fd_s))

        fig_sens = go.Figure()
        fig_sens.add_trace(go.Scatter(
            x=tasas_sens, y=vpn_sens,
            mode="lines", name="VPN",
            line=dict(color=TEAL, width=3),
            fill="tozeroy",
            fillcolor="rgba(20,184,166,0.10)",
            hovertemplate="<b>WACC %{x:.1f}%</b><br>VPN: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_sens.add_vline(x=discount_rate, line_color=AMBER, line_dash="dash", line_width=2,
                           annotation_text=f"WACC {discount_rate}%",
                           annotation_font=dict(color=AMBER, size=10))
        if tir is not None:
            fig_sens.add_vline(x=tir, line_color=ROSE, line_dash="dot", line_width=2,
                               annotation_text=f"TIR {tir:.1f}%",
                               annotation_font=dict(color=ROSE, size=10),
                               annotation_position="top right")
        fig_sens.add_hline(y=0, line_color="#475569", line_width=1)
        lay_sens = copy.deepcopy(PLOT_LAYOUT)
        lay_sens.update({
            "height": 300,
            "yaxis": dict(title="VPN (MXN)", gridcolor="#1e2230", tickformat=","),
            "xaxis": dict(title="WACC (%)", gridcolor="#1e2230",
                          range=[0, max(32, (tir or 0) + 5)]),
            "legend": dict(orientation="h", y=1.12, x=0.5, xanchor="center", bgcolor="rgba(0,0,0,0)"),
            "margin": dict(l=10, r=10, t=50, b=40),
        })
        fig_sens.update_layout(**lay_sens)
        st.plotly_chart(fig_sens, use_container_width=True)

    with fm_col4:
        st.markdown('<div class="section-header">Tabla financiera año a año</div>',
                    unsafe_allow_html=True)
        tabla_fin = pd.DataFrame({
            "Año":               years,
            "Gen. (MWh)":        [f"{g/1000:,.2f}" for g in gen_proj],
            "Tarifa ($/kWh)":    [f"${t:.3f}" for t in tarifas_y],
            "Ingreso (MXN)":     [f"${v:,.0f}" for v in flujo_nominal],
            "O&M (MXN)":         [f"${v:,.0f}" for v in om_anual],
            "Flujo neto (MXN)":  [f"${v:,.0f}" for v in flujo_neto],
            "Flujo desc. (MXN)": [f"${v:,.0f}" for v in flujo_desc],
            "VPN acum. (MXN)":   [f"${v:,.0f}" for v in acum_desc],
        })
        st.dataframe(tabla_fin, use_container_width=True, hide_index=True)

    # ── Totales — ancho completo ───────────────────────────────────────────
    st.markdown(f"""
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:12px;">
  <div class="snap-card">
    <div class="sc-label">Ingreso bruto total</div>
    <div class="sc-val" style="color:#f9fafb;">${sum(flujo_nominal):,.0f}</div>
    <div class="sc-sub">MXN nominales</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">O&amp;M total (nominal)</div>
    <div class="sc-val" style="color:#6b7280;">${sum(om_anual):,.0f}</div>
    <div class="sc-sub">MXN nominales</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Flujo neto total</div>
    <div class="sc-val" style="color:#f9fafb;">${sum(flujo_neto):,.0f}</div>
    <div class="sc-sub">MXN nominales</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">VPN final</div>
    <div class="sc-val" style="color:{'#4ade80' if vpn>0 else '#f87171'};">${vpn:,.0f}</div>
    <div class="sc-sub">MXN</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Criterio de decisión
    if tir is None:
        st.warning("⚠️ No se pudo calcular la TIR (flujo sin solución en el rango analizado).")
    elif vpn > 0 and tir > discount_rate + 3:
        st.success("🟢 **Proyecto muy atractivo** — VPN positivo y TIR supera significativamente el costo de capital.")
    elif vpn > 0 and tir > discount_rate:
        st.success("🟡 **Proyecto atractivo** — VPN positivo y TIR supera el costo de capital.")
    else:
        st.error("🔴 **Proyecto poco atractivo** — VPN negativo o TIR por debajo del costo de capital.")

            # ── Exportar TOR ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Exportar TOR</div>', unsafe_allow_html=True)

    # Llamada corregida y simplificada a build_tor_text
    tor_text = build_tor_text(
        "Proyecto Solar",
        "—",
        proj_loc,
        "",
        panel_wp,
        panel_eff_declared,
        panel_largo_mm,
        panel_ancho_mm,
        panel_peso_kg,
        panel_area,
        n_panels,
        kwp,
        pr_pct,
        irr_vals,
        monthly_gen,
        annual_gen,
        p50,
        p90,
        co2_saved,
        inversion,
        ahorro1,
        payback,
        gen_por_anio,
    )

    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        st.download_button(
            "⬇️ Descargar TOR (.txt)",
            data=tor_text.encode("utf-8"),
            file_name=f"TOR_Solar_{proj_loc[:20].replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True)
    with ex2:
        pdf_sizing_bytes = build_pdf_sizing(
            proj_loc=proj_loc, lat=lat, lon=lon,
            panel_wp=panel_wp, panel_eff_declared=panel_eff_declared,
            panel_largo_mm=panel_largo_mm, panel_ancho_mm=panel_ancho_mm,
            panel_peso_kg=panel_peso_kg, panel_area=panel_area,
            n_panels=n_panels, kwp=kwp, pr_pct=pr_pct,
            irr_vals=irr_vals, monthly_gen=monthly_gen, annual_gen=annual_gen,
            p50=p50, p90=p90, co2_saved=co2_saved,
            inversion_usd=float(inversion), usd_to_mxn=usd_to_mxn,
            ahorro1=ahorro1, payback=payback,
            vpn=vpn, tir=tir, lcoe=lcoe, pb_disc=pb_disc,
            tarifa_efectiva=tarifa_efectiva, inflation=inflation,
            discount_rate=discount_rate, vida_util=vida_util,
            om_pct=om_pct_sidebar,
            sizing_mode_label="Por área" if uso_area else "Por recibo CFE",
        )
        st.download_button(
            "📄 Exportar PDF — Sizing",
            data=pdf_sizing_bytes,
            file_name=f"Sizing_Solar_{proj_loc[:20].replace(' ','_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    with ex3:
        if st.button("📝 Generar Caso de Negocio (.docx)",
                     use_container_width=True, key="btn_word_turnkey"):
            with st.spinner("Generando Word…"):
                try:
                    import datetime as _dt
                    _consumo_a = sum(monthly_cons_ref) if monthly_cons_ref else 0
                    _cob_pct   = sz.get("cobertura_anual", 0) if not uso_area else 0
                    _word_bytes = build_word_turnkey(
                        proj_loc=proj_loc, lat=lat, lon=lon,
                        fecha=_dt.date.today().strftime("%B %Y"),
                        kwp=kwp, n_panels=n_panels,
                        panel_wp=panel_wp, panel_eff_declared=panel_eff_declared,
                        panel_largo_mm=panel_largo_mm, panel_ancho_mm=panel_ancho_mm,
                        panel_peso_kg=panel_peso_kg,
                        area_used=area_used, inversion_usd=float(inversion),
                        inversion_mxn=inversion_mxn, usd_to_mxn=usd_to_mxn,
                        costo_kwp=costo_kwp,
                        ahorro1=ahorro1, co2_saved_t=co2_saved_t,
                        hsp_anual=hsp_anual, annual_gen=annual_gen,
                        p50=p50, p90_real=p90_real,
                        pr_pct=pr_pct, panel_degradation=panel_degradation,
                        vida_util=vida_util, wacc=discount_rate,
                        inflacion_cfe=inflation,
                        tarifa_efectiva=tarifa_efectiva,
                        om_pct_sidebar=om_pct_sidebar,
                        vpn=vpn, tir=tir, pb_simple=pb_simple,
                        pb_disc=pb_disc, lcoe=lcoe,
                        fm=fm,
                        consumo_anual=_consumo_a,
                        cobertura_pct=_cob_pct,
                        # Datos para gráficas embebidas:
                        irr_vals=list(active_irr),
                        monthly_gen=list(monthly_gen),
                        monthly_cons=list(monthly_cons_ref) if monthly_cons_ref else None,
                    )
                    st.session_state["word_turnkey_bytes"] = _word_bytes
                    st.success("✅ Documento generado")
                except Exception as _e:
                    st.error(f"❌ Error generando Word: {_e}")
        if "word_turnkey_bytes" in st.session_state:
            import datetime as _dt2
            st.download_button(
                "⬇️ Descargar Caso de Negocio (.docx)",
                data=st.session_state["word_turnkey_bytes"],
                file_name=f"CasoNegocio_Turnkey_{proj_loc[:20].replace(' ','_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — PPA · VENTA AL CLIENTE
# ═════════════════════════════════════════════════════════════════════════════
with tab3:

    st.markdown("""
    <div class="info-box">
    💡 <b>Power Purchase Agreement (PPA)</b> — El cliente paga por la energía generada a una
    tarifa fija acordada ($/kWh), en lugar de comprar la instalación. Tú (o el financiador)
    eres dueño del sistema durante el plazo del contrato. Evalúa distintos plazos y
    encuentra el precio PPA que hace viable el proyecto.
    </div>
    """, unsafe_allow_html=True)

    ppa_col1, ppa_col2, ppa_col3 = st.columns([1.1, 1.1, 1.8], gap="large")

    with ppa_col1:
        st.markdown('<div class="section-header">Sistema base</div>', unsafe_allow_html=True)

        # Valores heredados de Turnkey Solar (Tab 1)
        _kwp_turnkey = max(1.0, round(float(kwp), 1))
        _inv_turnkey = max(1000.0, round(float(kwp) * float(costo_kwp), 0))

        st.markdown(f"""
<div class="info-box" style="margin-bottom:0.5rem;">
  📐 <b>Valores importados de Turnkey Solar:</b>
  {_kwp_turnkey:.1f} kWp &nbsp;·&nbsp; ${_inv_turnkey:,.0f} USD inversión.
  Puedes editarlos abajo si deseas simular un escenario diferente.
</div>
""", unsafe_allow_html=True)

        ppa_kwp = st.number_input("Capacidad (kWp)", 1.0, 50000.0,
                                   _kwp_turnkey, 1.0, key="ppa_kwp")

        # ── Generación base: siempre P90 cuando está disponible ──────────────
        _p50_val = max(100.0, round(float(annual_gen), 0))
        _p90_val = max(100.0, round(float(p90), 0)) if p90 else None
        _has_p90 = _p90_val is not None

        if _has_p90:
            st.markdown(
                f'<div class="nasa-box">🔬 <b>Base de generación: P90</b> — '
                f'{_p90_val:,.0f} kWh/año · estándar de la industria para contratos PPA. '
                f'El sistema supera este valor el 90% de los años históricos (NASA POWER {NASA_START}–{NASA_END}). '
                f'P50 = {_p50_val:,.0f} kWh/año (mediana).</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="warn-box">⚠️ <b>P90 no disponible — usando P50 como base.</b> '
                'Carga datos NASA POWER desde el sidebar para usar el P90 (recomendado para PPA).</div>',
                unsafe_allow_html=True,
            )

        _gen_default = _p90_val if _has_p90 else _p50_val
        _gen_label   = f"Generación año 1 — {'P90' if _has_p90 else 'P50'} (kWh/año)"

        ppa_gen_anual = st.number_input(_gen_label, 100.0, 50_000_000.0,
                                         _gen_default, 100.0, key="ppa_gen")
        ppa_inversion_usd = st.number_input("Inversión total (USD)", 1000.0, 50_000_000.0,
                                             _inv_turnkey, 100.0, key="ppa_inv")
        st.caption(f"≈ ${ppa_inversion_usd * usd_to_mxn:,.0f} MXN al tipo de cambio configurado")

        st.markdown('<div class="section-header">Parámetros técnicos</div>', unsafe_allow_html=True)
        ppa_degradacion  = st.slider("Degradación anual (%)", 0.0, 1.5, 0.5, 0.05, key="ppa_deg")
        ppa_om_pct       = st.slider("O&M anual (% inv. MXN)", 0.3, 2.5, 1.0, 0.1, key="ppa_om")
        ppa_seguros_pct  = st.slider("Seguros / otros (% inv. MXN)", 0.0, 1.0, 0.3, 0.05, key="ppa_seg")

    with ppa_col2:
        st.markdown('<div class="section-header">Condiciones financieras</div>', unsafe_allow_html=True)
        ppa_wacc             = st.slider("WACC (%)", 5.0, 30.0, 15.0, 0.5, key="ppa_wacc")
        ppa_spread_hurdle    = st.number_input(
            "Spread objetivo sobre WACC (%)", 0.5, 10.0, 4.0, 0.5,
            key="ppa_spread",
            help=f"Hurdle rate = WACC + spread. La tarifa objetivo es el precio PPA donde TIR equity = WACC + spread. Default 4%."
        )
        ppa_inflacion_tarifa = st.slider("Escalador PPA anual (%)", 0.0, 8.0, 3.5, 0.5, key="ppa_esc",
                                          help="Incremento anual pactado en el precio PPA")
        ppa_inflacion_om     = st.slider("Inflación O&M anual (%)", 0.0, 8.0, 4.0, 0.5, key="ppa_inf_om")

        ppa_financiamiento = st.checkbox("¿Incluir financiamiento?", value=False, key="ppa_fin_chk")
        if ppa_financiamiento:
            ppa_equity_pct  = st.slider("Capital propio (%)", 10, 100, 30, 5, key="ppa_eq")
            ppa_tasa_deuda  = st.slider("Tasa deuda anual (%)", 5.0, 25.0, 12.0, 0.5, key="ppa_debt_r")
            ppa_plazo_deuda = st.slider("Plazo deuda (años)", 3, 20, 10, 1, key="ppa_debt_p")
        else:
            ppa_equity_pct  = 100
            ppa_tasa_deuda  = 0.0
            ppa_plazo_deuda = 0

        st.markdown('<div class="section-header">Valor de rescate</div>', unsafe_allow_html=True)
        ppa_usar_valor_residual = st.checkbox(
            "Incluir valor de rescate en el modelo",
            value=True,
            key="ppa_usar_vr",
            help=(
                "El valor de rescate es el VPN de los flujos que el sistema seguirá generando "
                "después del contrato PPA, si la vida útil del panel es mayor al plazo. "
                "Cuando está activado, mejora el VPN del desarrollador al reconocer que el activo "
                "tiene valor residual. Desactívalo para un escenario más conservador, o cuando el "
                "contrato PPA cubre toda la vida útil del sistema."
            ),
        )
        if ppa_usar_valor_residual:
            st.markdown(
                '<div class="info-box" style="font-size:12px;">'
                '☑️ <b>Activo</b> — Se calcula el VPN de los flujos post-contrato usando anuidad '
                'con crecimiento compuesto (Gordon generalizado, suma finita exacta). '
                'Mejora el VPN del desarrollador cuando el plazo es menor a la vida útil del sistema.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="warn-box" style="font-size:12px;">'
                '☐ <b>Inactivo</b> — El modelo asume que el activo no tiene valor al final del contrato. '
                'Escenario conservador: útil cuando el cliente adquiere el sistema al término del PPA '
                'o cuando se desea bankability sin asumir flujos futuros.'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-header">Tarifa CFE del cliente</div>', unsafe_allow_html=True)
        ppa_tarifa_cliente = st.number_input("Tarifa actual (MXN/kWh)", 0.5, 15.0,
                                              max(0.5, round(float(tarifa_efectiva), 2)),
                                              0.05, key="ppa_tar")
        ppa_inflacion_cfe  = st.slider("Inflación CFE anual (%)", 0.0, 12.0, 6.0, 0.5, key="ppa_inf_cfe")

    with ppa_col3:
        st.markdown('<div class="section-header">Precio PPA a evaluar</div>', unsafe_allow_html=True)
        ppa_precio_manual = st.number_input(
            "Precio PPA año 1 (MXN/kWh)", 0.50, 10.0, 1.80, 0.05, key="ppa_price",
            help="Ajusta este valor hasta encontrar el precio óptimo para tu cliente")

        st.markdown('<div class="section-header">Plazos a comparar</div>', unsafe_allow_html=True)
        st.caption("Define hasta 4 plazos en años (1–30). Deja en 0 para desactivar.")
        _pc1, _pc2 = st.columns(2)
        _p_raw = [
            _pc1.number_input("Plazo 1 (años)", 0, 30, 10, 1, key="ppa_p1"),
            _pc2.number_input("Plazo 2 (años)", 0, 30, 15, 1, key="ppa_p2"),
            _pc1.number_input("Plazo 3 (años)", 0, 30, 20, 1, key="ppa_p3"),
            _pc2.number_input("Plazo 4 (años)", 0, 30, 25, 1, key="ppa_p4"),
        ]
        # Filtrar duplicados y ceros, ordenar
        ppa_plazos = sorted(set(p for p in _p_raw if p > 0))
        if len(ppa_plazos) == 0:
            st.warning("Define al menos un plazo mayor a 0.")
            ppa_plazos = [10]
        if len(ppa_plazos) > 1 and len(set(ppa_plazos)) < len(_p_raw):
            st.caption("ℹ️ Se eliminaron plazos duplicados o en cero.")

        st.markdown('<div class="section-header">Plazo objetivo</div>', unsafe_allow_html=True)
        ppa_plazo_minimo = st.selectbox("Plazo para análisis detallado", ppa_plazos, key="ppa_pmin_plazo")

    # ── Calcular todos los plazos — usando funciones cacheadas globales ──────
    # Si el usuario desactivó el valor de rescate, se pasa vida_util_total = plazo
    # para que anios_restantes = 0 y valor_residual = 0 en todos los escenarios.
    ppa_cache_kwargs = dict(
        gen1=ppa_gen_anual, inv_usd=ppa_inversion_usd,
        wacc_pct=ppa_wacc, esc_ppa=ppa_inflacion_tarifa,
        deg=ppa_degradacion, om_pct=ppa_om_pct,
        inf_om=ppa_inflacion_om, seg_pct=ppa_seguros_pct,
        usd_mx=usd_to_mxn, equity_pct=ppa_equity_pct,
        tasa_deuda=ppa_tasa_deuda, plazo_deuda=ppa_plazo_deuda,
        con_fin=ppa_financiamiento,
        vida_util_total=vida_util)

    resultados = {}
    # ppa_cache_kwargs_hurdle: igual que ppa_cache_kwargs pero con wacc = hurdle rate.
    # El VPN del comparativo se calcula con la tasa del hurdle rate (WACC + spread)
    # para ser consistente con el encabezado "Hurdle rate WACC+X% = Y%".
    ppa_cache_kwargs_hurdle = {**ppa_cache_kwargs, "wacc_pct": ppa_wacc + ppa_spread_hurdle}
    for pl in ppa_plazos:
        _vida_util_eff = vida_util if ppa_usar_valor_residual else pl
        _kwargs_pl        = {**ppa_cache_kwargs,        "vida_util_total": _vida_util_eff}
        _kwargs_pl_hurdle = {**ppa_cache_kwargs_hurdle, "vida_util_total": _vida_util_eff}
        # VPN y payback descontado se calculan con hurdle rate (tasa que ve el usuario)
        res = dict(calc_ppa_result(precio_ppa=ppa_precio_manual, plazo=pl, **_kwargs_pl_hurdle))
        # TIR y payback simple no dependen de la tasa de descuento — se toman del calculo base (WACC)
        res_base = dict(calc_ppa_result(precio_ppa=ppa_precio_manual, plazo=pl, **_kwargs_pl))
        res["tir"] = res_base["tir"]
        res["pb"]  = res_base["pb"]
        # VPN a WACC base y VPN a precio ofrecido (precio manual) con hurdle rate
        res["vpn_wacc"]     = res_base["vpn"]   # VPN descontado a WACC base
        res["vpn_hurdle"]   = res["vpn"]        # VPN descontado a hurdle rate (ya calculado)
        res["pm"] = calc_precio_minimo(
            plazo=pl, vida_util_total=_vida_util_eff,
            **{k: v for k, v in _kwargs_pl.items() if k != "vida_util_total"})
        res["ph"] = calc_precio_hurdle(
            plazo=pl, vida_util_total=_vida_util_eff,
            spread_pct=ppa_spread_hurdle,
            **{k: v for k, v in _kwargs_pl.items() if k != "vida_util_total"})
        resultados[pl] = res

    descuento_vs_cfe = ((ppa_precio_manual / ppa_tarifa_cliente) - 1) * 100
    pm_obj = resultados[ppa_plazo_minimo]["pm"]
    viable = pm_obj is not None and ppa_precio_manual >= pm_obj
    color_viable = "#4ade80" if viable else "#f87171"
    pm_str = f"${pm_obj:.4f}/kWh" if pm_obj else "No viable en este plazo"

    # ── Hero PPA ─────────────────────────────────────────────────────────────
    ro_obj = resultados[ppa_plazo_minimo]
    val_res = ro_obj.get("valor_residual", 0.0)
    _anios_rest = max(0, vida_util - ppa_plazo_minimo) if ppa_usar_valor_residual else 0
    _g_ing = round((ppa_inflacion_tarifa - ppa_degradacion), 2)
    if not ppa_usar_valor_residual:
        val_res_str = "Desactivado (escenario conservador)"
        _nota_rescate = "El valor de rescate está excluido del modelo. Actívalo en Condiciones financieras."
        _vr_color = "#64748b"
    elif val_res > 0:
        val_res_str = f"${val_res:,.0f} MXN"
        _nota_rescate = (
            f"Gordon generalizado · suma finita exacta · {_anios_rest} años restantes · "
            f"g_ingreso = {_g_ing:+.2f}%/año (escalador {ppa_inflacion_tarifa:.1f}% - degradación {ppa_degradacion:.2f}%) · "
            f"descontado a WACC {ppa_wacc:.1f}% desde t={ppa_plazo_minimo}"
        )
        _vr_color = "#14b8a6"
    else:
        val_res_str = "Contrato = vida útil" if vida_util <= ppa_plazo_minimo else "—"
        _nota_rescate = "Contrato cubre toda la vida útil del sistema" if vida_util <= ppa_plazo_minimo else "Sin años restantes"
        _vr_color = "#475569"
    _hurdle_label = f"WACC+{ppa_spread_hurdle:.0f}% = {ppa_wacc + ppa_spread_hurdle:.1f}%"
    st.markdown(f"""
<div class="tor-hero" style="margin-top:1rem;">
  <div class="th-project">📄 ANÁLISIS PPA · Plazo objetivo {ppa_plazo_minimo} años
    &nbsp;·&nbsp; Valor de rescate: <span style="color:{'#14b8a6' if ppa_usar_valor_residual else '#64748b'}">{'INCLUIDO' if ppa_usar_valor_residual else 'EXCLUIDO'}</span>
  </div>
  <div class="th-meta">
    Precio evaluado: <b style="color:#f59e0b">${ppa_precio_manual:.4f}/kWh</b>
    &nbsp;·&nbsp; Ahorro cliente vs CFE hoy: <b style="color:#14b8a6">{descuento_vs_cfe:+.1f}%</b>
    &nbsp;·&nbsp; <b style="color:{color_viable}">{'✅ Precio viable' if viable else '⚠️ Por debajo del mínimo'}</b>
  </div>
  <div class="th-grid" style="grid-template-columns:repeat(4,1fr);">
    <div class="th-item">
      <span class="th-label">Precio mínimo viable</span>
      <span class="th-val" style="color:{color_viable};font-size:15px;">{pm_str}</span>
      <span class="th-unit">a {ppa_plazo_minimo} años · VPN = 0</span>
    </div>
    <div class="th-item">
      <span class="th-label">Precio PPA evaluado</span>
      <span class="th-val">${ppa_precio_manual:.4f}</span>
      <span class="th-unit">MXN/kWh año 1</span>
    </div>
    <div class="th-item">
      <span class="th-label">Tarifa CFE cliente</span>
      <span class="th-val">${ppa_tarifa_cliente:.2f}</span>
      <span class="th-unit">MXN/kWh actual</span>
    </div>
    <div class="th-item">
      <span class="th-label">Inversión total</span>
      <span class="th-val">${ppa_inversion_usd:,.0f}</span>
      <span class="th-unit">USD · ${ppa_inversion_usd*usd_to_mxn:,.0f} MXN</span>
    </div>
    <div class="th-item" style="margin-top:10px;">
      <span class="th-label">VALOR DE RESCATE</span>
      <span class="th-val" style="color:{_vr_color};font-size:14px;">{val_res_str}</span>
      <span class="th-unit">{_nota_rescate}</span>
    </div>
    <div class="th-item" style="margin-top:10px;">
      <span class="th-label">VPN a WACC {ppa_wacc:.1f}%</span>
      <span class="th-val" style="color:{'#4ade80' if ro_obj['vpn_wacc']>0 else '#f87171'};font-size:15px;">${ro_obj['vpn_wacc']:,.0f}</span>
      <span class="th-unit">MXN</span>
    </div>
    <div class="th-item" style="margin-top:10px;">
      <span class="th-label">VPN a hurdle {_hurdle_label}</span>
      <span class="th-val" style="color:{'#4ade80' if ro_obj['vpn_hurdle']>0 else '#f87171'};font-size:15px;">${ro_obj['vpn_hurdle']:,.0f}</span>
      <span class="th-unit">MXN</span>
    </div>
    <div class="th-item" style="margin-top:10px;">
      <span class="th-label">TIR equity</span>
      <span class="th-val" style="color:#22d3ee;font-size:15px;">{f"{ro_obj['tir']:.1f}%" if ro_obj['tir'] else '—'}</span>
      <span class="th-unit">vs hurdle {ppa_wacc+ppa_spread_hurdle:.1f}%</span>
    </div>
    <div class="th-item" style="margin-top:10px;">
      <span class="th-label">Payback descontado</span>
      <span class="th-val" style="color:#f1f5f9;font-size:15px;">{f"{ro_obj['pb_disc']} años" if ro_obj.get('pb_disc') else f'>{ppa_plazo_minimo}a'}</span>
      <span class="th-unit">a hurdle {ppa_wacc+ppa_spread_hurdle:.1f}%</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Tarjetas comparativas por plazo ───────────────────────────────────────
    st.markdown(f'<div class="section-header">Comparativo de plazos · Hurdle rate {_hurdle_label}</div>',
                unsafe_allow_html=True)
    cols_pl = st.columns(len(ppa_plazos))
    for idx, pl in enumerate(ppa_plazos):
        r   = resultados[pl]
        vc  = "#4ade80" if r["vpn"]>0 else "#f87171"
        tis = f"{r['tir']:.1f}%" if r["tir"] is not None else "N/A"
        pbs      = f"{r['pb']} años" if r["pb"] else f">{pl}a"
        pbs_disc = f"{r['pb_disc']} años" if r.get("pb_disc") else f">{pl}a"
        pmc = "#4ade80" if r["pm"] and ppa_precio_manual>=r["pm"] else "#f87171"
        pms = f"${r['pm']:.4f}" if r["pm"] else "No viable"
        phs = f"${r['ph']:.4f}" if r.get("ph") else "N/A"
        phc = "#f59e0b" if r.get("ph") and ppa_precio_manual >= r["ph"] else "#94a3b8"
        with cols_pl[idx]:
            st.markdown(f"""
<div class="snap-card" style="min-height:280px;padding:18px 12px;">
  <div class="sc-label" style="font-size:14px;font-weight:700;color:#f59e0b;margin-bottom:12px;">{pl} AÑOS</div>
  <div style="width:100%;text-align:left;display:flex;flex-direction:column;gap:8px;">
    <div><div class="sc-label">VPN a WACC {ppa_wacc:.1f}%</div>
         <div class="sc-val" style="color:{'#4ade80' if r['vpn_wacc']>0 else '#f87171'};font-size:13px;">${r['vpn_wacc']:,.0f}</div></div>
    <div><div class="sc-label">VPN a hurdle {_hurdle_label}</div>
         <div class="sc-val" style="color:{vc};font-size:13px;">${r['vpn_hurdle']:,.0f}</div></div>
    <div><div class="sc-label">TIR equity</div>
         <div class="sc-val" style="color:#22d3ee;font-size:13px;">{tis}</div></div>
    <div><div class="sc-label">Payback simple</div>
         <div class="sc-val" style="color:#f9fafb;font-size:13px;">{pbs}</div></div>
    <div><div class="sc-label">Payback descontado</div>
         <div class="sc-val" style="color:#9ca3af;font-size:13px;">{pbs_disc}</div></div>
    <div style="border-top:1px solid #1e2230;padding-top:8px;margin-top:2px;">
      <div class="sc-label">Precio mínimo viable (VPN=0)</div>
      <div class="sc-val" style="color:{pmc};font-size:13px;">{pms}/kWh</div></div>
    <div><div class="sc-label">Tarifa objetivo ({_hurdle_label})</div>
         <div class="sc-val" style="color:{phc};font-size:13px;">{phs}/kWh</div></div>
    <div><div class="sc-label">Tarifa ofrecida</div>
         <div class="sc-val" style="color:#f1f5f9;font-size:13px;">${ppa_precio_manual:.4f}/kWh</div></div>
    <div><div class="sc-label">Valor de rescate</div>
         <div class="sc-val" style="color:#14b8a6;font-size:13px;">${r['valor_residual']:,.0f}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    # Tabla resumen
    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
    tabla_ppa = []
    for pl in ppa_plazos:
        r = resultados[pl]
        tabla_ppa.append({
            "Plazo":                        f"{pl} años",
            "Precio mínimo (VPN=0)":        f"${r['pm']:.4f}/kWh" if r["pm"] else "No viable",
            f"Tarifa obj. ({_hurdle_label})": f"${r['ph']:.4f}/kWh" if r.get("ph") else "N/A",
            "Tarifa ofrecida":              f"${ppa_precio_manual:.4f}/kWh",
            f"VPN WACC {ppa_wacc:.1f}%":           f"${r['vpn_wacc']:,.0f}",
            f"VPN hurdle {_hurdle_label}":  f"${r['vpn_hurdle']:,.0f}",
            "TIR equity":                   f"{r['tir']:.1f}%" if r["tir"] else "N/A",
            "Payback simple":               f"{r['pb']} años" if r["pb"] else f">{pl}a",
            "Payback desc.":               f"{r['pb_disc']} años" if r.get("pb_disc") else f">{pl}a",
            "Ingreso total":               f"${r['ing_total']:,.0f}",
            "Valor de rescate":            f"${r.get('valor_residual', 0):,.0f}",
        })
    st.dataframe(pd.DataFrame(tabla_ppa), use_container_width=True, hide_index=True)

    # ── Gráficas ──────────────────────────────────────────────────────────────
    gc1, gc2 = st.columns(2, gap="large")

    with gc1:
        st.markdown(f'<div class="section-header">VPN por plazo</div>', unsafe_allow_html=True)
        vpn_wacc_vals   = [resultados[pl]["vpn_wacc"]   for pl in ppa_plazos]
        vpn_hurdle_vals = [resultados[pl]["vpn_hurdle"] for pl in ppa_plazos]
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Bar(
            x=[f"{pl}a" for pl in ppa_plazos], y=vpn_wacc_vals, name=f"WACC {ppa_wacc:.1f}%",
            marker_color=TEAL, opacity=0.85,
            text=[f"${v/1e6:.2f}M" for v in vpn_wacc_vals],
            textposition="outside", textfont=dict(size=11, family="DM Mono"),
            hovertemplate="<b>%{x}</b><br>VPN WACC: $%{y:,.0f} MXN<extra></extra>"))
        fig_vp.add_trace(go.Bar(
            x=[f"{pl}a" for pl in ppa_plazos], y=vpn_hurdle_vals, name=f"Hurdle {ppa_wacc+ppa_spread_hurdle:.1f}%",
            marker_color=AMBER, opacity=0.85,
            text=[f"${v/1e6:.2f}M" for v in vpn_hurdle_vals],
            textposition="outside", textfont=dict(size=11, family="DM Mono"),
            hovertemplate="<b>%{x}</b><br>VPN hurdle: $%{y:,.0f} MXN<extra></extra>"))
        fig_vp.add_hline(y=0, line_color="#6b7280", line_width=1.5)
        lyt_vp = copy.deepcopy(PLOT_LAYOUT)
        lyt_vp.update({"height":300, "barmode": "group",
                       "yaxis": dict(title="VPN (MXN)", gridcolor="#2a2d3a", tickformat=","),
                       "xaxis": dict(title="Plazo"),
                       "margin": dict(l=20,r=20,t=30,b=40),
                       "legend": dict(orientation="h",y=1.12,x=0.5,xanchor="center",bgcolor="rgba(0,0,0,0)",font=dict(size=11))})
        fig_vp.update_layout(**lyt_vp)
        st.plotly_chart(fig_vp, use_container_width=True)

    with gc2:
        st.markdown('<div class="section-header">Precio mínimo viable por plazo</div>', unsafe_allow_html=True)
        pm_vals = [resultados[pl]["pm"] for pl in ppa_plazos]
        fig_pm = go.Figure()
        fig_pm.add_trace(go.Scatter(
            x=[f"{pl}a" for pl in ppa_plazos],
            y=[v if v else None for v in pm_vals],
            mode="lines+markers+text",
            line=dict(color=AMBER, width=3),
            marker=dict(size=10, color=AMBER),
            text=[f"${v:.4f}" if v else "N/V" for v in pm_vals],
            textposition="top center", textfont=dict(size=11, family="DM Mono"),
            name="Precio mínimo",
            hovertemplate="<b>%{x}</b><br>Precio mín: $%{y:.4f}/kWh<extra></extra>"))
        fig_pm.add_hline(y=ppa_precio_manual, line_color=TEAL, line_dash="dash", line_width=2,
                         annotation_text=f"Precio evaluado ${ppa_precio_manual:.4f}",
                         annotation_font=dict(color=TEAL, size=11))
        fig_pm.add_hline(y=ppa_tarifa_cliente, line_color=ROSE, line_dash="dot", line_width=1.5,
                         annotation_text=f"CFE hoy ${ppa_tarifa_cliente:.2f}",
                         annotation_font=dict(color=ROSE, size=11), annotation_position="bottom right")
        lyt_pm = copy.deepcopy(PLOT_LAYOUT)
        lyt_pm.update({"height":300,
                       "yaxis": dict(title="MXN/kWh", gridcolor="#2a2d3a", tickformat=".4f"),
                       "xaxis": dict(title="Plazo"),
                       "margin": dict(l=20,r=20,t=30,b=40),
                       "legend": dict(orientation="h",y=1.1,x=0.5,xanchor="center",bgcolor="rgba(0,0,0,0)")})
        fig_pm.update_layout(**lyt_pm)
        st.plotly_chart(fig_pm, use_container_width=True)

    # ── Flujos anuales plazo objetivo ─────────────────────────────────────────
    st.markdown(f'<div class="section-header">Flujos anuales — {ppa_plazo_minimo} años</div>',
                unsafe_allow_html=True)
    ro = resultados[ppa_plazo_minimo]
    fig_fl = go.Figure()
    fig_fl.add_trace(go.Bar(x=ro["years"], y=ro["ing_y"], name="Ingreso PPA",
        marker_color=AMBER, opacity=0.9,
        hovertemplate="<b>Año %{x}</b><br>Ingreso: $%{y:,.0f} MXN<extra></extra>"))
    costos_y = [ro["om_y"][i]+ro["seg_y"][i] for i in range(ppa_plazo_minimo)]
    fig_fl.add_trace(go.Bar(x=ro["years"], y=costos_y, name="O&M + Seguros",
        marker_color="#374151",
        hovertemplate="<b>Año %{x}</b><br>Costos: $%{y:,.0f} MXN<extra></extra>"))
    if any(d>0 for d in ro["deu_y"]):
        fig_fl.add_trace(go.Bar(x=ro["years"], y=ro["deu_y"], name="Servicio deuda",
            marker_color=ROSE, opacity=0.8,
            hovertemplate="<b>Año %{x}</b><br>Deuda: $%{y:,.0f} MXN<extra></extra>"))
    fig_fl.add_trace(go.Scatter(x=ro["years"], y=ro["fn_y"], name="Flujo neto",
        mode="lines+markers", line=dict(color=TEAL,width=2.5), marker=dict(size=6,color=TEAL),
        hovertemplate="<b>Año %{x}</b><br>Flujo neto: $%{y:,.0f} MXN<extra></extra>"))
    lyt_fl = copy.deepcopy(PLOT_LAYOUT)
    lyt_fl.update({"height":330,"barmode":"stack",
                   "yaxis": dict(title="MXN",gridcolor="#2a2d3a",tickformat=","),
                   "xaxis": dict(title="Año",tickmode="linear",dtick=max(1,ppa_plazo_minimo//10)),
                   "legend": dict(orientation="h",y=1.12,x=0.5,xanchor="center",bgcolor="rgba(0,0,0,0)"),
                   "margin": dict(l=20,r=20,t=50,b=40),"hovermode":"x unified"})
    fig_fl.update_layout(**lyt_fl)
    st.plotly_chart(fig_fl, use_container_width=True)

    # ── Perspectiva del cliente ───────────────────────────────────────────────
    st.markdown('<div class="section-header">Perspectiva del cliente · Ahorro vs CFE</div>',
                unsafe_allow_html=True)
    gen_cl   = ro["gen_y"]
    prec_cl  = ro["prec_y"]
    cfe_y    = [ppa_tarifa_cliente*(1+ppa_inflacion_cfe/100)**i for i in range(ppa_plazo_minimo)]
    pago_ppa = [gen_cl[i]*prec_cl[i] for i in range(ppa_plazo_minimo)]
    pago_cfe = [gen_cl[i]*cfe_y[i]   for i in range(ppa_plazo_minimo)]
    ahorro_y = [pago_cfe[i]-pago_ppa[i] for i in range(ppa_plazo_minimo)]

    fig_cl = go.Figure()
    fig_cl.add_trace(go.Bar(x=ro["years"], y=pago_cfe, name="Lo que pagaría a CFE",
        marker_color="#374151",
        hovertemplate="<b>Año %{x}</b><br>CFE: $%{y:,.0f} MXN<extra></extra>"))
    fig_cl.add_trace(go.Bar(x=ro["years"], y=pago_ppa, name="Pago PPA",
        marker_color=AMBER, opacity=0.9,
        hovertemplate="<b>Año %{x}</b><br>PPA: $%{y:,.0f} MXN<extra></extra>"))
    fig_cl.add_trace(go.Scatter(x=ro["years"], y=ahorro_y, name="Ahorro anual",
        mode="lines+markers", line=dict(color=TEAL,width=2.5), marker=dict(size=6,color=TEAL),
        hovertemplate="<b>Año %{x}</b><br>Ahorro: $%{y:,.0f} MXN<extra></extra>"))
    lyt_cl = copy.deepcopy(PLOT_LAYOUT)
    lyt_cl.update({"height":310,"barmode":"overlay",
                   "yaxis": dict(title="MXN/año",gridcolor="#2a2d3a",tickformat=","),
                   "xaxis": dict(title="Año",tickmode="linear",dtick=max(1,ppa_plazo_minimo//10)),
                   "legend": dict(orientation="h",y=1.12,x=0.5,xanchor="center",bgcolor="rgba(0,0,0,0)"),
                   "margin": dict(l=20,r=20,t=50,b=40),"hovermode":"x unified"})
    fig_cl.update_layout(**lyt_cl)
    st.plotly_chart(fig_cl, use_container_width=True)

    # KPIs cliente
    ahorro_total = sum(ahorro_y)
    cfe_final    = cfe_y[-1]
    ppa_final    = prec_cl[-1]
    st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:8px;">
  <div class="snap-card">
    <div class="sc-label">Ahorro total cliente</div>
    <div class="sc-val" style="color:#4ade80;">${ahorro_total:,.0f}</div>
    <div class="sc-sub">MXN en {ppa_plazo_minimo} años</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Ahorro año 1</div>
    <div class="sc-val" style="color:#4ade80;">${ahorro_y[0]:,.0f}</div>
    <div class="sc-sub">MXN</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Descuento vs CFE hoy</div>
    <div class="sc-val" style="color:#f59e0b;">{descuento_vs_cfe:+.1f}%</div>
    <div class="sc-sub">precio PPA vs tarifa actual</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">CFE año {ppa_plazo_minimo} (proyectada)</div>
    <div class="sc-val" style="color:#f87171;">${cfe_final:.4f}</div>
    <div class="sc-sub">vs ${ppa_final:.4f} PPA ese año</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Tabla anual detallada — con servicio de deuda desglosado ─────────────
    st.markdown(f'<div class="section-header">Tabla año a año · {ppa_plazo_minimo} años</div>',
                unsafe_allow_html=True)

    # Desglose capital/interés por año (amortización francesa)
    _eq_mxn   = ro.get("equity_mxn", ro.get("inv_mxn", ppa_inversion_usd * usd_to_mxn))
    _inv_mxn  = ro.get("inv_mxn", ppa_inversion_usd * usd_to_mxn)
    _deu_ini  = _inv_mxn - _eq_mxn   # deuda inicial

    interes_y = []
    capital_y = []
    saldo_y   = []
    saldo     = _deu_ini

    for i, y in enumerate(ro["years"]):
        serv = ro["deu_y"][i]
        if serv > 0 and saldo > 0:
            int_y = saldo * (ppa_tasa_deuda / 100)
            cap_y = min(serv - int_y, saldo)
            cap_y = max(cap_y, 0.0)
            saldo = max(saldo - cap_y, 0.0)
        else:
            int_y = 0.0
            cap_y = 0.0
        interes_y.append(int_y)
        capital_y.append(cap_y)
        saldo_y.append(saldo)

    _tiene_deuda = any(d > 0 for d in ro["deu_y"])

    tabla_dict = {
        "Año":                ro["years"],
        "Generación (MWh)":  [f"{g/1000:.2f}" for g in gen_cl],
        "Precio PPA ($/kWh)":[f"${p:.4f}" for p in prec_cl],
        "Ingreso PPA (MXN)": [f"${v:,.0f}" for v in pago_ppa],
        "O&M + Seg. (MXN)":  [f"${ro['om_y'][i]+ro['seg_y'][i]:,.0f}" for i in range(ppa_plazo_minimo)],
    }
    if _tiene_deuda:
        tabla_dict["Interés (MXN)"]  = [f"${v:,.0f}" for v in interes_y]
        tabla_dict["Capital (MXN)"]  = [f"${v:,.0f}" for v in capital_y]
        tabla_dict["Serv. deuda (MXN)"] = [f"${v:,.0f}" for v in ro["deu_y"]]
        tabla_dict["Saldo deuda (MXN)"] = [f"${v:,.0f}" for v in saldo_y]
    tabla_dict["Flujo neto (MXN)"]   = [f"${v:,.0f}" for v in ro["fn_y"]]
    tabla_dict["CFE equiv. ($/kWh)"] = [f"${c:.4f}" for c in cfe_y]
    tabla_dict["Ahorro cliente"]     = [f"${v:,.0f}" for v in ahorro_y]

    st.dataframe(pd.DataFrame(tabla_dict), use_container_width=True, hide_index=True)

    if _tiene_deuda:
        st.caption(
            f"Servicio de deuda: anuidad fija calculada sobre ${_deu_ini:,.0f} MXN "
            f"a {ppa_tasa_deuda:.1f}% anual en {ppa_plazo_deuda} años. "
            f"Interés = saldo × tasa. Capital = servicio - interés. "
            f"Saldo = saldo anterior - capital amortizado."
        )

    # ── Exportar PDF PPA ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Exportar análisis PPA</div>',
                unsafe_allow_html=True)
    pdf_ppa_bytes = build_pdf_ppa(
        proj_loc=proj_loc,
        ppa_kwp=ppa_kwp, ppa_gen_anual=ppa_gen_anual,
        ppa_inversion_usd=ppa_inversion_usd, usd_to_mxn=usd_to_mxn,
        ppa_wacc=ppa_wacc, ppa_inflacion_tarifa=ppa_inflacion_tarifa,
        ppa_degradacion=ppa_degradacion, ppa_om_pct=ppa_om_pct,
        ppa_seguros_pct=ppa_seguros_pct, ppa_tarifa_cliente=ppa_tarifa_cliente,
        ppa_inflacion_cfe=ppa_inflacion_cfe,
        ppa_precio_manual=ppa_precio_manual,
        ppa_plazo_minimo=ppa_plazo_minimo, ppa_plazos=ppa_plazos,
        resultados=resultados, descuento_vs_cfe=descuento_vs_cfe,
        ro=ro,
        ahorro_total=ahorro_total, ahorro_y=ahorro_y,
        cfe_y=cfe_y, pago_ppa=pago_ppa, pago_cfe=pago_cfe,
        pm_obj=pm_obj, viable=viable,
    )
    _ppa_exp1, _ppa_exp2 = st.columns(2)
    with _ppa_exp1:
        st.download_button(
            "📄 Exportar PDF — Análisis PPA",
            data=pdf_ppa_bytes,
            file_name=f"PPA_Solar_{proj_loc[:20].replace(' ','_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    with _ppa_exp2:
        if st.button("📝 Generar Caso de Negocio (.docx)",
                     use_container_width=True, key="btn_word_ppa"):
            with st.spinner("Generando Word…"):
                try:
                    import datetime as _dt
                    _ppa_inv_mxn = ppa_inversion_usd * usd_to_mxn
                    _gen_label   = "P90" if _has_p90 else "P50"
                    _vr_nota     = (
                        f"Gordon generalizado · {max(0, vida_util - ppa_plazo_minimo)} años restantes"
                        if ppa_usar_valor_residual and vida_util > ppa_plazo_minimo
                        else "Excluido del modelo" if not ppa_usar_valor_residual
                        else "Contrato cubre vida útil"
                    )
                    _ppa_co2 = ppa_gen_anual * CO2_FACTOR_KG_KWH / 1000
                    _ppa_hsp = sum(active_irr) / 12
                    _ppa_cache_for_esc = dict(ppa_cache_kwargs)
                    _word_bytes = build_word_ppa(
                        proj_loc=proj_loc, lat=lat, lon=lon,
                        fecha=_dt.date.today().strftime("%B %Y"),
                        kwp=ppa_kwp, n_panels=max(1, round(ppa_kwp * 1000 / panel_wp)),
                        inversion_usd=ppa_inversion_usd,
                        inversion_mxn=_ppa_inv_mxn,
                        usd_to_mxn=usd_to_mxn,
                        ppa_gen_anual=ppa_gen_anual,
                        gen_base_label=_gen_label,
                        hsp_anual=_ppa_hsp,
                        co2_saved_t=_ppa_co2,
                        pr_pct=pr_pct,
                        ppa_degradacion=ppa_degradacion,
                        vida_util=vida_util,
                        ppa_wacc=ppa_wacc,
                        ppa_spread_hurdle=ppa_spread_hurdle,
                        hurdle_label=_hurdle_label,
                        ppa_inflacion_tarifa=ppa_inflacion_tarifa,
                        ppa_inflacion_cfe=ppa_inflacion_cfe,
                        ppa_om_pct=ppa_om_pct,
                        ppa_seguros_pct=ppa_seguros_pct,
                        ppa_financiamiento=ppa_financiamiento,
                        ppa_equity_pct=ppa_equity_pct,
                        ppa_tasa_deuda=ppa_tasa_deuda,
                        ppa_plazo_deuda=ppa_plazo_deuda,
                        ppa_usar_valor_residual=ppa_usar_valor_residual,
                        valor_residual_nota=_vr_nota,
                        ppa_precio_manual=ppa_precio_manual,
                        ppa_tarifa_cliente=ppa_tarifa_cliente,
                        descuento_vs_cfe=descuento_vs_cfe,
                        ppa_plazos=ppa_plazos,
                        ppa_plazo_minimo=ppa_plazo_minimo,
                        resultados=resultados,
                        ahorro_total=ahorro_total,
                        ppa_cache_kwargs=_ppa_cache_for_esc,
                    )
                    st.session_state["word_ppa_bytes"] = _word_bytes
                    st.success("✅ Documento generado")
                except Exception as _e:
                    st.error(f"❌ Error generando Word: {_e}")
        if "word_ppa_bytes" in st.session_state:
            import datetime as _dt3
            st.download_button(
                "⬇️ Descargar Caso de Negocio (.docx)",
                data=st.session_state["word_ppa_bytes"],
                file_name=f"CasoNegocio_PPA_{proj_loc[:20].replace(' ','_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )



# ═════════════════════════════════════════════════════════════════════════════
# PDF — INFORME RECURSO SOLAR 8760h
# ═════════════════════════════════════════════════════════════════════════════

def build_pdf_recurso_solar(
    lat: float, lon: float, proj_loc: str,
    kwp: float, pr_sistema: float, pr_efectivo: float,
    noct: float, gamma: float, year_ref: int,
    irr_arr,        # np.array 8760 W/m²
    temp_arr,       # np.array 8760 °C
    pv_kw,          # np.array 8760 kW
    pv_per_kwp,     # np.array 8760 kW/kWp
    irr_total_kwh: float,
    gen_total_kwh: float,
    gen_per_kwp: float,
    temp_media: float,
    horas_gen: int,
    peak_pv: float,
    factor_cap: float,
    p50_kwh,        # float o None
    p90_kwh,        # float o None
    n_años: int,
    months_irr: list,   # 12 kWh/m²
    months_gen: list,   # 12 MWh
) -> bytes:
    """
    Genera el PDF del informe de Recurso Solar 8760h.
    Secciones: portada KPIs · tabla mensual · gráfica mensual ·
               perfil horario por mes · curva de duración · heatmaps.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as _np

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.8*cm,
    )
    S   = _pdf_styles()
    W   = letter[0] - 3.6*cm
    story = []

    # ── helpers locales ──────────────────────────────────────────────────────
    MONTH_NAMES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    MONTH_DAYS_ = [31,28,31,30,31,30,31,31,30,31,30,31]

    def _fig_to_flowable(fig, width_cm=16.5, dpi=150):
        """Convierte una figura matplotlib a un Flowable PDF."""
        _b = BytesIO()
        fig.savefig(_b, format="png", dpi=dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        _b.seek(0)
        plt.close(fig)
        from reportlab.platypus import Image as RLImage
        w_pt = width_cm * cm
        from PIL import Image as PILImage
        pil = PILImage.open(_b)
        wpx, hpx = pil.size
        h_pt = w_pt * hpx / wpx
        _b.seek(0)
        return RLImage(_b, width=w_pt, height=h_pt)

    def _dark_fig(figsize=(9, 2.8)):
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#13151f")
        for spine in ax.spines.values():
            spine.set_color("#2a2d3a")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        ax.xaxis.label.set_color("#94a3b8")
        ax.yaxis.label.set_color("#94a3b8")
        ax.grid(color="#2a2d3a", linewidth=0.5)
        return fig, ax

    def _dark_fig2(figsize=(9, 2.8)):
        """Dos ejes Y."""
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#13151f")
        for spine in ax.spines.values():
            spine.set_color("#2a2d3a")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        ax.xaxis.label.set_color("#94a3b8")
        ax.yaxis.label.set_color("#94a3b8")
        ax.grid(color="#2a2d3a", linewidth=0.5)
        ax2 = ax.twinx()
        ax2.set_facecolor("#13151f")
        for spine in ax2.spines.values():
            spine.set_color("#2a2d3a")
        ax2.tick_params(colors="#14b8a6", labelsize=8)
        ax2.yaxis.label.set_color("#14b8a6")
        return fig, ax, ax2

    import numpy as _np2
    irr_np   = _np2.array(irr_arr,    dtype=float)
    temp_np  = _np2.array(temp_arr,   dtype=float)
    pv_np    = _np2.array(pv_kw,      dtype=float)
    pvkwp_np = _np2.array(pv_per_kwp, dtype=float)

    # ── PORTADA / ENCABEZADO ─────────────────────────────────────────────────
    story.append(Paragraph("Informe de Recurso Solar", S["title"]))
    story.append(Paragraph(
        f"TMY 8760h &nbsp;·&nbsp; {proj_loc} &nbsp;·&nbsp; ({lat:.4f}, {lon:.4f})",
        S["subtitle"]))
    story.append(_hr())

    # ── KPIs principales ─────────────────────────────────────────────────────
    story.append(Paragraph("RESUMEN DEL SISTEMA", S["section"]))
    kpi_rows = [
        ("Capacidad", f"{kwp:.0f} kWp", "Sistema de referencia"),
        ("Irradiación GHI", f"{irr_total_kwh:,.0f} kWh/m²", "Anual · NASA POWER TMY"),
        ("Generación anual", f"{gen_total_kwh/1000:,.1f} MWh", f"{gen_per_kwp:,.0f} kWh/kWp"),
        ("PR efectivo", f"{pr_efectivo:.1f}%", f"PR sistema {pr_sistema*100:.0f}% + térmico"),
    ]
    story.append(_kpi_table(kpi_rows, S))
    story.append(Spacer(1, 6))
    kpi_rows2 = [
        ("Temp. media anual", f"{temp_media:.1f}°C", "NASA POWER T2M"),
        ("Horas de generación", f"{horas_gen:,} h", "PV > 10 W/año"),
        ("Pico de generación", f"{peak_pv:,.1f} kW", "Hora más soleada"),
        ("Factor de planta", f"{factor_cap:.1f}%", "CF anual"),
    ]
    story.append(_kpi_table(kpi_rows2, S))
    story.append(Spacer(1, 4))

    if p50_kwh is not None:
        kpi_p = [
            ("P50 interanual", f"{p50_kwh/1000:,.1f} MWh", f"Mediana {n_años} años"),
            ("P90 interanual", f"{p90_kwh/1000:,.1f} MWh",
             f"{(p90_kwh/p50_kwh-1)*100:+.1f}% vs P50"),
            ("NOCT panel", f"{noct}°C", "Normal Op. Cell Temp."),
            ("Coef. temp. γ", f"{gamma:.2f}%/°C", "Pérdida por temperatura"),
        ]
        story.append(_kpi_table(kpi_p, S))
        story.append(Spacer(1, 4))

    # ── TABLA MENSUAL ────────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("RESUMEN MENSUAL", S["section"]))
    t_hdr = [Paragraph(h, S["th"]) for h in
              ["Mes", "GHI (kWh/m²)", "Generación (MWh)", "Gen/kWp (kWh)", "T media (°C)"]]
    t_rows = [t_hdr]
    ptr = 0
    for m, days in enumerate(MONTH_DAYS_):
        hrs = days * 24
        sl  = slice(ptr, ptr + hrs)
        gh  = float((irr_np[sl] / 1000).sum())
        gn  = float(pv_np[sl].sum())
        gkwp= float(pvkwp_np[sl].sum())
        tm  = float(temp_np[sl].mean())
        t_rows.append([
            Paragraph(MONTH_NAMES[m], S["td_l"]),
            Paragraph(f"{gh:,.0f}", S["td"]),
            Paragraph(f"{gn/1000:,.2f}", S["td"]),
            Paragraph(f"{gkwp:,.0f}", S["td"]),
            Paragraph(f"{tm:.1f}", S["td"]),
        ])
        ptr += hrs
    # Totales
    t_rows.append([
        Paragraph("TOTAL", S["th"]),
        Paragraph(f"{irr_total_kwh:,.0f}", S["th"]),
        Paragraph(f"{gen_total_kwh/1000:,.2f}", S["th"]),
        Paragraph(f"{gen_per_kwp:,.0f}", S["th"]),
        Paragraph(f"{temp_media:.1f}", S["th"]),
    ])
    col_w = [W*0.12, W*0.22, W*0.22, W*0.22, W*0.22]
    story.append(Table(t_rows, colWidths=col_w, style=_table_style()))
    story.append(Spacer(1, 8))

    # ── GRÁFICA MENSUAL GHI + GENERACIÓN ────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("PERFIL MENSUAL", S["section"]))
    fig, ax, ax2 = _dark_fig2(figsize=(9, 3.2))
    x = _np2.arange(12)
    ax.bar(x, months_irr, color="#f59e0b", alpha=0.85, width=0.5, label="GHI (kWh/m²)")
    ax.set_ylabel("Irradiación GHI (kWh/m²)", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(MONTH_NAMES, fontsize=8)
    ax2.plot(x, months_gen, color="#14b8a6", linewidth=2.2, marker="o",
             markersize=5, label=f"Generación (MWh) · {kwp:.0f} kWp")
    ax2.set_ylabel("Generación (MWh)", fontsize=8, color="#14b8a6")
    ax2.tick_params(axis="y", colors="#14b8a6", labelsize=8)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1+h2, l1+l2, loc="upper right", fontsize=7,
              facecolor="#1a1d27", edgecolor="#2a2d3a", labelcolor="#94a3b8")
    fig.tight_layout(pad=0.6)
    story.append(_fig_to_flowable(fig))
    story.append(Spacer(1, 8))

    # ── PERFIL HORARIO PROMEDIO POR MES ──────────────────────────────────────
    story.append(Paragraph("PERFIL HORARIO DIARIO PROMEDIO (kW/kWp)", S["section"]))
    COLORS_M = ["#f59e0b","#fb923c","#fbbf24","#a3e635","#14b8a6","#3b82f6",
                 "#8b5cf6","#ec4899","#f43f5e","#64748b","#94a3b8","#cbd5e1"]
    fig2, ax3 = _dark_fig(figsize=(9, 3.2))
    ptr = 0
    for m, days in enumerate(MONTH_DAYS_):
        hrs  = days * 24
        vals = pvkwp_np[ptr:ptr+hrs]
        havg = [float(vals[h::24].mean()) for h in range(24)]
        ax3.plot(range(24), havg, color=COLORS_M[m], linewidth=1.5, label=MONTH_NAMES[m])
        ptr += hrs
    ax3.set_xlabel("Hora del día", fontsize=8)
    ax3.set_ylabel("kW/kWp", fontsize=8)
    ax3.set_xticks(range(0, 24, 2))
    ax3.legend(ncol=6, fontsize=6.5, facecolor="#1a1d27",
               edgecolor="#2a2d3a", labelcolor="#94a3b8", loc="upper right")
    fig2.tight_layout(pad=0.6)
    story.append(_fig_to_flowable(fig2))
    story.append(Spacer(1, 8))

    # ── CURVA DE DURACIÓN DE GENERACIÓN ──────────────────────────────────────
    story.append(Paragraph("CURVA DE DURACIÓN DE GENERACIÓN (kW)", S["section"]))
    sorted_pv = _np2.sort(pv_np)[::-1]
    pct_x     = _np2.linspace(0, 100, len(sorted_pv))
    fig3, ax4 = _dark_fig(figsize=(9, 2.8))
    ax4.fill_between(pct_x, sorted_pv, alpha=0.25, color="#f59e0b")
    ax4.plot(pct_x, sorted_pv, color="#f59e0b", linewidth=1.8)
    ax4.set_xlabel("% horas del año ≥ valor", fontsize=8)
    ax4.set_ylabel("Generación (kW)", fontsize=8)
    ax4.set_xlim(0, 100)
    p50_gen = float(_np2.percentile(sorted_pv, 50))
    ax4.axhline(p50_gen, color="#14b8a6", linewidth=1, linestyle="--",
                label=f"Mediana {p50_gen:.1f} kW")
    ax4.legend(fontsize=7.5, facecolor="#1a1d27", edgecolor="#2a2d3a", labelcolor="#94a3b8")
    fig3.tight_layout(pad=0.6)
    story.append(_fig_to_flowable(fig3))
    story.append(Spacer(1, 8))

    # ── HEATMAP GHI 24×365 ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("HEATMAP DE IRRADIANCIA GHI (W/m²) — 24 × 365", S["section"]))
    n_days  = len(irr_np) // 24
    mat_irr = irr_np[:n_days*24].reshape(n_days, 24).T  # 24 × n_days
    fig4, ax5 = plt.subplots(figsize=(9, 3.2))
    fig4.patch.set_facecolor("#0f1117")
    ax5.set_facecolor("#0f1117")
    im = ax5.imshow(mat_irr, aspect="auto", origin="lower",
                    cmap="YlOrRd", interpolation="nearest",
                    extent=[0, n_days, 0, 24])
    cb = fig4.colorbar(im, ax=ax5, pad=0.01)
    cb.ax.tick_params(colors="#94a3b8", labelsize=7)
    cb.set_label("W/m²", color="#94a3b8", fontsize=8)
    ax5.set_xlabel("Día del año", fontsize=8, color="#94a3b8")
    ax5.set_ylabel("Hora del día", fontsize=8, color="#94a3b8")
    ax5.tick_params(colors="#94a3b8", labelsize=7)
    for sp in ax5.spines.values(): sp.set_color("#2a2d3a")
    fig4.tight_layout(pad=0.5)
    story.append(_fig_to_flowable(fig4))
    story.append(Spacer(1, 8))

    # ── HEATMAP GENERACIÓN PV 24×365 ────────────────────────────────────────
    story.append(Paragraph(f"HEATMAP DE GENERACIÓN PV (kW) — {kwp:.0f} kWp", S["section"]))
    mat_pv = pv_np[:n_days*24].reshape(n_days, 24).T
    fig5, ax6 = plt.subplots(figsize=(9, 3.2))
    fig5.patch.set_facecolor("#0f1117")
    ax6.set_facecolor("#0f1117")
    im2 = ax6.imshow(mat_pv, aspect="auto", origin="lower",
                     cmap="YlOrBr", interpolation="nearest",
                     extent=[0, n_days, 0, 24])
    cb2 = fig5.colorbar(im2, ax=ax6, pad=0.01)
    cb2.ax.tick_params(colors="#94a3b8", labelsize=7)
    cb2.set_label("kW", color="#94a3b8", fontsize=8)
    ax6.set_xlabel("Día del año", fontsize=8, color="#94a3b8")
    ax6.set_ylabel("Hora del día", fontsize=8, color="#94a3b8")
    ax6.tick_params(colors="#94a3b8", labelsize=7)
    for sp in ax6.spines.values(): sp.set_color("#2a2d3a")
    fig5.tight_layout(pad=0.5)
    story.append(_fig_to_flowable(fig5))
    story.append(Spacer(1, 8))

    # ── NOTA METODOLÓGICA ────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("METODOLOGÍA", S["section"]))
    nota = (
        f"TMY construido con irradiancia horaria NASA POWER (API temporal/hourly) "
        f"para el año de referencia {year_ref}, escalada mes a mes al promedio "
        f"climatológico {NASA_START}–{NASA_END} (20 años). "
        f"Temperatura de celda: modelo NOCT IEC 61724 "
        f"(T_cell = T_amb + (NOCT−20)/800 × G). "
        f"Corrección de potencia: factor = 1 + γ × (T_cell − 25°C). "
        f"El PR de sistema ({pr_sistema*100:.0f}%) incluye pérdidas de inversor, "
        f"cableado y mismatch; la corrección térmica se aplica adicionalmente, "
        f"resultando en un PR efectivo anual de {pr_efectivo:.1f}%. "
        f"Fuente: NASA POWER · Sizing Tool — solo para uso interno."
    )
    story.append(Paragraph(nota, S["note"]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════════════════
# TAB — RECURSO SOLAR 8760h
# Descarga el TMY horario de NASA POWER y genera el atlas solar del sitio:
# GHI, temperatura, generación PV/kWp, heatmap, curva de duración, P50/P90
# interanual, CSV descargable para PVSyst / SAM / Excel.
# ═════════════════════════════════════════════════════════════════════════════

with tab_sol:

    st.markdown("""
<div class="info-box">
  🌞 <b>Recurso Solar 8760h</b> — Descarga el perfil horario completo (TMY) del sitio
  usando las coordenadas del sidebar y la API de NASA POWER (2005–2024).
  Obtén GHI, temperatura, generación PV por kWp, heatmap 24×365, curva de
  duración, estadísticas de variabilidad interanual (P50/P90) y el CSV listo
  para PVSyst, SAM o cualquier herramienta de ingeniería.
</div>
""", unsafe_allow_html=True)

    # ── Parámetros del sistema para la simulación PV ─────────────────────────
    sol_c1, sol_c2 = st.columns([1, 2], gap="large")

    with sol_c1:
        st.markdown('<div class="section-header">Parámetros de simulación PV</div>', unsafe_allow_html=True)
        sol_kwp = st.number_input(
            "Capacidad de referencia (kWp)",
            min_value=1.0, max_value=100000.0, value=100.0, step=1.0,
            key="sol_kwp",
            help="kWp de referencia para escalar la generación. El CSV incluye kW/kWp para que puedas escalar a cualquier tamaño."
        )
        sol_pr = st.slider(
            "PR de sistema (no térmico)", 0.60, 0.95, 0.87, 0.01,
            key="sol_pr",
            help="Pérdidas no térmicas: inversor ~2%, cableado ~1.5%, mismatch ~1.5%, "
                 "soiling ~3%, disponibilidad ~1%, sombras ~1% → PR típico México 0.84–0.90. "
                 "Default 0.87 (instalación comercial/industrial, zona semicálida). "
                 "La corrección térmica (NOCT + γ) se aplica hora a hora adicionalmente."
        )
        sol_noct = st.number_input(
            "NOCT del panel (°C)", 30.0, 55.0, 44.0, 0.5,
            key="sol_noct",
            help="Normal Operating Cell Temperature. Típico LFP/Si: 43-46°C."
        )
        sol_gamma = st.number_input(
            "Coef. temperatura Pmax (%/°C)", -0.50, -0.20, -0.35, 0.01,
            key="sol_gamma",
            help="Coeficiente de temperatura de la potencia máxima (γ). Típico mono-Si: -0.35%/°C."
        )

        sol_year = st.selectbox(
            "Año de referencia para TMY",
            list(range(2001, 2025)),
            index=list(range(2001, 2025)).index(2023),
            key="sol_year_ref",
            help="Año usado para la estructura horaria (DOY, día de la semana). La irradiancia se reemplaza por la media climatológica 2005–2024."
        )

        st.markdown('<div class="section-header">Coordenadas activas</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="panel-card">
  <div class="pc-grid">
    <div class="pc-item"><span class="pc-label">Latitud</span>
      <span class="pc-val">{lat:.4f}°</span></div>
    <div class="pc-item"><span class="pc-label">Longitud</span>
      <span class="pc-val">{lon:.4f}°</span></div>
  </div>
  <div style="margin-top:8px;font-size:11px;color:#475569;">
    Modifica las coordenadas en el sidebar y haz clic en el botón de NASA POWER
    para actualizar la irradiancia mensual antes de generar el TMY.
  </div>
</div>
""", unsafe_allow_html=True)

        sol_btn = st.button(
            "🌍 Generar TMY 8760h desde NASA POWER",
            type="primary", use_container_width=True, key="sol_run"
        )

    with sol_c2:

        if not sol_btn and "sol_tmy_df" not in st.session_state:
            st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            min-height:340px;border:1px dashed #1e2230;border-radius:14px;
            color:#475569;font-size:13px;text-align:center;gap:12px;">
  <div style="font-size:32px;">☀️</div>
  <div><b>Define los parámetros y pulsa el botón</b><br>
  para descargar el TMY horario del sitio.</div>
  <div style="font-size:11px;color:#374151;">
    La descarga tarda ~15–30 segundos · NASA POWER API hourly
  </div>
</div>
""", unsafe_allow_html=True)

        if sol_btn:
            with st.spinner("🌍 Descargando datos horarios de NASA POWER… (15–30 s)"):
                _tmy_df, _tmy_err = build_tmy_8760(
                    lat, lon,
                    irr_media_mensual=tuple(active_irr),
                    year_ref=sol_year,
                )
            if _tmy_df is None:
                st.error(f"❌ No se pudo construir el TMY: {_tmy_err}")
            else:
                if _tmy_err:
                    st.caption(f"ℹ️ {_tmy_err}")
                st.session_state["sol_tmy_df"]  = _tmy_df
                st.session_state["sol_kwp_ref"] = sol_kwp
                st.session_state["sol_pr_ref"]  = sol_pr
                st.session_state["sol_noct_ref"]= sol_noct
                st.session_state["sol_gam_ref"] = sol_gamma
                st.success("✅ TMY generado correctamente.")

        # ── KPI hero dentro de sol_c2 — llena el hueco junto al sidebar ──────
        if "sol_tmy_df" in st.session_state:
            _tmy_c2  = st.session_state["sol_tmy_df"]
            _kwp_c2  = sol_kwp
            _pr_c2   = sol_pr
            _noct_c2 = sol_noct
            _gam_c2  = sol_gamma
            _ia_c2   = _tmy_c2["irradiance_Wm2"].values[:8760]
            _ta_c2   = _tmy_c2["temp_C"].values[:8760]
            _tc_c2   = _ta_c2 + ((_noct_c2 - 20.0) / 800.0) * _ia_c2
            _tf_c2   = (1.0 + (_gam_c2 / 100.0) * (_tc_c2 - 25.0)).clip(min=0.0)
            _pk_c2   = (_ia_c2 / 1000.0) * _pr_c2 * _tf_c2 * _kwp_c2
            _irr_c2  = float((_ia_c2 / 1000.0).sum())
            _gen_c2  = float(_pk_c2.sum())
            _gkp_c2  = float(((_ia_c2 / 1000.0) * _pr_c2 * _tf_c2).sum())
            _pre_c2  = _gkp_c2 / max(_irr_c2, 1) * 100
            _tm_c2   = float(_ta_c2.mean())
            _hg_c2   = int((_pk_c2 > 0.01).sum())
            _pp_c2   = float(_pk_c2.max())
            _fc_c2   = _gen_c2 / (_kwp_c2 * 8760) * 100
            st.markdown(f"""
<div class="tor-hero" style="margin-top:0;">
  <div class="th-project">🌞 RECURSO SOLAR — TMY 8760h · ({lat:.4f}, {lon:.4f})</div>
  <div class="th-meta">NASA POWER {NASA_START}–{NASA_END} · Año ref {sol_year} ·
    PR sistema {_pr_c2*100:.0f}% · PR efectivo {_pre_c2:.1f}% · NOCT {_noct_c2}°C · γ {_gam_c2:.2f}%/°C · {_kwp_c2:.0f} kWp
  </div>
  <div class="th-grid" style="grid-template-columns:repeat(2,1fr);gap:12px 16px;">
    <div class="th-item">
      <span class="th-label">IRRADIACIÓN ANUAL</span>
      <span class="th-val">{_irr_c2:,.0f}</span>
      <span class="th-unit">kWh/m²/año · GHI</span>
    </div>
    <div class="th-item">
      <span class="th-label">GENERACIÓN ANUAL</span>
      <span class="th-val">{_gen_c2/1000:,.1f}</span>
      <span class="th-unit">MWh/año · {_kwp_c2:.0f} kWp</span>
    </div>
    <div class="th-item">
      <span class="th-label">GEN. ESPECÍFICA</span>
      <span class="th-val">{_gkp_c2:,.0f}</span>
      <span class="th-unit">kWh/kWp/año</span>
    </div>
    <div class="th-item">
      <span class="th-label">PR EFECTIVO</span>
      <span class="th-val">{_pre_c2:.1f}</span>
      <span class="th-unit">% real · sistema + térmico</span>
    </div>
    <div class="th-item">
      <span class="th-label">TEMP. MEDIA ANUAL</span>
      <span class="th-val">{_tm_c2:.1f}</span>
      <span class="th-unit">°C · NASA POWER T2M</span>
    </div>
    <div class="th-item">
      <span class="th-label">HORAS DE GENERACIÓN</span>
      <span class="th-val">{_hg_c2:,}</span>
      <span class="th-unit">h/año con PV > 10 W</span>
    </div>
    <div class="th-item">
      <span class="th-label">PICO DE GENERACIÓN</span>
      <span class="th-val">{_pp_c2:,.1f}</span>
      <span class="th-unit">kW · hora más soleada</span>
    </div>
    <div class="th-item">
      <span class="th-label">FACTOR DE PLANTA</span>
      <span class="th-val">{_fc_c2:.1f}</span>
      <span class="th-unit">% capacidad · (CF)</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Resultados — ancho completo de la pantalla ────────────────────────────
    if "sol_tmy_df" in st.session_state:
        _tmy   = st.session_state["sol_tmy_df"]
        _kwp   = sol_kwp
        _pr    = sol_pr
        _noct  = sol_noct
        _gamma = sol_gamma
        _irr_arr  = _tmy["irradiance_Wm2"].values[:8760]
        _temp_arr = _tmy["temp_C"].values[:8760]
        _t_cell = _temp_arr + ((_noct - 20.0) / 800.0) * _irr_arr
        _temp_factor = (1.0 + (_gamma / 100.0) * (_t_cell - 25.0)).clip(min=0.0)
        _pv_per_kwp = (_irr_arr / 1000.0) * _pr * _temp_factor
        _pv_kw      = _pv_per_kwp * _kwp
        _irr_total_kwh = float((_irr_arr / 1000.0).sum())
        _gen_total_kwh = float(_pv_kw.sum())
        _gen_per_kwp   = float(_pv_per_kwp.sum())
        _pr_efectivo   = _gen_per_kwp / max(_irr_total_kwh, 1) * 100
        _temp_media    = float(_temp_arr.mean())
        _peak_pv       = float(_pv_kw.max())
        _horas_gen     = int((_pv_kw > 0.01).sum())
        _factor_cap    = _gen_total_kwh / (_kwp * 8760) * 100

        # ── Calcular datos mensuales y horarios (necesarios para PDF) ─────
        _months_irr = []
        _months_gen = []
        _ptr = 0
        for m_idx, days in enumerate(MONTH_DAYS):
            hrs = days * 24
            _months_irr.append(float((_irr_arr[_ptr:_ptr+hrs] / 1000.0).sum()))
            _months_gen.append(float(_pv_kw[_ptr:_ptr+hrs].sum()) / 1000.0)
            _ptr += hrs

        _colors_month = [
            AMBER, "#fb923c", "#fbbf24", "#a3e635", TEAL, BLUE,
            VIOLET, "#ec4899", ROSE, "#64748b", "#94a3b8", "#cbd5e1"
        ]

        # ── Fila 1: Heatmap GHI | Heatmap PV ─────────────────────────────
        _hc1, _hc2 = st.columns(2, gap="medium")
        with _hc1:
            st.markdown('<div class="section-header">Heatmap irradiancia GHI (W/m²)</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                build_heatmap_fig(list(_irr_arr), "GHI", "W/m²", "YlOrRd"),
                use_container_width=True
            )
        with _hc2:
            st.markdown('<div class="section-header">Heatmap generación PV (kW)</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                build_heatmap_fig(list(_pv_kw), "Gen. PV", "kW", "YlOrBr"),
                use_container_width=True
            )

        # ── Fila 2: Mensual GHI+Gen | Perfil horario por mes ─────────────
        _mc1, _mc2 = st.columns(2, gap="medium")
        with _mc1:
            st.markdown('<div class="section-header">Perfil mensual — GHI y generación</div>',
                        unsafe_allow_html=True)
            _fig_mes = go.Figure()
            _fig_mes.add_trace(go.Bar(
                x=MONTHS, y=_months_irr,
                name="Irradiación GHI (kWh/m²)",
                marker_color=AMBER, opacity=0.85,
                yaxis="y",
                hovertemplate="<b>%{x}</b><br>GHI: %{y:,.0f} kWh/m²<extra></extra>",
            ))
            _fig_mes.add_trace(go.Scatter(
                x=MONTHS, y=_months_gen,
                name=f"Generación (MWh) · {_kwp:.0f} kWp",
                mode="lines+markers",
                line=dict(color=TEAL, width=2.5),
                marker=dict(size=7, color=TEAL),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>Gen: %{y:,.1f} MWh<extra></extra>",
            ))
            _lay_mes = copy.deepcopy(PLOT_LAYOUT)
            _lay_mes.update({
                "height": 300,
                "barmode": "group",
                "yaxis":  dict(title="GHI (kWh/m²)", gridcolor="#1e2230"),
                "yaxis2": dict(title="Generación (MWh)", overlaying="y", side="right",
                               showgrid=False, tickfont=dict(color=TEAL)),
                "legend": dict(orientation="h", y=1.12, x=0.5, xanchor="center",
                               bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
                "margin": dict(l=20, r=60, t=40, b=40),
            })
            _fig_mes.update_layout(**_lay_mes)
            st.plotly_chart(_fig_mes, use_container_width=True)

        with _mc2:
            st.markdown('<div class="section-header">Perfil horario diario promedio (kW/kWp)</div>',
                        unsafe_allow_html=True)
            _pv_per_kwp_arr = _pv_per_kwp
            _fig_horal = go.Figure()
            _ptr = 0
            for m_idx, days in enumerate(MONTH_DAYS):
                hrs = days * 24
                _mes_vals = _pv_per_kwp_arr[_ptr:_ptr+hrs]
                _hourly_avg = [float(_mes_vals[h::24].mean()) for h in range(24)]
                _fig_horal.add_trace(go.Scatter(
                    x=list(range(24)), y=_hourly_avg,
                    name=MONTHS[m_idx], mode="lines",
                    line=dict(color=_colors_month[m_idx], width=1.8),
                    hovertemplate=f"<b>{MONTHS[m_idx]}</b> · Hora %{{x}}h<br>kW/kWp: %{{y:.3f}}<extra></extra>",
                ))
                _ptr += hrs
            _lay_hr = copy.deepcopy(PLOT_LAYOUT)
            _lay_hr.update({
                "height": 300,
                "xaxis": dict(title="Hora del día", gridcolor="#1e2230",
                              tickmode="linear", dtick=2),
                "yaxis": dict(title="kW/kWp", gridcolor="#1e2230"),
                "legend": dict(orientation="h", y=1.14, x=0.5, xanchor="center",
                               bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
                "margin": dict(l=20, r=20, t=50, b=40),
            })
            _fig_horal.update_layout(**_lay_hr)
            st.plotly_chart(_fig_horal, use_container_width=True)

        # ── Fila 3: Curva de duración | P50/P90 ──────────────────────────
        _dc1, _dc2 = st.columns(2, gap="medium")
        with _dc1:
            st.markdown('<div class="section-header">Curva de duración de generación (kW)</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                duration_curve_fig(list(_pv_kw), f"Generación PV · {_kwp:.0f} kWp", AMBER),
                use_container_width=True
            )

        with _dc2:
            if active_irr_por_anio:
                st.markdown('<div class="section-header">Variabilidad interanual P50 / P90</div>',
                            unsafe_allow_html=True)
                p50_r, p90_r, gen_yr = compute_p90(active_irr_por_anio, _kwp, _pr)
                if p50_r is not None:
                    _anios_v = sorted(gen_yr.keys())
                    _gen_v   = [gen_yr[a] / 1000 for a in _anios_v]
                    _p50_mwh = p50_r / 1000
                    _p90_mwh = p90_r / 1000
                    _bar_col = [ROSE if v < _p90_mwh else AMBER if v < _p50_mwh else TEAL
                                for v in _gen_v]
                    _fig_p90 = go.Figure()
                    _fig_p90.add_trace(go.Bar(
                        x=_anios_v, y=_gen_v,
                        marker=dict(color=_bar_col, cornerradius=4),
                        hovertemplate="<b>%{x}</b><br>%{y:,.1f} MWh<extra></extra>",
                    ))
                    _fig_p90.add_hline(y=_p50_mwh, line_color=AMBER, line_dash="dash",
                                       line_width=1.8,
                                       annotation_text=f"P50 {_p50_mwh:,.1f} MWh",
                                       annotation_font=dict(color=AMBER, size=10))
                    _fig_p90.add_hline(y=_p90_mwh, line_color=ROSE, line_dash="dot",
                                       line_width=1.8,
                                       annotation_text=f"P90 {_p90_mwh:,.1f} MWh",
                                       annotation_font=dict(color=ROSE, size=10),
                                       annotation_position="bottom right")
                    _lay_p9 = copy.deepcopy(PLOT_LAYOUT)
                    _lay_p9.update({
                        "height": 300,
                        "yaxis": dict(title="MWh/año", gridcolor="#1e2230"),
                        "xaxis": dict(tickmode="linear", dtick=1, tickangle=-45,
                                      gridcolor="rgba(0,0,0,0)"),
                        "bargap": 0.25,
                        "margin": dict(l=20, r=20, t=20, b=60),
                    })
                    _fig_p90.update_layout(**_lay_p9)
                    st.plotly_chart(_fig_p90, use_container_width=True)
                    _vp1, _vp2, _vp3, _vp4 = st.columns(4)
                    _vp1.metric("P50", f"{_p50_mwh:,.1f} MWh")
                    _vp2.metric("P90", f"{_p90_mwh:,.1f} MWh",
                                f"{(_p90_mwh/_p50_mwh-1)*100:+.1f}% vs P50")
                    _vp3.metric("Mejor año", f"{max(_gen_v):,.1f} MWh")
                    _vp4.metric("Peor año",  f"{min(_gen_v):,.1f} MWh")
            else:
                st.markdown(
                    '<div class="info-box" style="margin-top:2rem;">Carga datos NASA POWER '
                    'desde el sidebar para calcular la variabilidad interanual P50/P90 '
                    'con los 20 años históricos.</div>',
                    unsafe_allow_html=True
                )
                p50_r = p90_r = None

        # ── Fila 4: Export CSV | Export PDF (side by side) ────────────────
        st.markdown('<div class="section-header">Exportar</div>', unsafe_allow_html=True)
        _ec1, _ec2 = st.columns(2, gap="medium")

        with _ec1:
            _df_export = pd.DataFrame({
                "hora_del_año":          list(range(1, 8761)),
                "datetime_TMY":          _tmy["datetime"].values[:8760],
                "GHI_Wm2":               [round(float(v), 2) for v in _irr_arr],
                "temp_amb_C":            [round(float(v), 2) for v in _temp_arr],
                "temp_celula_C":         [round(float(v), 2) for v in _t_cell],
                "factor_temp":           [round(float(v), 5) for v in _temp_factor],
                "gen_kW_por_kWp":        [round(float(v), 5) for v in _pv_per_kwp],
                f"gen_kW_{_kwp:.0f}kWp": [round(float(v), 3) for v in _pv_kw],
            })
            _csv_bytes = _df_export.to_csv(index=False).encode("utf-8")
            _fname_csv = f"Recurso_Solar_8760h_{lat:.4f}_{lon:.4f}_{_kwp:.0f}kWp.csv"
            st.markdown(f"""
<div class="info-box" style="font-size:11px;">
      📊 CSV 8760h · {_kwp:.0f} kWp · <code>gen_kW_por_kWp</code> escalable a cualquier tamaño.<br>
      PR sistema {_pr*100:.0f}% · corrección térmica NOCT {_noct}°C · γ {_gamma:.2f}%/°C incluida.
</div>
""", unsafe_allow_html=True)
            st.download_button(
                f"⬇️ Descargar CSV 8760h — {_kwp:.0f} kWp",
                data=_csv_bytes,
                file_name=_fname_csv,
                mime="text/csv",
                use_container_width=True,
                type="primary",
            )

        with _ec2:
            _p50_val = p50_r if p50_r is not None else None
            _p90_val = p90_r if p90_r is not None else None
            _n_años  = len(active_irr_por_anio) if active_irr_por_anio else 0
            st.markdown(f"""
<div class="info-box" style="font-size:11px;">
      📄 PDF técnico · portada KPIs · tabla mensual · gráficas · heatmaps · metodología.<br>
      PR sistema {_pr*100:.0f}% · PR efectivo {_pr_efectivo:.1f}% · NASA POWER {NASA_START}–{NASA_END}.
</div>
""", unsafe_allow_html=True)
            if st.button("📄 Generar PDF — Informe Recurso Solar 8760h",
                         use_container_width=True, type="primary",
                         key="btn_pdf_recurso"):
                with st.spinner("Generando PDF… (10–20 s)"):
                    try:
                        _pdf_bytes = build_pdf_recurso_solar(
                            lat=lat, lon=lon, proj_loc=proj_loc,
                            kwp=_kwp, pr_sistema=_pr, pr_efectivo=_pr_efectivo,
                            noct=_noct, gamma=_gamma, year_ref=sol_year,
                            irr_arr=_irr_arr, temp_arr=_temp_arr,
                            pv_kw=_pv_kw, pv_per_kwp=_pv_per_kwp,
                            irr_total_kwh=_irr_total_kwh,
                            gen_total_kwh=_gen_total_kwh,
                            gen_per_kwp=_gen_per_kwp,
                            temp_media=_temp_media,
                            horas_gen=_horas_gen,
                            peak_pv=_peak_pv,
                            factor_cap=_factor_cap,
                            p50_kwh=_p50_val,
                            p90_kwh=_p90_val,
                            n_años=_n_años,
                            months_irr=_months_irr,
                            months_gen=_months_gen,
                        )
                        st.session_state["pdf_recurso_bytes"] = _pdf_bytes
                        st.success("✅ PDF generado.")
                    except Exception as _e:
                        st.error(f"❌ Error al generar PDF: {str(_e)[:200]}")

            if "pdf_recurso_bytes" in st.session_state:
                _fname_pdf = f"Recurso_Solar_{lat:.4f}_{lon:.4f}_{_kwp:.0f}kWp.pdf"
                st.download_button(
                    "⬇️ Descargar PDF — Informe Recurso Solar",
                    data=st.session_state["pdf_recurso_bytes"],
                    file_name=_fname_pdf,
                    mime="application/pdf",
                    use_container_width=True,
                )

