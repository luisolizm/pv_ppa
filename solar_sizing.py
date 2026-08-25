import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import copy
import requests
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors as rl_color
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
    background: #1e2028; border: 1px solid #2e3138; border-radius: 16px;
  }
  .login-title { font-size: 22px; font-weight: 700; color: #f1f5f9;
                 margin-bottom: 4px; text-align: center; }
  .login-sub   { font-size: 13px; color: #94a3b8; text-align: center;
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

  /* NOTA — no incluir `span` ni `div` en este selector.
     Los iconos de Streamlit son ligatures de Material Symbols: el <span> lleva
     el texto "arrow_right" y la fuente lo convierte en flecha. Al forzar Inter
     con !important sobre todos los span, la fuente de iconos quedaba anulada y
     el nombre del icono se dibujaba como TEXTO encima del titulo del expander.
     Con html/body basta: la tipografia se hereda igual. */
  html, body, [class*="css"], button, label, p,
  .stMarkdown, .stTextInput, .stNumberInput, .stSlider, .stRadio, .stCheckbox {
    font-family: 'Inter', sans-serif !important;
  }

  /* ── Fondo global oscuro ── */
  [data-testid="stAppViewContainer"] { background: #17191f; }
  .main { background: #17191f; }
  [data-testid="stSidebar"] {
    background: #1a1c23 !important;
    border-right: 1px solid #2e3138 !important;
  }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }

  /* ── Ocultar iconos de colapso del sidebar ──
     Acotado a los controles del sidebar: la regla global tambien alcanzaba la
     flecha de los expander y su ligature "arrow_down" se dibujaba como texto
     encima del titulo. */
  [data-testid="collapsedControl"] span.material-symbols-rounded,
  [data-testid="collapsedControl"] span.material-symbols-outlined,
  [data-testid="stSidebarCollapseButton"] span.material-symbols-rounded,
  [data-testid="stSidebarCollapseButton"] span.material-symbols-outlined {
    font-size:0!important; visibility:hidden!important;
    width:0!important; height:0!important;
  }

  /* ── Tipografia monoespaciada ── */
  .mono { font-family: 'JetBrains Mono', monospace !important; }

  /* ── Cabecera ── */
  .app-title { font-size:28px; font-weight:700; color:#f1f5f9; letter-spacing:-0.6px; }
  .app-sub   { font-size:13px; color:#cbd5e1; margin-top:-4px; margin-bottom:1.5rem; }

  /* ── Section header ── */
  .section-header {
    font-size:12px; font-weight:600; color:#cbd5e1;
    text-transform:uppercase; letter-spacing:0.10em;
    margin:1.6rem 0 0.8rem; padding-bottom:6px;
    border-bottom:1px solid #2e3138;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] { background:#1e2028; border-radius:10px; padding:4px; gap:4px; }
  .stTabs [data-baseweb="tab"]      { background:transparent; border-radius:8px; color:#cbd5e1; font-weight:500; font-size:14px; }
  .stTabs [aria-selected="true"]    { background:#f59e0b !important; color:#17191f !important; font-weight:600 !important; }

  /* ── Cajas informativas ── */
  .info-box { background:#1e2028; border-left:3px solid #f59e0b; border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#94a3b8; margin-bottom:1rem; }
  .nasa-box { background:#0b1623; border-left:3px solid #3b82f6; border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#93c5fd; margin-bottom:1rem; }
  .warn-box { background:#1e2028; border-left:3px solid #f43f5e; border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#94a3b8; margin-bottom:1rem; }

  /* ── TOR Hero ── */
  .tor-hero {
    background: #1e2028;
    border:1px solid #2e3138; border-radius:14px;
    padding:20px 24px; margin-bottom:1.4rem;
  }
  .tor-hero .th-project { font-size:11px; color:#cbd5e1; text-transform:uppercase; letter-spacing:0.10em; margin-bottom:4px; }
  .tor-hero .th-meta    { font-size:12.5px; color:#cbd5e1; margin-bottom:16px; }
  .tor-hero .th-grid    { display:grid; grid-template-columns:repeat(4,1fr); gap:14px 20px; }
  .tor-hero .th-item    { display:flex; flex-direction:column; }
  .tor-hero .th-label   { font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:3px; }
  .tor-hero .th-val     { font-size:20px; font-weight:700; color:#f59e0b; font-family:'JetBrains Mono',monospace; line-height:1.1; word-break:break-word; }
  .tor-hero .th-unit    { font-size:11px; color:#94a3b8; margin-top:3px; }

  /* ── Badges PR ── */
  .pr-badge  { display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:500; }
  .pr-green  { background:#052e16; color:#4ade80; border:1px solid #166534; }
  .pr-yellow { background:#1c1a04; color:#facc15; border:1px solid #713f12; }
  .pr-red    { background:#1f0a0a; color:#f87171; border:1px solid #7f1d1d; }

  /* ── Panel card ── */
  .panel-card           { background:#1e2028; border:1px solid #2e3138; border-radius:12px; padding:14px 18px; margin-bottom:1rem; }
  .panel-card .pc-title { font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:10px; }
  .panel-card .pc-grid  { display:grid; grid-template-columns:1fr 1fr; gap:6px 16px; }
  .panel-card .pc-item  { display:flex; flex-direction:column; }
  .panel-card .pc-label { font-size:10px; color:#94a3b8; }
  .panel-card .pc-val   { font-size:14px; font-weight:600; color:#f59e0b; font-family:'JetBrains Mono',monospace; }

  /* ── Snap cards KPI ── */
  .snap-card {
    background:#1e2028; border:1px solid #2e3138; border-radius:12px;
    padding:16px 12px; text-align:center;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    min-height:110px;
  }
  .snap-card .sc-label { font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; line-height:1.3; }
  .snap-card .sc-val   { font-size:clamp(14px,1.4vw,22px); font-weight:700; font-family:'JetBrains Mono',monospace; word-break:break-word; overflow-wrap:anywhere; line-height:1.2; max-width:100%; color:#e2e8f0; }
  .snap-card .sc-sub   { font-size:10px; color:#94a3b8; margin-top:4px; line-height:1.3; }

  /* ── st.metric ── */
  [data-testid="stMetric"] { background:#1e2028; border:1px solid #2e3138; border-radius:12px; padding:14px 12px !important; text-align:center; }
  [data-testid="stMetricValue"] { font-family:'JetBrains Mono',monospace !important; font-size:clamp(13px,1.3vw,20px) !important; font-weight:700 !important; word-break:break-word !important; overflow-wrap:anywhere !important; white-space:normal !important; line-height:1.2 !important; color:#e2e8f0 !important; }
  [data-testid="stMetricLabel"] { font-family:'Inter',sans-serif !important; font-size:11px !important; color:#94a3b8 !important; text-transform:uppercase; letter-spacing:0.06em; }

  /* ── Sidebar inputs ── */
  [data-testid="stSidebar"] input[type="number"],
  [data-testid="stSidebar"] input[type="text"],
  [data-testid="stSidebar"] .stTextInput input,
  [data-testid="stSidebar"] .stNumberInput input {
    background-color:#17191f !important; color:#e2e8f0 !important;
    border:1px solid #2d3748 !important; border-radius:6px !important;
  }
  [data-testid="stSidebar"] input:focus { border-color:#f59e0b !important; box-shadow:0 0 0 2px rgba(245,158,11,0.2) !important; outline:none !important; }
  [data-testid="stSidebar"] [data-baseweb="input"],
  [data-testid="stSidebar"] [data-baseweb="base-input"] { background-color:#17191f !important; }
  [data-testid="stSidebar"] [data-baseweb="input"] input,
  [data-testid="stSidebar"] [data-baseweb="base-input"] input { color:#e2e8f0 !important; background-color:#17191f !important; caret-color:#f59e0b !important; }
  [data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"],
  [data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"] { background-color:#1e2028 !important; color:#e2e8f0 !important; border-color:#2d3748 !important; }
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background-color:#17191f !important; border-color:#2d3748 !important; color:#e2e8f0 !important; }
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

# Límite de capacidad para Generación Distribuida en México.
# El umbral aplica a la capacidad de INTERCONEXIÓN (potencia AC del inversor),
# no a la potencia pico DC del generador. Por encima de este valor el proyecto
# requiere permiso CRE y deja de calificar para el contrato de interconexión
# simplificado. VERIFICAR contra la resolución CRE vigente antes de usarlo como
# criterio de diseño: es un parámetro regulatorio, no técnico.
LIMITE_GD_KW_AC = 500.0   # kW AC  (0.5 MW)

# Holgura del área de instalación sobre la superficie neta de módulos.
# La superficie de paneles (n × largo × ancho) NO es el área que ocupa la
# instalación: hay separación entre filas para evitar sombreado mutuo, pasillos
# de mantenimiento y acceso, y separación al perímetro. Un 35 % es la holgura
# típica de un arreglo coplanar sobre cubierta. Para arreglos inclinados sobre
# losa el factor real es mayor (GCR de 0.4–0.5 implica 100–150 % de holgura),
# así que este valor es el piso, no el techo.
HOLGURA_INSTALACION_PCT = 35.0


PLOT_LAYOUT = dict(
    paper_bgcolor="#1e2028", plot_bgcolor="#1e2028",
    font=dict(family="Inter, sans-serif", color="#cbd5e1", size=12),
    xaxis=dict(gridcolor="#343841", linecolor="#343841", tickcolor="#343841"),
    yaxis=dict(gridcolor="#343841", linecolor="#343841", tickcolor="#343841"),
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


def _mirr(cash_flows: list, finance_rate: float, reinvest_rate: float) -> float | None:
    """
    TIR modificada (MIRR). Única por construcción, a diferencia de la TIR clásica.
      MIRR = (VF(flujos positivos) / -VP(flujos negativos))^(1/n) - 1
    finance_rate : tasa a la que se financian los flujos negativos.
    reinvest_rate: tasa a la que se reinvierten los flujos positivos.
    Retorna % anual, o None si no es calculable.
    """
    n = len(cash_flows) - 1
    if n <= 0:
        return None
    vp_neg = sum(c / (1 + finance_rate) ** t
                 for t, c in enumerate(cash_flows) if c < 0)
    vf_pos = sum(c * (1 + reinvest_rate) ** (n - t)
                 for t, c in enumerate(cash_flows) if c > 0)
    if vp_neg >= 0 or vf_pos <= 0:
        return None
    try:
        return ((vf_pos / -vp_neg) ** (1 / n) - 1) * 100
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def _irr_robusta(cash_flows: list, finance_rate: float,
                 reinvest_rate: float) -> tuple[float | None, str]:
    """
    TIR con verificación de unicidad (regla de signos de Descartes).

    Una serie con un solo cambio de signo tiene TIR única y la bisección es
    válida. Con dos o más cambios de signo —lo que ocurre en cuanto se agrega
    el reemplazo de inversor o el servicio de deuda supera el ingreso en los
    primeros años— pueden existir múltiples raíces y la bisección devolvería
    una arbitraria. En ese caso se reporta MIRR, que sí es única.

    Devuelve (valor_%, metodo) donde metodo ∈ {"TIR", "MIRR", "—"}.
    """
    signos = [1 if c > 0 else (-1 if c < 0 else 0) for c in cash_flows if c != 0]
    cambios = sum(1 for i in range(1, len(signos)) if signos[i] != signos[i - 1])

    if cambios <= 1:
        v = _bisection_irr(cash_flows)
        return (v, "TIR") if v is not None else (None, "—")

    v = _mirr(cash_flows, finance_rate, reinvest_rate)
    if v is not None:
        return v, "MIRR"
    v = _bisection_irr(cash_flows)
    return (v, "TIR") if v is not None else (None, "—")


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



@st.cache_data(ttl=7200, show_spinner=False)
def get_nasa_power_componentes(lat: float, lon: float):
    """
    Trae la descomposición de la irradiancia que necesita la transposición:
      ALLSKY_SFC_SW_DWN  — global horizontal (GHI)
      ALLSKY_SFC_SW_DIFF — difusa horizontal
      ALLSKY_SFC_SW_DNI  — directa normal (solo para diagnóstico de consistencia)

    Devuelve (ghi[12], diff[12], dni[12]) como climatología mensual en
    kWh/m²/día, o None si el endpoint no responde. La transposición es opcional:
    si esto falla, la herramienta sigue trabajando en modo coplanar.
    """
    url = (
        "https://power.larc.nasa.gov/api/temporal/climatology/point"
        "?parameters=ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_SFC_SW_DNI"
        f"&community=RE&longitude={lon}&latitude={lat}&format=JSON"
    )
    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        par = r.json().get("properties", {}).get("parameter", {})

        claves = ["JAN","FEB","MAR","APR","MAY","JUN",
                  "JUL","AUG","SEP","OCT","NOV","DEC"]

        def _serie(nombre):
            d = par.get(nombre, {})
            if not d:
                return None
            out = []
            for k in claves:
                v = d.get(k)
                # NASA POWER marca los faltantes con −999
                if v is None or v < 0:
                    return None
                out.append(float(v))
            return out

        ghi  = _serie("ALLSKY_SFC_SW_DWN")
        diff = _serie("ALLSKY_SFC_SW_DIFF")
        dni  = _serie("ALLSKY_SFC_SW_DNI")

        if ghi is None:
            return None
        # La difusa es lo único indispensable. Si falta, se estima con la
        # correlación de Erbs sobre el índice de claridad mensual: es peor que
        # el dato medido pero mucho mejor que asumir una fracción fija.
        if diff is None:
            diff = _difusa_erbs(lat, ghi)
        return ghi, diff, dni

    except Exception:
        return None


def _difusa_erbs(lat: float, ghi_mes: list) -> list:
    """
    Fracción difusa mensual por la correlación de Erbs (1982), usada solo
    cuando NASA POWER no entrega ALLSKY_SFC_SW_DIFF para el píxel.

        Kd = 1.391 − 3.560·Kt + 4.189·Kt² − 2.137·Kt³     (Kt ≤ 0.722)
        Kd = 0.143                                        (Kt >  0.722)

    con Kt = H / H_0, el índice de claridad mensual sobre la irradiancia
    extraterrestre horizontal H_0 integrada en el día representativo.
    """
    lat_r = math.radians(lat)
    out = []
    for m in range(12):
        n   = DIA_REPRESENTATIVO[m]
        dec = _declinacion(n)
        w_s = _angulo_ocaso(lat_r, dec)
        G_on = _extraterrestre_normal(n)
        # H_0 diario en kWh/m²/día (Duffie-Beckman 1.10.3)
        H0 = (24.0 / math.pi) * G_on * (
            math.cos(lat_r) * math.cos(dec) * math.sin(w_s)
            + w_s * math.sin(lat_r) * math.sin(dec)) / 1000.0
        Kt = (ghi_mes[m] / H0) if H0 > 0 else 0.5
        Kt = max(0.05, min(0.85, Kt))
        if Kt <= 0.722:
            Kd = 1.391 - 3.560*Kt + 4.189*Kt**2 - 2.137*Kt**3
        else:
            Kd = 0.143
        Kd = max(0.10, min(0.98, Kd))
        out.append(ghi_mes[m] * Kd)
    return out


# ═════════════════════════════════════════════════════════════════════════════
# TRANSPOSICIÓN GHI → POA · modelo Hay-Davies
# ═════════════════════════════════════════════════════════════════════════════
# NASA POWER entrega irradiancia sobre plano HORIZONTAL (GHI). Un generador
# fotovoltaico inclinado recibe irradiancia sobre su propio plano (POA, plane of
# array), que no es la misma. Convertir una en otra es la "transposición".
#
# Hay-Davies descompone la difusa en dos partes: una circunsolar, que viene del
# disco solar y se comporta como directa, y una isotrópica repartida por toda la
# bóveda. El peso relativo lo da el índice de anisotropía Ai = DNI / G_on. En
# días despejados Ai → 1 y casi toda la difusa se trata como directa; en días
# nublados Ai → 0 y el modelo colapsa al isotrópico simple.
#
# Se prefiere sobre el isotrópico (Liu-Jordan) porque este subestima 3–5 % en
# climas despejados como el altiplano mexicano, y sobre Perez porque Perez exige
# datos horarios y coeficientes tabulados que no se justifican en una etapa
# preliminar. Hay-Davies queda dentro de ±2 % de Perez para inclinaciones
# menores a 40°, que cubre todo el rango de cubierta industrial.
#
# Referencia: Duffie & Beckman, "Solar Engineering of Thermal Processes", 4ª ed.,
# §2.16 (Hay-Davies), §2.13 (Collares-Pereira & Rabl), §2.14 (Liu-Jordan).
# ─────────────────────────────────────────────────────────────────────────────

# Día representativo de cada mes (Klein 1977) — el día cuya declinación iguala
# el promedio mensual. Usar el día 15 introduce un sesgo de hasta 0.4° en δ.
DIA_REPRESENTATIVO = [17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]

ALBEDO_DEFAULT = 0.20   # concreto envejecido / grava. Nieve 0.6–0.8, césped 0.20.

# Paso de integración. 10 min mantiene el error de cuadratura por debajo de
# 0.05 % contra un paso de 1 min y corre en milisegundos.
_PASO_MIN = 10.0


def _declinacion(n: int) -> float:
    """Declinación solar en radianes (Cooper). n = día del año."""
    return math.radians(23.45) * math.sin(2.0 * math.pi * (284 + n) / 365.0)


def _extraterrestre_normal(n: int) -> float:
    """Irradiancia extraterrestre normal G_on en W/m² (excentricidad orbital)."""
    return 1367.0 * (1.0 + 0.033 * math.cos(2.0 * math.pi * n / 365.0))


def _angulo_ocaso(lat_rad: float, dec_rad: float) -> float:
    """Ángulo horario de ocaso en radianes. Acotado para latitudes polares."""
    x = -math.tan(lat_rad) * math.tan(dec_rad)
    return math.acos(max(-1.0, min(1.0, x)))


def poa_mensual_hay_davies(lat: float,
                           ghi_mes: list,
                           diff_mes: list,
                           inclinacion: float,
                           azimut_brujula: float,
                           albedo: float = ALBEDO_DEFAULT) -> dict:
    """
    Transpone irradiancia horizontal mensual al plano del generador.

    Parámetros
      lat            : latitud en grados (+N, −S)
      ghi_mes        : list[12] irradiancia global horizontal, kWh/m²/día
      diff_mes       : list[12] irradiancia difusa horizontal, kWh/m²/día
      inclinacion    : β, grados desde la horizontal (0 = coplanar)
      azimut_brujula : convención brújula — 0=N, 90=E, 180=S, 270=O
      albedo         : reflectancia del suelo

    Devuelve dict con:
      poa      : list[12] kWh/m²/día sobre el plano del generador
      ratio    : list[12] POA/GHI mensual
      ratio_an : ratio anual ponderado por energía
      difusa   : list[12] fracción difusa mensual usada
    """
    lat_r  = math.radians(lat)
    beta   = math.radians(max(0.0, min(90.0, inclinacion)))
    # Convención Duffie-Beckman: γ = 0 al sur, negativo al este, positivo al oeste.
    gamma  = math.radians(((azimut_brujula - 180.0 + 180.0) % 360.0) - 180.0)
    rho    = max(0.0, min(1.0, albedo))

    cos_b  = math.cos(beta)
    sin_b  = math.sin(beta)
    f_iso  = (1.0 + cos_b) / 2.0     # vista de bóveda
    f_gnd  = (1.0 - cos_b) / 2.0     # vista de suelo

    dt_h   = _PASO_MIN / 60.0        # duración del paso, horas
    dw     = math.radians(15.0 * dt_h)

    poa_out, ratio_out, fd_out = [], [], []

    for m in range(12):
        H_ghi = max(0.0, float(ghi_mes[m]))
        if H_ghi <= 0.0:
            poa_out.append(0.0); ratio_out.append(1.0); fd_out.append(0.0)
            continue

        # La difusa no puede superar la global ni caer por debajo de la difusa
        # de cielo perfectamente despejado (~10 %). NASA POWER ocasionalmente
        # devuelve combinaciones inconsistentes en píxeles costeros.
        H_dif = float(diff_mes[m]) if diff_mes and diff_mes[m] is not None else 0.0
        H_dif = max(0.10 * H_ghi, min(0.98 * H_ghi, H_dif))

        n     = DIA_REPRESENTATIVO[m]
        dec   = _declinacion(n)
        G_on  = _extraterrestre_normal(n)
        w_s   = _angulo_ocaso(lat_r, dec)
        if w_s <= 1e-6:
            poa_out.append(0.0); ratio_out.append(1.0); fd_out.append(H_dif / H_ghi)
            continue

        # Coeficientes Collares-Pereira & Rabl para el reparto horario de la global
        w_s_deg = math.degrees(w_s)
        s60     = math.sin(math.radians(w_s_deg - 60.0))
        a_cpr   = 0.409 + 0.5016 * s60
        b_cpr   = 0.6609 - 0.4767 * s60

        # ── 1. Construir el perfil intradiario ───────────────────────────────
        pasos, f_tot, f_dif = [], [], []
        w = -w_s + dw / 2.0
        while w < w_s:
            cw   = math.cos(w)
            base = max(0.0, cw - math.cos(w_s))
            ft   = max(0.0, (a_cpr + b_cpr * cw) * base)   # Collares-Pereira & Rabl
            fd   = base                                     # Liu-Jordan
            pasos.append(w); f_tot.append(ft); f_dif.append(fd)
            w += dw

        s_tot = sum(f_tot); s_dif = sum(f_dif)
        if s_tot <= 0 or s_dif <= 0:
            poa_out.append(H_ghi); ratio_out.append(1.0); fd_out.append(H_dif / H_ghi)
            continue

        # ── 2. Integrar Hay-Davies paso a paso ───────────────────────────────
        poa_dia = 0.0
        for i, w in enumerate(pasos):
            E_ghi = H_ghi * f_tot[i] / s_tot      # kWh/m² en este paso
            E_dif = H_dif * f_dif[i] / s_dif
            if E_dif > E_ghi:
                E_dif = E_ghi
            E_bh  = E_ghi - E_dif                  # directa sobre horizontal

            cos_z = (math.sin(dec) * math.sin(lat_r)
                     + math.cos(dec) * math.cos(lat_r) * math.cos(w))
            if cos_z <= 0.02:
                # Sol muy bajo: la directa no se transpone de forma estable.
                # Solo entra la difusa isotrópica y el albedo.
                poa_dia += E_dif * f_iso + E_ghi * rho * f_gnd
                continue

            # Coseno de incidencia sobre el plano inclinado (Duffie-Beckman 1.6.2)
            cos_t = (math.sin(dec) * math.sin(lat_r) * cos_b
                     - math.sin(dec) * math.cos(lat_r) * sin_b * math.cos(gamma)
                     + math.cos(dec) * math.cos(lat_r) * cos_b * math.cos(w)
                     + math.cos(dec) * math.sin(lat_r) * sin_b * math.cos(gamma) * math.cos(w)
                     + math.cos(dec) * sin_b * math.sin(gamma) * math.sin(w))
            cos_t = max(0.0, cos_t)

            E_dni = E_bh / cos_z                   # kWh/m² normal en el paso
            R_b   = cos_t / cos_z

            # Índice de anisotropía — necesita irradiancia, no energía
            dni_w = (E_dni * 1000.0) / dt_h        # W/m²
            A_i   = max(0.0, min(1.0, dni_w / G_on))

            poa_dia += (E_dni * cos_t                                  # directa
                        + E_dif * (A_i * R_b + (1.0 - A_i) * f_iso)    # difusa H-D
                        + E_ghi * rho * f_gnd)                          # albedo

        poa_out.append(poa_dia)
        ratio_out.append(poa_dia / H_ghi if H_ghi > 0 else 1.0)
        fd_out.append(H_dif / H_ghi)

    # Ratio anual ponderado por energía, no promedio simple de ratios
    e_poa = sum(poa_out[m] * MONTH_DAYS[m] for m in range(12))
    e_ghi = sum(max(0.0, float(ghi_mes[m])) * MONTH_DAYS[m] for m in range(12))
    ratio_an = (e_poa / e_ghi) if e_ghi > 0 else 1.0

    return {"poa": poa_out, "ratio": ratio_out,
            "ratio_an": ratio_an, "difusa": fd_out}


def inclinacion_optima(lat: float, ghi_mes: list, diff_mes: list,
                       azimut_brujula: float = 180.0,
                       albedo: float = ALBEDO_DEFAULT,
                       tope: float = 40.0) -> tuple:
    """
    Barre la inclinación de 0° al tope y devuelve (β_óptimo, ratio_óptimo).

    El tope existe por una razón práctica: pasando ~30° la estructura sobre
    cubierta empieza a necesitar lastre o anclaje significativo y la separación
    entre filas crece, así que la ganancia marginal de irradiancia se la come
    el costo de estructura y la pérdida de superficie utilizable.
    """
    mejor_b, mejor_r = 0.0, 0.0
    b = 0.0
    while b <= tope + 1e-9:
        r = poa_mensual_hay_davies(lat, ghi_mes, diff_mes, b,
                                   azimut_brujula, albedo)["ratio_an"]
        if r > mejor_r:
            mejor_r, mejor_b = r, b
        b += 1.0
    return mejor_b, mejor_r


# ── Recorte del inversor (clipping) ──────────────────────────────────────────
# Ley de potencia con umbral ajustada a valores típicos publicados de pérdida
# anual por recorte en sistemas fijos de latitud baja:
#
#     clip(r) = CLIP_A · max(0, r − CLIP_R0) ^ CLIP_B
#
# Sustituye a la interpolación lineal sobre 7 puntos que había antes. Tres razones:
#
#  1. DERIVADA CONTINUA. La interpolación daba una derivada escalonada (0.050 →
#     0.110 → 0.180 → 0.240), lo que hacía que el óptimo económico se pegara a los
#     nodos en vez de caer donde realmente está. Con la ley de potencia el óptimo
#     de ejemplo pasa de 1.300 (artefacto del nodo) a 1.255 (valor real).
#
#  2. CERO EXACTO BAJO EL UMBRAL. Un polinomio ajustado a los mismos puntos se
#     vuelve negativo en r≈1.05 y predice recorte con arreglos subdimensionados.
#     La forma con umbral lo impide por construcción.
#
#  3. EXTRAPOLA. La tabla se aplanaba en 14 % arriba de r=1.80 y dejaba de
#     discriminar; la función sigue creciendo (21 % a r=2.0, 43 % a r=2.5).
#
# El exponente ~1.6 tiene sentido físico: el recorte es la integral del exceso
# sobre un umbral en una distribución con cola, y eso crece como potencia.
# Error máximo contra los puntos de referencia: 0.18 puntos porcentuales.
#
# PROCEDENCIA: los puntos de referencia son valores típicos publicados para
# sistemas fijos, NO una correlación citable de NREL o SAM. Ver CURVA_CLIP_REF.
CLIP_A  = 0.2538
CLIP_R0 = 1.11
CLIP_B  = 1.60

# Puntos de referencia usados para el ajuste. Se conservan para validación y
# para poder recalibrar contra generación medida de plantas propias.
CURVA_CLIP_REF = [(1.00, 0.000), (1.10, 0.000), (1.20, 0.005),
                  (1.30, 0.016), (1.40, 0.034), (1.50, 0.058), (1.80, 0.140)]


def _clip_desde_dcac(dc_ac: float) -> float:
    """Pérdida fraccional anual por recorte para una relación DC/AC dada."""
    if dc_ac <= CLIP_R0:
        return 0.0
    return CLIP_A * (dc_ac - CLIP_R0) ** CLIP_B


def _dclip_ddcac(dc_ac: float) -> float:
    """Derivada de la pérdida por recorte respecto a la relación DC/AC."""
    if dc_ac <= CLIP_R0:
        return 0.0
    return CLIP_A * CLIP_B * (dc_ac - CLIP_R0) ** (CLIP_B - 1)


def dc_ac_optimo(costo_dc_usd_kwp: float, rendimiento_kwh_kwp: float,
                 valor_kwh_mxn: float, usd_mxn: float,
                 factor_descuento: float, ac_total_kw: float,
                 monthly_irr_pr: list = None, monthly_cons: list = None,
                 om_frac_vp: float = 0.0, r_max: float = 2.0,
                 paso: float = 0.005) -> tuple:
    """
    Relación DC/AC que maximiza el valor presente neto por kW AC instalado.

    Se evalúa el VPN completo en una malla de r en vez de resolver la condición
    marginal analítica. La razón es que para un proyecto de AUTOCONSUMO el valor
    del kWh marginal NO es constante: al subir r se genera más de lo que el
    cliente consume en los meses pico, y ese excedente se vierte a $0. La
    fracción de autoconsumo cae con r, y eso desplaza el óptimo hacia abajo de
    forma sustancial.

    Con un caso de 300 MWh/año de consumo el óptimo real resulta 1.31, mientras
    que ignorando la restricción de consumo salía 1.75. Es la diferencia entre
    optimizar un proyecto de autoconsumo y uno que vende toda su energía.

    costo_dc_usd_kwp : costo MARGINAL de añadir un kWp — módulo, estructura y
        cableado DC. NO incluye inversor, interconexión ni costos fijos.
    factor_descuento : Σ (1−deg)^y (1+inf)^y / (1+r)^(y+1) sobre la vida útil.
    monthly_irr_pr   : 12 valores de kWh generados por kWp instalado en cada mes
        (HSP × PR × días). Si es None se asume que toda la energía tiene valor.
    monthly_cons     : 12 valores de consumo (kWh). Si es None, ídem.
    om_frac_vp       : valor presente del O&M como fracción del CAPEX marginal.

    Devuelve (r_optimo, autoconsumo_en_el_optimo). r_optimo es None si ni
    siquiera conviene r = 1.0 (panel muy caro o energía muy barata).
    """
    if rendimiento_kwh_kwp <= 0 or valor_kwh_mxn <= 0 or ac_total_kw <= 0:
        return None, None

    _costo_kwp = costo_dc_usd_kwp * usd_mxn * (1 + om_frac_vp)

    def vpn(r):
        kwp = ac_total_kw * r
        _c = 1 - _clip_desde_dcac(r)
        if monthly_irr_pr and monthly_cons and sum(monthly_cons) > 0:
            mg = [kwp * monthly_irr_pr[m] * _c for m in range(12)]
            _tot = sum(mg)
            cub = sum(min(mg[m], monthly_cons[m]) for m in range(12))
            af = (cub / _tot) if _tot > 0 else 1.0
        else:
            _tot = kwp * rendimiento_kwh_kwp * _c
            af = 1.0
        return _tot * af * valor_kwh_mxn * factor_descuento - kwp * _costo_kwp

    mejor_r, mejor_v = None, None
    r = 1.0
    while r <= r_max + 1e-9:
        v = vpn(r)
        if mejor_v is None or v > mejor_v:
            mejor_r, mejor_v = r, v
        r += paso
    if mejor_v is None or mejor_v <= 0:
        return None, None

    # Autoconsumo en el óptimo, para poder explicárselo al usuario.
    af_opt = None
    if monthly_irr_pr and monthly_cons and sum(monthly_cons) > 0:
        kwp = ac_total_kw * mejor_r
        _c = 1 - _clip_desde_dcac(mejor_r)
        mg = [kwp * monthly_irr_pr[m] * _c for m in range(12)]
        _t = sum(mg)
        af_opt = (sum(min(mg[m], monthly_cons[m]) for m in range(12)) / _t) if _t > 0 else 1.0
    return mejor_r, af_opt


def clip_a_nivel(dc_ac_real: float, factor_energia: float) -> float:
    """
    Recorte esperado cuando el recurso del año está a `factor_energia` del P50.

    El recorte NO escala linealmente con la irradiancia: es un fenómeno de cola.
    En un año pobre menos horas rebasan el techo del inversor, así que se recorta
    proporcionalmente mucho menos. Aplicar el mismo clip_frac al P50 y al P90
    castiga el P90 de más.

    En vez de inventar un exponente, se reutiliza la misma curva evaluada a la
    relación DC/AC EFECTIVA del año: menos irradiancia equivale a un generador
    más pequeño frente al mismo inversor.

        DC/AC_efectivo = DC/AC_real × factor_energia

    Con DC/AC 1.45 y un P90 al 90.9 % del P50, el DC/AC efectivo baja a 1.32 y el
    recorte pasa de 4.6 % a 1.9 % — un factor 0.42, coherente con la simulación
    horaria de curvas diarias (que da 0.21 con un perfil de nubosidad sintético;
    la correlación es la referencia más confiable de las dos).
    """
    f = max(0.0, min(1.5, factor_energia))
    return _clip_desde_dcac(dc_ac_real * f)


# ── Incertidumbre del recurso — componentes de σ para el P90 ─────────────────
# El P90 bancable no es el percentil 10 de la serie histórica: esa muestra sólo
# captura la variabilidad interanual del recurso e ignora que el propio dato de
# entrada, el modelo y el sizing tienen error. La convención de la industria
# (IEC 61724-1, guías de due diligence) es:
#     P90 = P50 · (1 − 1.282 · σ_total),  σ_total = √(Σ σ_i²)
# σ_recurso es la incertidumbre del dataset satelital frente a piranómetro en
# tierra. NASA POWER es un producto de reanálisis a ~0.5°, con sesgo conocido en
# zonas de altitud y alto aerosol — condiciones comunes en México — por lo que se
# toma un valor conservador. Ajustar si se dispone de medición en sitio.
SIGMA_RECURSO   = 0.06   # incertidumbre del dato de irradiancia (satélite vs tierra)
SIGMA_MODELO    = 0.03   # modelo de transposición, PR, pérdidas
SIGMA_DEGRADAC  = 0.01   # dispersión de la tasa de degradación

# Valores z de la normal estándar para cada nivel de excedencia.
# Pxx = P50 · (1 − z_xx · σ_total). "Excedido el xx % de los años."
#   P75 → z = -NORMSINV(0.25)   P90 → z = -NORMSINV(0.10)   P99 → z = -NORMSINV(0.01)
# El paquete que revisa un comité de crédito incluye los cuatro niveles:
# P50 y P75 para el caso base del equity, P90 para dimensionar la deuda, y P99
# para calibrar la cuenta de reserva de servicio de deuda (DSRA) y el seguro.
Z_P75           = 0.674490
Z_P90           = 1.281552
Z_P99           = 2.326348

# Horizonte de excedencia. Los term sheets especifican percentil Y horizonte
# ("P90 a un año" vs "P90 a diez años"). Sólo la componente interanual se promedia
# con √n; σ_recurso y σ_modelo son sesgos sistemáticos que no se diluyen: si el
# dataset sobreestima la irradiancia del sitio, la sobreestima todos los años.
# Esta herramienta reporta el P90 ANUAL, que es la base conservadora para DSCR.
HORIZONTE_PXX   = 1      # años


def compute_p90(irr_por_anio: dict, kwp: float, pr: float,
                sigma_extra: bool = True,
                ratio_irr: float = 1.0,
                dc_ac_real: float = 0.0,
                disponibilidad: float = 1.0) -> tuple:
    """
    Niveles de excedencia de la generación anual, ya en AC.

    Devuelve (p50, p90, gen_por_anio, detalle). Todos los valores son AC:
    post-recorte del inversor y post-disponibilidad.

    Metodología
    -----------
    El recorte del inversor se aplica AÑO POR AÑO sobre la serie histórica,
    ANTES de calcular la estadística. Es una transformación física del recurso,
    no un ajuste posterior sobre los percentiles.

    Cada año se recorta a su propio nivel: un año pobre rebasa el techo del
    inversor menos horas, así que pierde proporcionalmente menos. Eso hace que
    el recorte COMPRIMA la cola alta de la distribución, y esa compresión se
    refleja en un σ interanual menor — efecto que un ajuste posterior sobre el
    P50 y el P90 no puede capturar.

    ratio_irr      : escala la serie NASA a la irradiancia editada por el usuario.
    dc_ac_real     : relación DC/AC del bloque de inversores. 0 = sin recorte.
    disponibilidad : fracción de tiempo operativa (1.0 = neutro).

    Si sigma_extra=False reproduce el percentil 10 empírico, que es
    sistemáticamente optimista y NO debe usarse para contratos.
    """
    if not irr_por_anio:
        return None, None, {}, {}

    # 1. Generación de cada año histórico ANTES DE SATURACIÓN.
    #
    # NOMENCLATURA — esto NO es generación DC. El PR ya incorpora la eficiencia
    # de conversión del inversor (~2 %), además de cableado, suciedad, mismatch,
    # temperatura y orientación. Así que kWp × HSP × PR es energía en el punto de
    # medición suponiendo que el inversor nunca satura: "AC antes de recorte".
    #
    # El recorte se aplica después sobre esta magnitud, y eso es correcto:
    #     min(P_dc · η, P_AC_nominal) ≡ min(P_dc, P_AC_nominal/η) · η
    # Capear la potencia ya convertida contra el límite AC da el mismo resultado
    # que capear la DC contra el límite equivalente y luego convertir.
    gen_pre_clip = {}
    for year, meses in sorted(irr_por_anio.items()):
        gen_pre_clip[year] = kwp * pr * ratio_irr * sum(meses[m] * MONTH_DAYS[m]
                                                        for m in range(12))

    # 2. Saturación del inversor por año, referida al año mediano, y disponibilidad.
    _ref = float(np.percentile(list(gen_pre_clip.values()), 50)) or 1.0
    gen_por_anio = {}
    clip_por_anio = {}
    for year, g in gen_pre_clip.items():
        _c = clip_a_nivel(dc_ac_real, g / _ref) if dc_ac_real > 0 else 0.0
        clip_por_anio[year] = _c
        gen_por_anio[year] = g * (1 - _c) * disponibilidad

    # 3. Estadística sobre la serie AC.
    valores  = sorted(gen_por_anio.values())
    p50_real = float(np.percentile(valores, 50))

    # σ interanual medida sobre la serie (coeficiente de variación).
    media = float(np.mean(valores))
    sigma_interanual = float(np.std(valores, ddof=1) / media) if media > 0 and len(valores) > 1 else 0.0

    if not sigma_extra:
        p90_real = float(np.percentile(valores, 10))
        detalle = dict(metodo="percentil 10 empírico",
                       sigma_interanual=sigma_interanual, sigma_total=sigma_interanual,
                       n_anios=len(valores))
        return p50_real, p90_real, gen_por_anio, detalle

    # Sólo la componente interanual se promedia con la raíz del horizonte.
    _si_h = sigma_interanual / math.sqrt(max(1, HORIZONTE_PXX))
    sigma_total = float(np.sqrt(_si_h ** 2 + SIGMA_RECURSO ** 2
                                + SIGMA_MODELO ** 2 + SIGMA_DEGRADAC ** 2))
    p75_real = p50_real * (1 - Z_P75 * sigma_total)
    p90_real = p50_real * (1 - Z_P90 * sigma_total)
    p99_real = p50_real * (1 - Z_P99 * sigma_total)
    detalle = dict(
        metodo="P50·(1−z·σ_total)",
        horizonte=HORIZONTE_PXX,
        sigma_interanual=sigma_interanual,
        sigma_recurso=SIGMA_RECURSO,
        sigma_modelo=SIGMA_MODELO,
        sigma_degradacion=SIGMA_DEGRADAC,
        sigma_total=sigma_total,
        n_anios=len(valores),
        p75=p75_real, p99=p99_real,
        p90_empirico=float(np.percentile(valores, 10)),
        # Recorte: se reporta el del año mediano y el rango observado en la serie.
        clip_p50=clip_por_anio.get(
            max(gen_pre_clip, key=lambda y: -abs(gen_pre_clip[y] - _ref)), 0.0),
        clip_min=min(clip_por_anio.values()) if clip_por_anio else 0.0,
        clip_max=max(clip_por_anio.values()) if clip_por_anio else 0.0,
        gen_pre_clip_p50=_ref,
        disponibilidad=disponibilidad,
    )
    return p50_real, p90_real, gen_por_anio, detalle


# ── Dimensionamiento de inversores ───────────────────────────────────────────
def calc_inversores(kwp: float, inv_unit_kw: float, dc_ac_objetivo: float,
                    irr_vals: tuple, effective_pr: float,
                    monthly_gen: list,
                    n_inv_manual: int = 0) -> dict:
    """
    Dimensiona el bloque de inversores y estima la pérdida por recorte (clipping).

    kwp            : potencia pico DC del generador.
    inv_unit_kw    : potencia nominal AC de cada inversor (kW).
    dc_ac_objetivo : relación DC/AC buscada (típico 1.15–1.30 en México).
    monthly_gen    : generación mensual DC (kWh) ya calculada por el sizing.
    n_inv_manual   : si > 0, se usa ese número de inversores y la relación DC/AC
                     pasa a ser un RESULTADO en vez de un objetivo. Sirve para
                     forzar una configuración concreta (equipo ya cotizado, límite
                     de espacio en el cuarto eléctrico, disponibilidad de modelo).

    Metodología del clipping
    ------------------------
    Sin serie horaria no se puede contar hora por hora la energía recortada, así
    que se usa la correlación empírica de NREL/SAM entre la relación DC/AC y la
    pérdida anual por recorte para sistemas fijos en latitudes bajas:

        DC/AC ≤ 1.10  →  ~0.0 %
        DC/AC  1.20   →  ~0.5 %
        DC/AC  1.30   →  ~1.6 %
        DC/AC  1.40   →  ~3.4 %
        DC/AC  1.50   →  ~5.8 %

    Se interpola linealmente entre puntos. Es una aproximación: el recorte real
    depende de la forma de la curva diaria, que a su vez depende de inclinación,
    azimut y régimen de nubosidad. Para diseño ejecutivo hay que sustituirlo por
    una simulación 8760 h en PVsyst o SAM.
    """
    inv_unit_kw = max(0.1, float(inv_unit_kw))
    if n_inv_manual and n_inv_manual > 0:
        # ── MODO DETALLE ────────────────────────────────────────────────────
        # El equipo está definido: la capacidad AC sale de las unidades reales y
        # la relación DC/AC es un RESULTADO, con su granularidad.
        n_inv        = int(n_inv_manual)
        ac_total_kw  = n_inv * inv_unit_kw
        dc_ac_real   = kwp / ac_total_kw if ac_total_kw > 0 else 0.0
        modo_dim     = "manual"
        n_inv_equiv  = n_inv
    else:
        # ── MODO PRE-SIZING ─────────────────────────────────────────────────
        # La relación DC/AC ASIGNADA manda y la capacidad AC se deriva de ella,
        # sin redondear a unidades enteras.
        #
        # Antes se calculaba al revés: se elegía el número mínimo de inversores
        # para no exceder el objetivo, y el DC/AC real caía donde la granularidad
        # del catálogo lo dejara. Con 182 kWp y objetivo 1.20 eso daba 1.14 con
        # unidades de 10 kW, 1.04 con unidades de 25 kW y 0.91 con unidades de
        # 50 kW — el resultado dependía de un dato que en pre-sizing todavía no
        # se conoce, y el recorte oscilaba entre 0 % y 0.67 % por esa suposición.
        #
        # Es el criterio de PVWatts: en estimación preliminar se especifica la
        # relación DC/AC, no un modelo de inversor. La granularidad se resuelve
        # en ingeniería de detalle, con el modo manual.
        dc_ac_real   = max(dc_ac_objetivo, 0.01)
        ac_total_kw  = kwp / dc_ac_real if dc_ac_real > 0 else 0.0
        # Número de unidades equivalente, sólo informativo.
        n_inv_equiv  = max(1, int(math.ceil(ac_total_kw / max(inv_unit_kw, 0.1))))
        n_inv        = n_inv_equiv
        modo_dim     = "auto"

    clip_frac = _clip_desde_dcac(dc_ac_real)

    gen_pre_clip_anual = sum(monthly_gen)

    # ── Reparto mensual del recorte: FACTOR UNIFORME ─────────────────────────
    # Antes se repartía proporcionalmente al CUBO de la generación mensual, con
    # la idea de concentrarlo en los picos. Al contrastarlo contra una simulación
    # horaria con nubosidad variable resultó mal calibrado: subestimaba marzo a
    # la mitad y asignaba a diciembre 24 veces más recorte del que realmente
    # ocurre (0.15 % real contra 3.58 % del cubo).
    #
    # La razón es estructural: el recorte es un fenómeno de UMBRAL. En los meses
    # de sol bajo el inversor nunca satura y el recorte es cero exacto, no "una
    # fracción pequeña". Ninguna ley de potencia puede reproducir eso, y probar
    # con exponentes 2 o 4 apenas mueve el error (47 puntos de distribución en el
    # mejor caso).
    #
    # Se usa un factor uniforme: es marginalmente menos preciso que el cubo
    # (62.7 vs 47.3 puntos a DC/AC 1.46) pero la diferencia práctica entre ambos
    # métodos es de 0.5–1.3 % en el mes más afectado y CERO cuando el DC/AC está
    # por debajo del umbral. A cambio, la cadena de generación queda como una
    # sola multiplicación de escalares, fácil de auditar y de replicar en Excel.
    #
    # El TOTAL ANUAL —lo que alimenta el modelo financiero— es idéntico en ambos
    # métodos. Para el perfil mensual fino hace falta simulación 8760 h.
    clip_mensual   = [g * clip_frac for g in monthly_gen]
    monthly_gen_ac = [g * (1 - clip_frac) for g in monthly_gen]

    # Validación de rango operativo
    # Arriba del último punto de referencia la función extrapola (ya no se aplana),
    # pero el ajuste deja de estar respaldado por datos.
    fuera_de_curva = dc_ac_real > CURVA_CLIP_REF[-1][0]
    if fuera_de_curva:
        estado = "excesivo"
        nota = (f"DC/AC {dc_ac_real:.2f} está fuera del rango con datos de referencia "
                f"(hasta {CURVA_CLIP_REF[-1][0]:.2f}). La función extrapola y da "
                f"{_clip_desde_dcac(dc_ac_real)*100:.1f} % de recorte, pero ese valor ya no "
                f"está validado. Requiere simulación horaria.")
    elif dc_ac_real < 1.05:
        estado, nota = "sub", "Inversor sobredimensionado — CAPEX AC desaprovechado."
    elif dc_ac_real <= 1.35:
        estado, nota = "ok", "Relación DC/AC en el rango óptimo para México."
    elif dc_ac_real <= 1.45:
        estado, nota = "alto", "DC/AC alto — verificar recorte contra simulación horaria."
    else:
        estado, nota = "excesivo", "DC/AC excesivo — pérdida por recorte significativa."

    return dict(
        n_inv=n_inv, inv_unit_kw=inv_unit_kw, ac_total_kw=ac_total_kw,
        dc_ac_real=dc_ac_real, dc_ac_objetivo=dc_ac_objetivo, modo_dim=modo_dim,
        n_inv_equiv=n_inv_equiv,
        n_inv_auto=max(1, int(math.ceil((kwp / max(dc_ac_objetivo, 0.01)) / max(inv_unit_kw, 0.1)))),
        clip_frac=clip_frac, clip_kwh=gen_pre_clip_anual * clip_frac,
        clip_mensual=clip_mensual,
        monthly_gen_ac=monthly_gen_ac, annual_gen_ac=sum(monthly_gen_ac),
        fuera_de_curva=fuera_de_curva,
        annual_gen_pre_clip=gen_pre_clip_anual,
        estado=estado, nota=nota,
    )


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
                         om_pct: float = 1.0,
                         autoconsumo_frac: float = 1.0,
                         lid_pct: float = 1.5,
                         inv_replace_year: int = 12,
                         inv_replace_pct: float = 10.0,
                         inv_replace_mxn: float = 0.0,
                         inv_replace_esc: float = 0.0,
                         isr_pct: float = 0.0,
                         deduccion_art34: bool = False,
                         escudo_inmediato: bool = True,
                         seguro_pct: float = 0.0,
                         con_deuda: bool = False,
                         deuda_pct: float = 0.0,
                         tasa_deuda_pct: float = 0.0,
                         plazo_deuda_tk: int = 0) -> dict:
    """Modelo financiero completo: VPN, TIR, payback, LCOE, flujos anuales.

    om_pct           : % de la inversión MXN destinado a O&M anual.
    autoconsumo_frac : fracción de la generación que efectivamente desplaza consumo
                       (Σ min(gen_mes, cons_mes) / Σ gen_mes). El excedente vertido
                       a la red se valora en $0 — criterio conservador. Con 1.0 el
                       modelo se comporta como antes.
    lid_pct          : pérdida inicial de primer año (LID/LeTID) en %. Se aplica una
                       sola vez al año 1; después corre panel_degradation anual.
    inv_replace_year : año en que se reemplaza el inversor (0 = sin reemplazo).
    inv_replace_pct  : costo del reemplazo como % del CAPEX (respaldo si no se da
                       inv_replace_mxn).
    inv_replace_mxn  : costo del reemplazo HOY en MXN, derivado de $/kW AC × kW AC.
                       Tiene prioridad sobre inv_replace_pct.
    inv_replace_esc  : escalador anual propio del precio del inversor (%). Default 0:
                       los inversores bajan de precio en términos reales.
    isr_pct          : tasa de ISR aplicada al flujo gravable (0 = modelo pre-impuestos).
    deduccion_art34  : si True, deduce el 100 % del CAPEX en el año 1 (LISR Art. 34,
                       deducción acelerada de equipo de generación de energía limpia).
    escudo_inmediato : si True, el escudo fiscal negativo se cobra en el ejercicio
                       (causante con otras utilidades). Si False, se arrastra como
                       pérdida fiscal amortizable — supuesto correcto para una SPV.
    seguro_pct       : % de la inversión MXN destinado a seguros y otros costos fijos.
                       Existía en el modelo PPA y faltaba aquí para el mismo activo.
    con_deuda        : si True, el proyecto se apalanca. Los flujos pasan a ser al
                       accionista (FCFE) y el desembolso inicial es el equity, no el
                       CAPEX. Los intereses son deducibles; la amortización no.
    """
    years = list(range(1, vida_util + 1))
    r     = discount_rate / 100
    inv_mxn = inversion_usd * usd_to_mxn
    af    = max(0.0, min(1.0, autoconsumo_frac))

    # Generación: pérdida LID una sola vez en el año 1, luego degradación compuesta.
    lid_factor = 1 - lid_pct / 100
    gen_proj   = [annual_gen * lid_factor * (1 - panel_degradation / 100) ** (y - 1)
                  for y in years]
    tarifas_y  = [tarifa_efectiva * (1 + inflation / 100) ** (y - 1) for y in years]
    # Sólo la energía autoconsumida genera ahorro; el excedente se valora en $0.
    flujo_nominal = [gen_proj[i] * af * tarifas_y[i] for i in range(len(years))]
    # FIX S5 — O&M y seguros. El modelo PPA ya cobraba seguros sobre el mismo activo
    # físico; Turnkey no, así que el mismo sistema tenía dos estructuras de costo
    # incompatibles. `om_anual` agrega ambos para no romper los consumidores previos.
    om_oper       = [inv_mxn * (om_pct / 100) * (1 + inflation / 100) ** (y - 1) for y in years]
    seguro_anual  = [inv_mxn * (seguro_pct / 100) * (1 + inflation / 100) ** (y - 1) for y in years]
    om_anual      = [om_oper[i] + seguro_anual[i] for i in range(len(years))]

    # ── Reemplazo de inversor ────────────────────────────────────────────────
    # Si se pasa `inv_replace_mxn` (costo hoy en MXN, derivado de $/kW AC x kW AC
    # instalados) se usa ese valor. Si no, se cae al % del CAPEX por compatibilidad.
    #
    # El escalador es PROPIO y por defecto 0 %: el precio de los inversores lleva
    # años cayendo en términos reales, así que inflarlo al INPC como se hacía antes
    # sobreestimaba el costo futuro ~38 % a 11 años.
    capex_reposicion = [0.0] * len(years)
    if inv_replace_year and 1 <= inv_replace_year <= vida_util:
        _base_rep = (inv_replace_mxn if inv_replace_mxn > 0
                     else inv_mxn * (inv_replace_pct / 100))
        if _base_rep > 0:
            _idx = inv_replace_year - 1
            capex_reposicion[_idx] = _base_rep * (1 + inv_replace_esc / 100) ** _idx

    # ── Impuestos ────────────────────────────────────────────────────────────
    # Base gravable = ahorro - O&M - depreciación. El ahorro en la factura eléctrica
    # es un menor gasto deducible, por lo que incrementa la utilidad gravable.
    t = max(0.0, isr_pct / 100)
    if t > 0:
        if deduccion_art34:
            # LISR Art. 34 fracc. XIII: 100 % deducible en el ejercicio de la inversión.
            depreciacion = [inv_mxn] + [0.0] * (vida_util - 1)
        else:
            # Línea recta sobre la vida útil.
            depreciacion = [inv_mxn / vida_util] * vida_util

        # FIX M2 — el reemplazo del inversor es inversión de capital y también genera
        # escudo fiscal. Antes se restaba del flujo pero no de la base gravable, lo
        # que sobreestimaba el impuesto del año del evento.
        for i in range(len(years)):
            if capex_reposicion[i] > 0:
                if deduccion_art34:
                    depreciacion[i] += capex_reposicion[i]
                else:
                    # Se deprecia en línea recta sobre los años que restan de vida útil.
                    _restan = max(1, vida_util - i)
                    for k in range(i, vida_util):
                        depreciacion[k] += capex_reposicion[i] / _restan

        base_gravable = [flujo_nominal[i] - om_anual[i] - depreciacion[i]
                         for i in range(len(years))]

        # FIX M3 — monetización del escudo fiscal.
        # Con la deducción acelerada del Art. 34 la base del año 1 se vuelve muy
        # negativa. Que eso se convierta en efectivo inmediato sólo es cierto si el
        # contribuyente tiene otras utilidades contra las cuales aplicarlo.
        #   escudo_inmediato=True  → causante en operación: el ahorro fiscal se cobra
        #                            en el ejercicio (impuesto negativo).
        #   escudo_inmediato=False → SPV sin otros ingresos: la base negativa se
        #                            arrastra como pérdida fiscal y se amortiza contra
        #                            utilidades futuras del propio proyecto.
        if escudo_inmediato:
            impuestos = [base_gravable[i] * t for i in range(len(years))]
            perdida_acum = [0.0] * len(years)
        else:
            impuestos    = []
            perdida_acum = []
            _saldo = 0.0   # pérdida fiscal pendiente de amortizar
            for i in range(len(years)):
                _base = base_gravable[i]
                if _base < 0:
                    _saldo += -_base
                    impuestos.append(0.0)
                else:
                    _aplicado = min(_saldo, _base)
                    _saldo   -= _aplicado
                    impuestos.append((_base - _aplicado) * t)
                perdida_acum.append(_saldo)
    else:
        depreciacion = [0.0] * vida_util
        impuestos    = [0.0] * vida_util
        perdida_acum = [0.0] * vida_util

    # ── Financiamiento opcional (FIX S6) ─────────────────────────────────────
    # Buena parte del turnkey en México se financia con crédito verde o
    # arrendamiento. Sin apalancamiento, la TIR reportada no es la que ve el
    # cliente. Los intereses son deducibles; la amortización de capital no.
    deuda_mxn = 0.0
    serv_deuda_tk = 0.0
    interes_y = [0.0] * len(years)
    capital_y = [0.0] * len(years)
    if con_deuda and tasa_deuda_pct > 0 and plazo_deuda_tk > 0 and 0 < deuda_pct <= 100:
        deuda_mxn = inv_mxn * (deuda_pct / 100)
        _rd = tasa_deuda_pct / 100
        _nd = min(plazo_deuda_tk, vida_util)
        serv_deuda_tk = deuda_mxn * _rd / (1 - (1 + _rd) ** (-_nd))
        _saldo = deuda_mxn
        for i in range(_nd):
            _int = _saldo * _rd
            _cap = serv_deuda_tk - _int
            interes_y[i] = _int
            capital_y[i] = _cap
            _saldo -= _cap
        # El interés es gasto deducible: recalcula impuestos con el escudo.
        if t > 0:
            base_gravable = [flujo_nominal[i] - om_anual[i] - depreciacion[i] - interes_y[i]
                             for i in range(len(years))]
            if escudo_inmediato:
                impuestos = [base_gravable[i] * t for i in range(len(years))]
            else:
                impuestos, perdida_acum, _saldo_pf = [], [], 0.0
                for i in range(len(years)):
                    _b = base_gravable[i]
                    if _b < 0:
                        _saldo_pf += -_b; impuestos.append(0.0)
                    else:
                        _ap = min(_saldo_pf, _b); _saldo_pf -= _ap
                        impuestos.append((_b - _ap) * t)
                    perdida_acum.append(_saldo_pf)

    servicio_deuda_y = [interes_y[i] + capital_y[i] for i in range(len(years))]
    equity_mxn = inv_mxn - deuda_mxn

    flujo_neto  = [flujo_nominal[i] - om_anual[i] - capex_reposicion[i] - impuestos[i]
                   - servicio_deuda_y[i] for i in range(len(years))]
    factor_desc = [1 / (1 + r) ** y for y in years]
    flujo_desc  = [flujo_neto[i] * factor_desc[i] for i in range(len(years))]

    # El desembolso inicial es el equity, no el CAPEX total, cuando hay deuda.
    acum_nominal, acum = [], -equity_mxn
    for fn in flujo_neto:
        acum += fn; acum_nominal.append(acum)
    acum_desc, acum = [], -equity_mxn
    for fd in flujo_desc:
        acum += fd; acum_desc.append(acum)

    vpn = acum_desc[-1]

    # DSCR del turnkey apalancado — mismo criterio que el PPA.
    cfads_y = [flujo_nominal[i] - om_anual[i] - impuestos[i] for i in range(len(years))]
    dscr_y  = [(cfads_y[i] / servicio_deuda_y[i]) if servicio_deuda_y[i] > 0 else None
               for i in range(len(years))]
    _dv = [d for d in dscr_y if d is not None]
    dscr_min = min(_dv) if _dv else None

    # TIR — con verificación de unicidad; cae a MIRR si hay múltiples raíces.
    tir, tir_metodo = _irr_robusta([-equity_mxn] + flujo_neto, finance_rate=r, reinvest_rate=r)

    pb_simple = None
    for i, v in enumerate(acum_nominal):
        if v >= 0:
            prev = acum_nominal[i - 1] if i > 0 else -equity_mxn
            pb_simple = round(years[i] - 1 + (-prev) / (v - prev), 1)
            break

    pb_disc = None
    for i, v in enumerate(acum_desc):
        if v >= 0:
            prev = acum_desc[i - 1] if i > 0 else -equity_mxn
            pb_disc = round(years[i] - 1 + (-prev) / (v - prev), 1)
            break

    # LCOE sobre generación total (no sólo autoconsumida): es el costo de producir
    # el kWh, independiente de cómo se valorice.
    total_gen_desc  = sum(gen_proj[i] * factor_desc[i] for i in range(len(years)))
    total_cost_desc = inv_mxn + sum((om_anual[i] + capex_reposicion[i]) * factor_desc[i]
                                    for i in range(len(years)))
    lcoe = total_cost_desc / total_gen_desc if total_gen_desc > 0 else 0

    return dict(
        vpn=vpn, tir=tir, tir_metodo=tir_metodo,
        pb_simple=pb_simple, pb_disc=pb_disc, lcoe=lcoe,
        years=years, gen_proj=gen_proj, tarifas_y=tarifas_y,
        flujo_nominal=flujo_nominal, om_anual=om_anual, flujo_neto=flujo_neto,
        om_oper=om_oper, seguro_anual=seguro_anual,
        capex_reposicion=capex_reposicion, impuestos=impuestos,
        depreciacion=depreciacion, perdida_fiscal_acum=perdida_acum,
        factor_desc=factor_desc, flujo_desc=flujo_desc,
        acum_nominal=acum_nominal, acum_desc=acum_desc, inv_mxn=inv_mxn,
        deuda_mxn=deuda_mxn, equity_mxn=equity_mxn,
        interes_y=interes_y, capital_y=capital_y,
        servicio_deuda_y=servicio_deuda_y, cfads_y=cfads_y,
        dscr_y=dscr_y, dscr_min=dscr_min,
        # Eco de la configuración — necesario para que los escenarios de sensibilidad
        # no reviertan a defaults silenciosamente.
        panel_degradation=panel_degradation, om_pct=om_pct,
        autoconsumo_frac=af, lid_pct=lid_pct,
        inv_replace_year=inv_replace_year, inv_replace_pct=inv_replace_pct,
        inv_replace_mxn=inv_replace_mxn, inv_replace_esc=inv_replace_esc,
        isr_pct=isr_pct, deduccion_art34=deduccion_art34,
        escudo_inmediato=escudo_inmediato, seguro_pct=seguro_pct,
        con_deuda=con_deuda, deuda_pct=deuda_pct,
        tasa_deuda_pct=tasa_deuda_pct, plazo_deuda_tk=plazo_deuda_tk,
    )


@st.cache_data(show_spinner=False)
def calc_ppa_result(gen1: float, inv_usd: float, precio_ppa: float,
                    plazo: int, wacc_pct: float, esc_ppa: float,
                    deg: float, om_pct: float, inf_om: float,
                    seg_pct: float, usd_mx: float, equity_pct: float,
                    tasa_deuda: float, plazo_deuda: int, con_fin: bool,
                    vida_util_total: int = 25,
                    descuento_pct: float | None = None,
                    dimensionar_por_dscr: bool = False,
                    dscr_objetivo: float = 1.30,
                    lid_pct: float = 1.5,
                    descuento_merchant: float = 30.0,
                    perfil_esculpido: bool = False,
                    disponibilidad: float = 1.0,
                    inv_replace_year: int = 0,
                    inv_replace_mxn: float = 0.0,
                    inv_replace_esc: float = 0.0,
                    isr_pct: float = 0.0,
                    deduccion_art34: bool = False,
                    escudo_inmediato: bool = True,
                    ke_dinamico: bool = True,
                    dsra_meses: float = 0.0) -> dict:
    """Resultado financiero PPA para un plazo dado — perspectiva equity.

    Los flujos fn_y son flujos de caja al accionista (FCFE): ingresos PPA menos
    O&M, seguro y servicio de deuda. El VPN y el payback descontado se calculan
    usando el costo del equity (Ke), no el WACC, para mantener consistencia entre
    la tasa de descuento y los flujos que se descuentan.

    Ke se estima con el modelo MM sin impuestos (Modigliani-Miller):
        Ke = WACC + (D/E) * (WACC - Kd)
    Cuando no hay financiamiento (con_fin=False o deuda=0), Ke = WACC.

    descuento_pct: tasa de descuento explícita (% anual) para fd_y y el valor
        residual. Si es None se usa Ke.

        FIX — antes, para evaluar contra un hurdle rate, se inyectaba
        (WACC + spread) en el parámetro wacc_pct. Eso no sólo cambiaba la tasa
        de descuento: también re-apalancaba Ke, porque wacc_pct alimenta la
        fórmula Ke = WACC + (D/E)(WACC - Kd). Con estructura 70/30 un spread de
        4 puntos inflaba Ke ~13 puntos y castigaba el VPN ~35 % en vez del ~11 %
        que corresponde. Ahora el hurdle se pasa por aquí y Ke queda intacto.

    vida_util_total: vida útil del sistema (años). Se usa para calcular el valor
    residual al final del contrato PPA si plazo < vida_util_total.

    dimensionar_por_dscr: si True, la deuda se dimensiona por cobertura en vez de
        fijarse con equity_pct. Es como opera el project finance real: el banco
        calcula el CFADS del proyecto, lo divide entre el DSCR objetivo para
        obtener el servicio de deuda máximo sostenible, y de ahí despeja el
        principal. El equity es el RESULTADO (CAPEX − deuda), no un input.
    dscr_objetivo: cobertura mínima exigida. Solar contratado suele pedir
        1.20–1.35x; 1.30x es el valor de trabajo.
    lid_pct: pérdida de primer año (LID/LeTID). Antes el PPA arrancaba el año 1
        al 100 % de placa mientras Turnkey ya descontaba el escalón inicial:
        mismo activo, dos supuestos de generación.
    perfil_esculpido: si True, el servicio de deuda se modela año a año sobre el
        CFADS para mantener el DSCR constante en el objetivo (sculpted). Libera más
        deuda que la anualidad plana cuando el CFADS crece con el escalador del PPA.
    disponibilidad: fracción de tiempo operativa (1.0 = neutro, ya dentro del PR).
    inv_replace_year / inv_replace_mxn / inv_replace_esc: reposición del inversor.
        En un PPA el DUEÑO del sistema es el desarrollador, así que la reposición
        es suya. Turnkey ya la modelaba y PPA no: con reposición de ~$236k en el
        año 12 el valor presente ronda el 25 % del VPN del proyecto.
    isr_pct / deduccion_art34 / escudo_inmediato: modelo fiscal, idéntico al de
        calc_financial_model. El desarrollador PPA paga ISR sobre el ingreso del
        contrato y el Art. 34 LISR le aplica igual que a un cliente turnkey.
    ke_dinamico: si True, Ke se recalcula cada año con el D/E vigente. La deuda
        amortiza, así que el apalancamiento cae; mantener el Ke del año 1 durante
        todo el plazo sobre-descuenta los años tardíos (con 70/30 son ~8 puntos
        de más a partir del vencimiento del crédito).
    dsra_meses: meses de servicio de deuda retenidos en la cuenta de reserva.
        Sale del flujo al inicio y se libera al último pago.
    descuento_merchant: castigo (%) sobre el último precio contratado para valorar
        la energía post-contrato. Al vencer el PPA el activo pasa a mercado o a
        renegociación, no conserva el precio contractual escalado.
    """
    inv_mxn = inv_usd * usd_mx
    r_d     = (tasa_deuda / 100) if tasa_deuda > 0 else 0.0

    def _anualidad(principal, tasa, n):
        """Servicio de deuda constante (amortización francesa)."""
        if principal <= 0 or n <= 0:
            return 0.0
        if tasa <= 0:
            return principal / n
        return principal * tasa / (1 - (1 + tasa) ** (-n))

    def _principal_desde_servicio(servicio, tasa, n):
        """Inverso de la anualidad: principal que soporta un servicio dado."""
        if servicio <= 0 or n <= 0:
            return 0.0
        if tasa <= 0:
            return servicio * n
        return servicio * (1 - (1 + tasa) ** (-n)) / tasa

    r = wacc_pct / 100   # WACC — referencia y base del Ke

    # ── Costo del equity (Ke) ─────────────────────────────────────────────────
    # ── Flujo operativo antes de deuda (CFADS) ───────────────────────────────
    # CFADS = Cash Flow Available for Debt Service. Es la magnitud que el banco
    # evalúa: ingreso del PPA menos costos operativos, antes del servicio de deuda.
    years  = list(range(1, plazo + 1))
    _lidf  = 1 - lid_pct / 100      # FIX S4 — escalón LID, ausente antes en el PPA
    _disp  = max(0.0, min(1.0, disponibilidad))
    gen_y  = [gen1 * _lidf * _disp * (1 - deg / 100) ** i for i in range(plazo)]
    prec_y = [precio_ppa * (1 + esc_ppa / 100) ** i for i in range(plazo)]
    ing_y  = [gen_y[i] * prec_y[i] for i in range(plazo)]
    om_y   = [inv_mxn * om_pct  / 100 * (1 + inf_om / 100) ** i for i in range(plazo)]
    seg_y  = [inv_mxn * seg_pct / 100 * (1 + inf_om / 100) ** i for i in range(plazo)]

    # Reposición del inversor — el dueño del sistema es el desarrollador.
    capex_rep_y = [0.0] * plazo
    if inv_replace_year and 1 <= inv_replace_year <= plazo and inv_replace_mxn > 0:
        _ir = inv_replace_year - 1
        capex_rep_y[_ir] = inv_replace_mxn * (1 + inv_replace_esc / 100) ** _ir

    # CFADS = flujo operativo antes de deuda. La reposición NO entra aquí: el
    # banco evalúa la capacidad operativa de pago y la reposición se financia
    # aparte o con reservas. Sí entra en el flujo al accionista.
    cfads_y = [ing_y[i] - om_y[i] - seg_y[i] for i in range(plazo)]

    # ── Estructura de capital ────────────────────────────────────────────────
    _n_deuda = min(plazo_deuda, plazo) if plazo_deuda > 0 else 0
    if not con_fin or r_d <= 0 or _n_deuda <= 0:
        deuda_mxn = 0.0
        serv_deuda = 0.0
        serv_deuda_y_ppa = None
        equity_mxn = inv_mxn
        metodo_deuda = "Sin financiamiento"
    elif dimensionar_por_dscr and perfil_esculpido:
        # Amortización ESCULPIDA (sculpted). El servicio de cada año se modela
        # sobre el CFADS de ese año para mantener el DSCR exactamente en el
        # objetivo durante toda la vida del crédito:
        #
        #     servicio_t = CFADS_t / DSCR_objetivo
        #     principal  = Σ servicio_t / (1 + Kd)^t
        #
        # Es la práctica estándar en project finance de renovables. Frente a la
        # anualidad constante libera más deuda: con generación degradante y precio
        # escalando, el CFADS crece, y una anualidad plana desperdicia esa holgura
        # (el DSCR sube muy por encima del objetivo en los años tardíos).
        _serv_scul = [max(0.0, cfads_y[i] / dscr_objetivo) for i in range(_n_deuda)]
        deuda_mxn  = sum(_serv_scul[i] / (1 + r_d) ** (i + 1) for i in range(_n_deuda))
        if deuda_mxn > inv_mxn:
            # El proyecto soportaría más deuda que el CAPEX: se recorta y el perfil
            # se reescala proporcionalmente para no sobrefinanciar.
            _k = inv_mxn / deuda_mxn
            _serv_scul = [v * _k for v in _serv_scul]
            deuda_mxn = inv_mxn
        serv_deuda_y_ppa = _serv_scul + [0.0] * (plazo - _n_deuda)
        serv_deuda = _serv_scul[0] if _serv_scul else 0.0
        equity_mxn = inv_mxn - deuda_mxn
        metodo_deuda = f"Esculpida a DSCR {dscr_objetivo:.2f}x constante"
    elif dimensionar_por_dscr:
        # FIX S1 — dimensionamiento por cobertura (práctica de project finance).
        # El servicio sostenible lo fija el año MÁS DÉBIL del periodo de crédito:
        #     servicio_max = min(CFADS_t) / DSCR_objetivo
        # y de ahí se despeja el principal con la anualidad inversa. El equity
        # sale por diferencia. Antes se hacía al revés: se fijaba el equity y el
        # servicio caía donde cayera, sin verificar que el proyecto lo aguantara.
        _cfads_periodo = cfads_y[:_n_deuda]
        _serv_max = (min(_cfads_periodo) / dscr_objetivo) if _cfads_periodo else 0.0
        _serv_max = max(0.0, _serv_max)
        deuda_mxn = _principal_desde_servicio(_serv_max, r_d, _n_deuda)
        deuda_mxn = min(deuda_mxn, inv_mxn)          # nunca más que el CAPEX
        serv_deuda = _anualidad(deuda_mxn, r_d, _n_deuda)
        serv_deuda_y_ppa = None
        equity_mxn = inv_mxn - deuda_mxn
        metodo_deuda = f"Anualidad constante · DSCR ≥ {dscr_objetivo:.2f}x"
    else:
        equity_mxn = inv_mxn * (equity_pct / 100)
        deuda_mxn  = inv_mxn - equity_mxn
        serv_deuda = _anualidad(deuda_mxn, r_d, _n_deuda)
        serv_deuda_y_ppa = None
        metodo_deuda = f"Equity fijo {equity_pct:.0f}%"
        if deuda_mxn <= 0:
            deuda_mxn = 0.0; serv_deuda = 0.0; equity_mxn = inv_mxn

    if serv_deuda_y_ppa is not None:
        deu_y = list(serv_deuda_y_ppa[:plazo]) + [0.0] * max(0, plazo - len(serv_deuda_y_ppa))
    else:
        deu_y = [serv_deuda if y <= _n_deuda else 0.0 for y in years]
    # ── Interés y capital, para el escudo fiscal ─────────────────────────────
    # El interés es gasto deducible; la amortización de capital no.
    interes_y = [0.0] * plazo
    capital_y = [0.0] * plazo
    _saldo = deuda_mxn
    for i in range(plazo):
        if deu_y[i] > 0 and _saldo > 0:
            _int = _saldo * r_d
            _cap = min(deu_y[i] - _int, _saldo)
            interes_y[i] = _int
            capital_y[i] = max(0.0, _cap)
            _saldo -= capital_y[i]

    # ── Impuestos ────────────────────────────────────────────────────────────
    # El desarrollador PPA es contribuyente: paga ISR sobre el ingreso del
    # contrato, y el Art. 34 LISR le aplica igual que a un cliente turnkey.
    t = max(0.0, isr_pct / 100)
    if t > 0:
        if deduccion_art34:
            depreciacion_y = [inv_mxn] + [0.0] * (plazo - 1)
        else:
            depreciacion_y = [inv_mxn / vida_util_total] * plazo
        for i in range(plazo):
            if capex_rep_y[i] > 0:
                if deduccion_art34:
                    depreciacion_y[i] += capex_rep_y[i]
                else:
                    _rest = max(1, plazo - i)
                    for k in range(i, plazo):
                        depreciacion_y[k] += capex_rep_y[i] / _rest
        base_grav_y = [ing_y[i] - om_y[i] - seg_y[i] - interes_y[i] - depreciacion_y[i]
                       for i in range(plazo)]
        if escudo_inmediato:
            impuestos_y = [base_grav_y[i] * t for i in range(plazo)]
        else:
            impuestos_y = []; _pf = 0.0
            for i in range(plazo):
                _b = base_grav_y[i]
                if _b < 0:
                    _pf += -_b; impuestos_y.append(0.0)
                else:
                    _ap = min(_pf, _b); _pf -= _ap
                    impuestos_y.append((_b - _ap) * t)
    else:
        depreciacion_y = [0.0] * plazo
        impuestos_y    = [0.0] * plazo

    # ── DSRA (cuenta de reserva de servicio de deuda) ─────────────────────────
    # Se funda al inicio con N meses de servicio y se libera al último pago.
    # Es capital inmovilizado: sale del bolsillo del accionista el año 0.
    dsra_monto = (deu_y[0] * dsra_meses / 12) if (dsra_meses > 0 and deu_y and deu_y[0] > 0) else 0.0
    dsra_y = [0.0] * plazo
    if dsra_monto > 0 and _n_deuda >= 1:
        dsra_y[_n_deuda - 1] += dsra_monto      # se libera al terminar la deuda

    # ── Flujo al accionista (FCFE) ───────────────────────────────────────────
    fn_y  = [cfads_y[i] - deu_y[i] - capex_rep_y[i] - impuestos_y[i] + dsra_y[i]
             for i in range(plazo)]

    # ── Cobertura: DSCR año a año y LLCR ─────────────────────────────────────
    dscr_y = [(cfads_y[i] / deu_y[i]) if deu_y[i] > 0 else None for i in range(plazo)]
    _dv    = [d for d in dscr_y if d is not None]
    dscr_min  = min(_dv) if _dv else None
    dscr_prom = (sum(_dv) / len(_dv)) if _dv else None

    # LLCR = VP(CFADS durante la vida del crédito) / saldo de deuda.
    # Se descuenta al costo de la deuda, que es la convención de la banca.
    if deuda_mxn > 0 and _n_deuda > 0:
        _pv_cfads = sum(cfads_y[i] / (1 + r_d) ** (i + 1) for i in range(_n_deuda))
        llcr = _pv_cfads / deuda_mxn
    else:
        llcr = None

    # ── Costo del equity (Ke) ────────────────────────────────────────────────
    # fn_y son flujos post-deuda (FCFE). Deben descontarse con Ke, no con WACC.
    # Ke = WACC + (D/E) * (WACC - Kd)  [MM sin impuestos]
    def _ke_de(saldo_deuda):
        """Ke para un saldo de deuda dado (MM Prop. II sin impuestos)."""
        _e = inv_mxn - saldo_deuda
        if _e <= 0 or saldo_deuda <= 0 or r <= 0:
            return r
        _k = r + (saldo_deuda / _e) * (r - r_d)
        return max(r, min(_k, 3 * r))      # cota contra apalancamientos extremos

    ke = _ke_de(deuda_mxn)                  # Ke del año 1, para reporte

    # ── Ke DINÁMICO ──────────────────────────────────────────────────────────
    # La deuda amortiza, así que el apalancamiento cae año con año y con él el
    # riesgo del accionista. Mantener el Ke del año 1 durante todo el plazo
    # sobre-descuenta los años tardíos: con estructura 70/30 se seguían
    # descontando al 23 % flujos de años en que ya no había deuda y el Ke real
    # era el desapalancado (15 %).
    saldo_ini = [0.0] * plazo
    _s = deuda_mxn
    for i in range(plazo):
        saldo_ini[i] = _s
        _s = max(0.0, _s - capital_y[i])
    ke_y = [_ke_de(saldo_ini[i]) for i in range(plazo)]

    # Tasa de descuento efectiva. Si se pasa un hurdle explícito se respeta tal
    # cual (es una exigencia del inversionista, no una derivada del riesgo).
    if descuento_pct is not None:
        disc   = descuento_pct / 100
        disc_y = [disc] * plazo
    elif ke_dinamico:
        disc   = ke                       # referencia para el residual y reporte
        disc_y = ke_y
    else:
        disc   = ke
        disc_y = [ke] * plazo

    # Factor de descuento acumulado: se compone el Ke de cada año en vez de
    # elevar una sola tasa a la potencia del año.
    _acum = 1.0
    factor_desc_y = []
    for i in range(plazo):
        _acum *= (1 + disc_y[i])
        factor_desc_y.append(1.0 / _acum)
    fd_y = [fn_y[i] * factor_desc_y[i] for i in range(plazo)]

    # Valor residual del sistema al final del contrato PPA
    # Si el contrato es más corto que la vida útil, el activo sigue generando valor.
    # Se estima como VPN de los flujos futuros post-contrato usando una anuidad con
    # crecimiento (fórmula de Gordon) que incorpora tanto el escalador PPA como la
    # degradación anual del panel — evita sobreestimar el valor al asumir flujo constante.
    anios_restantes = max(0, vida_util_total - plazo)
    disc_res = (descuento_pct / 100) if descuento_pct is not None else r
    if anios_restantes > 0 and disc_res > 0:
        gen_post  = gen_y[-1] * (1 - deg / 100)       # generación año plazo+1
        # FIX S3 — al vencer el contrato ya NO existe el precio PPA. Valorar la
        # energía post-contrato al precio contractual escalado sobreestimaba el
        # residual: con $1.80 inicial y escalador 3.5 %, el año 11 quedaba a
        # $2.54/kWh, un precio que expiró. Se aplica un descuento de mercado sobre
        # el último precio contratado para reflejar renegociación o merchant.
        prec_post = prec_y[-1] * (1 + esc_ppa / 100) * (1 - descuento_merchant / 100)
        om_post   = om_y[-1]  * (1 + inf_om / 100)    # O&M escalado
        seg_post  = seg_y[-1] * (1 + inf_om / 100)

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

        # El valor residual usa la misma tasa que fd_y (`disc`), para que la
        # etiqueta que se muestra al usuario y la matemática coincidan.
        # Al vencer el contrato la deuda ya está amortizada, así que el activo es
        # 100 % equity y la tasa correcta es la DESAPALANCADA, no el Ke del año 1.
        # Si hay hurdle explícito se respeta, porque es una exigencia del inversor.
        pv_ingresos = _gordon_pv(gen_post * prec_post, g_ingreso, anios_restantes, disc_res)
        pv_costos   = _gordon_pv(om_post + seg_post,   g_costos,  anios_restantes, disc_res)
        # _gordon_pv devuelve el VPN de los flujos post-contrato al instante t=0
        # suponiendo que el primer flujo cae en t=1. Como los flujos post-contrato
        # empiezan en t=plazo+1, se descuenta `plazo` períodos adicionales.
        # Se trae a hoy con el factor acumulado de los años del contrato.
        valor_residual = (pv_ingresos - pv_costos) * factor_desc_y[-1]
    else:
        valor_residual = 0.0

    # El accionista desembolsa el equity MÁS la DSRA que queda inmovilizada.
    desembolso_equity = equity_mxn + dsra_monto
    vpn = -desembolso_equity + sum(fd_y) + valor_residual

    # TIR — con verificación de unicidad; cae a MIRR si hay múltiples raíces
    # (ocurre cuando el servicio de deuda supera el ingreso en los primeros años).
    tir, tir_metodo = _irr_robusta([-desembolso_equity] + fn_y,
                                   finance_rate=disc, reinvest_rate=disc)

    # Payback simple — acumulado sobre flujos nominales
    pb = None
    acum_pb = -desembolso_equity
    for i, fn in enumerate(fn_y):
        prev_acum = acum_pb
        acum_pb  += fn
        if acum_pb >= 0:
            pb = round(years[i] - 1 + (-prev_acum) / (acum_pb - prev_acum), 1)
            break

    # Payback descontado — acumulado sobre flujos descontados (fd_y)
    pb_disc = None
    acum_disc = -desembolso_equity
    for i, fd in enumerate(fd_y):
        prev_disc = acum_disc
        acum_disc += fd
        if acum_disc >= 0:
            pb_disc = round(years[i] - 1 + (-prev_disc) / (acum_disc - prev_disc), 1)
            break

    return dict(vpn=vpn, tir=tir, tir_metodo=tir_metodo,
                pb=pb, pb_disc=pb_disc, ing_total=sum(ing_y),
                fn_y=fn_y, fd_y=fd_y, ing_y=ing_y, om_y=om_y,
                seg_y=seg_y, gen_y=gen_y, prec_y=prec_y, deu_y=deu_y,
                cfads_y=cfads_y,
                equity_mxn=equity_mxn, deuda_mxn=deuda_mxn, inv_mxn=inv_mxn,
                desembolso_equity=desembolso_equity, dsra_monto=dsra_monto,
                capex_rep_y=capex_rep_y, impuestos_y=impuestos_y,
                depreciacion_y=depreciacion_y, interes_y=interes_y,
                capital_y=capital_y, ke_y=[k * 100 for k in ke_y],
                factor_desc_y=factor_desc_y, disponibilidad=_disp,
                serv_deuda=serv_deuda, plazo_deuda_eff=_n_deuda,
                metodo_deuda=metodo_deuda, esculpido=bool(serv_deuda_y_ppa is not None),
                # ── Cobertura (project finance) ──────────────────────────────
                dscr_y=dscr_y, dscr_min=dscr_min, dscr_prom=dscr_prom,
                dscr_objetivo=dscr_objetivo, llcr=llcr,
                apalancamiento=(deuda_mxn / inv_mxn * 100) if inv_mxn > 0 else 0.0,
                years=years,
                valor_residual=valor_residual,
                ke_pct=ke * 100,          # Ke derivado del WACC y la estructura (% anual)
                disc_pct=disc * 100,      # tasa efectivamente usada para descontar (% anual)
                wacc_pct=wacc_pct)        # WACC de referencia del usuario (%)


@st.cache_data(show_spinner=False)
def calc_precio_minimo(gen1: float, inv_usd: float, plazo: int,
                       wacc_pct: float, esc_ppa: float, deg: float,
                       om_pct: float, inf_om: float, seg_pct: float,
                       usd_mx: float, equity_pct: float,
                       tasa_deuda: float, plazo_deuda: int, con_fin: bool,
                       vida_util_total: int = 25,
                       descuento_pct: float | None = None,
                       dimensionar_por_dscr: bool = False,
                       dscr_objetivo: float = 1.30,
                       lid_pct: float = 1.5,
                       descuento_merchant: float = 30.0,
                       perfil_esculpido: bool = False,
                       disponibilidad: float = 1.0,
                       inv_replace_year: int = 0,
                       inv_replace_mxn: float = 0.0,
                       inv_replace_esc: float = 0.0,
                       isr_pct: float = 0.0,
                       deduccion_art34: bool = False,
                       escudo_inmediato: bool = True,
                       ke_dinamico: bool = True,
                       dsra_meses: float = 0.0):
    """Precio mínimo PPA (VPN=0) por bisección. Cacheado."""
    lo, hi = 0.01, 20.0
    def vpn_at(p):
        return calc_ppa_result(gen1, inv_usd, p, plazo, wacc_pct, esc_ppa,
                               deg, om_pct, inf_om, seg_pct, usd_mx,
                               equity_pct, tasa_deuda, plazo_deuda, con_fin,
                               vida_util_total, descuento_pct,
                               dimensionar_por_dscr, dscr_objetivo,
                               lid_pct, descuento_merchant, perfil_esculpido,
                               disponibilidad, inv_replace_year, inv_replace_mxn,
                               inv_replace_esc, isr_pct, deduccion_art34,
                               escudo_inmediato, ke_dinamico, dsra_meses)["vpn"]
    if vpn_at(hi) < 0: return None
    for _ in range(80):
        mid = (lo+hi)/2
        if vpn_at(mid) >= 0: hi = mid
        else: lo = mid
    return round((lo+hi)/2, 4)

@st.cache_data(show_spinner=False)

# ═════════════════════════════════════════════════════════════════════════════
# ANÁLISIS DEL COMPRADOR — comparación de modalidades
# ═════════════════════════════════════════════════════════════════════════════
# Todo el modelo financiero previo mira el proyecto desde el lado del
# DESARROLLADOR: VPN, TIR de equity, DSCR, LLCR. Eso responde "¿me conviene
# construirlo?". El comprador industrial tiene una pregunta distinta y nadie se
# la contesta: "¿me conviene comprarlo, contratarlo, o no hacer nada?".
#
# Las tres opciones entregan EL MISMO SERVICIO — la misma energía — así que la
# forma correcta de compararlas no es por ahorro sino por COSTO. Se pone cada
# modalidad sobre el mismo horizonte y la misma curva de generación, se
# descuenta al costo de capital del comprador, y gana la de menor valor
# presente. El ahorro anual, que es lo único que suele mostrar una propuesta de
# PPA, puede favorecer a la opción que destruye más valor.
#
# Tres decisiones de modelado que cambian el resultado y que aquí van explícitas
# en vez de escondidas:
#
#   1. HORIZONTE COMÚN. Un PPA a 15 años y un sistema propio de 25 no se comparan
#      en sus propios plazos. Se comparan a 25. Lo que pase en los años 16–25 es
#      un supuesto contractual, no un detalle: si el activo se transfiere al
#      cliente, esos años son casi gratis; si el cliente vuelve a la red, son
#      años de tarifa CFE completa. La diferencia entre ambos supuestos suele
#      ser mayor que todo el ahorro del contrato.
#
#   2. BASE DESPUÉS DE IMPUESTOS. El pago a CFE y el pago del PPA son gasto
#      deducible; el CAPEX del sistema propio también lo es, y bajo el Art. 34
#      LISR al 100 % en el primer año. Comparar antes de impuestos infla
#      sistemáticamente el atractivo del PPA porque le quita al sistema propio
#      su ventaja fiscal más grande.
#
#   3. TIR INCREMENTAL, no TIR de cada opción. La pregunta no es "¿qué TIR da el
#      sistema propio?" sino "¿qué rendimiento obtengo por el CAPEX adicional que
#      pongo al comprar en vez de contratar?". Ese es el número que decide.
# ─────────────────────────────────────────────────────────────────────────────


def _serie_generacion(gen_anio1: float, degradacion_pct: float,
                      lid_pct: float, n: int) -> list:
    """Generación año a año con escalón LID el primer año y degradación lineal-compuesta."""
    g0 = gen_anio1 * (1.0 - lid_pct / 100.0)
    return [g0 * (1.0 - degradacion_pct / 100.0) ** i for i in range(n)]


def _amortizacion_francesa(principal: float, tasa_pct: float, plazo: int, n: int) -> list:
    """Servicio de deuda constante durante `plazo` años, cero después."""
    if principal <= 0 or plazo <= 0:
        return [0.0] * n
    r = tasa_pct / 100.0
    if r <= 0:
        cuota = principal / plazo
    else:
        cuota = principal * r / (1.0 - (1.0 + r) ** (-plazo))
    return [cuota if i < plazo else 0.0 for i in range(n)]


def _vp(flujos: list, tasa_pct: float) -> float:
    """Valor presente a fin de año. El año 1 se descuenta un periodo."""
    r = tasa_pct / 100.0
    return sum(f / (1.0 + r) ** (i + 1) for i, f in enumerate(flujos))


def analisis_comprador(
    gen_anio1: float,
    tarifa_cfe: float,
    inflacion_cfe: float,
    precio_ppa: float,
    escalador_ppa: float,
    plazo_ppa: int,
    capex_mxn: float,
    *,
    horizonte: int = 25,
    degradacion_pct: float = 0.5,
    lid_pct: float = 1.0,
    om_pct: float = 1.7,
    seguros_pct: float = 0.5,
    inflacion_om: float = 4.0,
    tasa_descuento: float = 12.0,
    isr_pct: float = 30.0,
    aplicar_isr: bool = True,
    deduccion_art34: bool = True,
    reemplazo_anio: int = 0,
    reemplazo_mxn: float = 0.0,
    deuda_pct: float = 0.0,
    tasa_deuda: float = 13.0,
    plazo_deuda: int = 7,
    ppa_transfiere_activo: bool = True,
    autoconsumo_frac: float = 1.0,
) -> dict:
    """
    Compara cuatro modalidades sobre el mismo horizonte y la misma energía.

    Devuelve un dict con, para cada opción, el flujo de costo año a año, su
    valor presente, el costo nivelado (LCOE) y el desembolso inicial; más los
    indicadores incrementales que resuelven la decisión.

    Convención de signos: TODO son COSTOS positivos. Menor es mejor.
    """
    n     = max(1, int(horizonte))
    isr   = (isr_pct / 100.0) if aplicar_isr else 0.0
    esc_c = 1.0 + inflacion_cfe / 100.0
    esc_p = 1.0 + escalador_ppa / 100.0
    esc_o = 1.0 + inflacion_om / 100.0
    ac    = max(0.0, min(1.0, autoconsumo_frac))

    gen   = _serie_generacion(gen_anio1, degradacion_pct, lid_pct, n)
    # Solo la energía autoconsumida desplaza tarifa. El excedente, bajo net
    # metering, se acredita a un valor menor; asumirlo al 100 % de la tarifa es
    # el error más común en una propuesta comercial.
    gen_util = [g * ac for g in gen]
    cfe_p = [tarifa_cfe * esc_c ** i for i in range(n)]
    ppa_p = [precio_ppa * esc_p ** i for i in range(n)]

    # ── A · No hacer nada ────────────────────────────────────────────────────
    # Comprar de la red toda la energía. Es gasto deducible.
    c_nada = [gen_util[i] * cfe_p[i] * (1.0 - isr) for i in range(n)]

    # ── B · Turnkey de contado ───────────────────────────────────────────────
    om_base = capex_mxn * (om_pct + seguros_pct) / 100.0
    c_om    = [om_base * esc_o ** i * (1.0 - isr) for i in range(n)]
    if 0 < reemplazo_anio <= n and reemplazo_mxn > 0:
        c_om[reemplazo_anio - 1] += reemplazo_mxn * esc_o ** (reemplazo_anio - 1) * (1.0 - isr)

    # Escudo fiscal del CAPEX. El Art. 34 LISR permite deducir al 100 % en el
    # ejercicio la inversión en equipo de generación con fuentes renovables,
    # siempre que se mantenga en operación cinco años. Vale solo si hay utilidad
    # fiscal contra la cual aplicarlo — de ahí el interruptor.
    escudo_capex = capex_mxn * isr if (aplicar_isr and deduccion_art34) else 0.0
    c_tk = list(c_om)
    if escudo_capex > 0:
        c_tk[0] -= escudo_capex          # se materializa al cierre del ejercicio 1

    # ── C · Turnkey financiado ───────────────────────────────────────────────
    deuda    = capex_mxn * max(0.0, min(1.0, deuda_pct / 100.0))
    equity   = capex_mxn - deuda
    serv     = _amortizacion_francesa(deuda, tasa_deuda, int(plazo_deuda), n)
    # El interés es deducible; el capital no.
    saldo, c_fin = deuda, []
    for i in range(n):
        interes = saldo * (tasa_deuda / 100.0) if saldo > 0 and serv[i] > 0 else 0.0
        capital = max(0.0, serv[i] - interes)
        saldo   = max(0.0, saldo - capital)
        c_fin.append(capital + interes * (1.0 - isr))
    c_tkf = [c_om[i] + c_fin[i] for i in range(n)]
    if escudo_capex > 0:
        c_tkf[0] -= escudo_capex

    # ── D · PPA ──────────────────────────────────────────────────────────────
    c_ppa = []
    for i in range(n):
        if i < plazo_ppa:
            c_ppa.append(gen_util[i] * ppa_p[i] * (1.0 - isr))
        elif ppa_transfiere_activo:
            # El activo pasa al cliente: solo queda operarlo.
            c_ppa.append(om_base * esc_o ** i * (1.0 - isr))
        else:
            # Sin transferencia, el cliente vuelve a comprar de la red.
            c_ppa.append(gen_util[i] * cfe_p[i] * (1.0 - isr))

    # ── Valores presentes y costo nivelado ───────────────────────────────────
    # El LCOE se calcula con energía DESCONTADA, no con energía nominal: ambos
    # lados de la razón tienen que estar en la misma unidad temporal.
    vp_energia = _vp(gen_util, tasa_descuento)

    def _pack(flujo, desembolso):
        vp_c = _vp(flujo, tasa_descuento) + desembolso
        return {"flujo": flujo,
                "desembolso": desembolso,
                "vp": vp_c,
                "lcoe": (vp_c / vp_energia) if vp_energia > 0 else 0.0}

    op = {
        "nada": _pack(c_nada, 0.0),
        "tk":   _pack(c_tk,   capex_mxn),
        "tkf":  _pack(c_tkf,  equity),
        "ppa":  _pack(c_ppa,  0.0),
    }
    for k in op:
        op[k]["ahorro_vp"] = op["nada"]["vp"] - op[k]["vp"]

    # ── Decisión incremental: comprar en vez de contratar ────────────────────
    # Flujo = lo que dejas de pagar al desarrollador menos lo que te cuesta operar.
    inc      = [c_ppa[i] - c_tk[i] for i in range(n)]
    flujo_inc = [-capex_mxn] + inc
    vpn_inc   = -capex_mxn + _vp(inc, tasa_descuento)
    # _irr_robusta devuelve (valor_en_%, método). El método importa: con
    # reemplazo de inversor o servicio de deuda el flujo cambia de signo más de
    # una vez y lo que se reporta es MIRR, no TIR.
    tir_inc, tir_metodo = _irr_robusta(flujo_inc, tasa_descuento / 100.0,
                                       tasa_descuento / 100.0)

    # Tasa de indiferencia: el costo de capital al que ambas opciones empatan.
    # Por encima de ella el PPA gana; por debajo, comprar. Es más robusta que la
    # TIR cuando el flujo incremental cambia de signo más de una vez.
    lo, hi = 0.0, 100.0
    def _vpn_a(t):
        return -capex_mxn + sum(inc[i] / (1.0 + t / 100.0) ** (i + 1) for i in range(n))
    tasa_indif = None
    if _vpn_a(lo) > 0 > _vpn_a(hi):
        for _ in range(200):
            mid = (lo + hi) / 2.0
            if _vpn_a(mid) > 0: lo = mid
            else:               hi = mid
        tasa_indif = (lo + hi) / 2.0

    # ── Año de cruce PPA vs CFE ──────────────────────────────────────────────
    # Si el escalador del PPA supera la inflación tarifaria, existe un año en que
    # el PPA se vuelve MÁS CARO que la red. Ninguna propuesta comercial lo grafica
    # porque cae fuera del plazo que se está vendiendo.
    cruce = None
    for i in range(n):
        if ppa_p[i] > cfe_p[i]:
            cruce = i + 1
            break
    # Cruce teórico aunque caiga fuera del horizonte — sirve para saber si el
    # contrato está estructurado para envejecer bien.
    cruce_teorico = None
    if escalador_ppa > inflacion_cfe and precio_ppa < tarifa_cfe:
        try:
            cruce_teorico = math.log(tarifa_cfe / precio_ppa) / (
                math.log(esc_p) - math.log(esc_c)) + 1
        except (ValueError, ZeroDivisionError):
            cruce_teorico = None

    # ── Ranking ──────────────────────────────────────────────────────────────
    etiquetas = {"nada": "No hacer nada", "tk": "Turnkey de contado",
                 "tkf": "Turnkey financiado", "ppa": f"PPA {plazo_ppa} años"}
    orden = sorted(op.keys(), key=lambda k: op[k]["vp"])

    return {
        "n": n,
        "gen": gen, "gen_util": gen_util,
        "cfe_precio": cfe_p, "ppa_precio": ppa_p,
        "opciones": op, "etiquetas": etiquetas, "orden": orden,
        "mejor": orden[0],
        "vp_energia": vp_energia,
        "vpn_incremental": vpn_inc,
        "tir_incremental": tir_inc,          # en %, no en decimal
        "tir_metodo": tir_metodo,
        "tasa_indiferencia": tasa_indif,
        "flujo_incremental": flujo_inc,
        "cruce_ppa_cfe": cruce,
        "cruce_teorico": cruce_teorico,
        "escudo_capex": escudo_capex,
        "equity_financiado": equity,
        "supuestos": {
            "horizonte": n, "isr_aplicado": aplicar_isr, "isr_pct": isr_pct,
            "art34": deduccion_art34, "transfiere": ppa_transfiere_activo,
            "tasa_descuento": tasa_descuento, "autoconsumo": ac,
        },
    }



# ═════════════════════════════════════════════════════════════════════════════
# HERRAMIENTAS DEL COMPRADOR — solicitud de cotización y normalización
# ═════════════════════════════════════════════════════════════════════════════
# El problema que resuelve esta sección no es técnico, es de asimetría de
# información. El comprador industrial recibe tres propuestas que no se pueden
# comparar: una cotiza 300 kWp y otra 285; una promete 1,850 kWh/kWp y otra
# 1,520; una incluye O&M cinco años y otra no lo menciona. Sin una base común,
# la decisión termina tomándose por precio total, que es exactamente el criterio
# que premia a quien recortó calidad o infló la generación.
#
# Dos piezas: una solicitud que obliga a todos a responder sobre la misma base,
# y una hoja que traduce las respuestas a un solo número comparable.
# ─────────────────────────────────────────────────────────────────────────────

# Umbrales de verificación. Cada uno tiene una razón física o de mercado, no son
# preferencias. Se documentan porque un comprador debe poder discutirlos.
# Banda observada en arreglos coplanares o de baja inclinación, que es como
# está montada la mayoría de la GD industrial mexicana. Si la propuesta declara
# inclinación, la banda se escala por el factor de transposición antes de juzgar
# —de otro modo se penalizaría a quien sí va a inclinar el arreglo.
RANGO_RENDIMIENTO_MX   = (1350.0, 1800.0)   # kWh/kWp/año, base coplanar
RANGO_PR_POA           = (0.72, 0.86)
RANGO_DEGRADACION      = (0.40, 0.70)       # %/año, garantías mono-Si actuales
RANGO_DC_AC            = (1.00, 1.45)
RANGO_COSTO_USD_WP     = (0.55, 1.30)       # llave en mano, GD industrial México


def hipotesis_obligatorias() -> list:
    """
    Lo que todo licitante debe declarar para que su número de generación sea
    auditable. Cada punto trae el porqué: el comprador tiene que entender qué
    está pidiendo, no solo copiarlo.
    """
    return [
        ("Fuente y periodo del recurso solar",
         "Base de datos (NASA POWER, Meteonorm, SolarGIS, PVGIS, estación en sitio) "
         "y años cubiertos. Dos bases distintas sobre el mismo sitio difieren entre "
         "3 % y 8 %; sin saber cuál usó cada quien, sus generaciones no son "
         "comparables."),

        ("Plano de cálculo, inclinación y azimut",
         "Si la generación se calculó sobre irradiancia horizontal (GHI) o sobre el "
         "plano del generador (POA), y con qué inclinación y orientación. La "
         "diferencia entre ambos planos es de 0 % a 17 % según geometría. Un "
         "proveedor puede inflar su cifra simplemente suponiendo una inclinación "
         "que después no va a construir."),

        ("Performance Ratio con desglose por componente",
         "PR global y su descomposición: temperatura, suciedad, mismatch, cableado "
         "DC y AC, eficiencia de inversor, transformador, indisponibilidad. Un PR "
         "sin desglose no se puede discutir. Sobre POA, arriba de 0.86 hay que "
         "sostenerlo con simulación."),

        ("Degradación — escalón de primer año y tasa anual",
         "LID/LeTID del primer año (típico 1–2 %) y degradación anual posterior. "
         "Debe coincidir con la garantía de potencia del módulo cotizado, no con "
         "un supuesto genérico. Una degradación declarada por debajo de 0.40 %/año "
         "no la respalda ninguna garantía comercial vigente."),

        ("Relación DC/AC y pérdida por recorte del inversor",
         "Potencia pico DC instalada contra capacidad AC nominal del conjunto de "
         "inversores, y la energía anual perdida por recorte que ya está descontada "
         "de la generación ofertada. Si el DC/AC pasa de 1.25 y la pérdida "
         "declarada es cero, la generación está sobreestimada."),

        ("Disponibilidad del sistema supuesta",
         "Fracción del año que la planta se asume operativa. Si viene al 100 % la "
         "propuesta no está considerando paros por mantenimiento, fallas de "
         "inversor ni cortes de red."),

        ("Software de simulación y entrega del archivo",
         "Nombre y versión (PVsyst, Helioscope, SAM). El archivo nativo debe "
         "entregarse como parte de la propuesta, no solo el PDF de resultados: sin "
         "él las pérdidas declaradas no se pueden verificar."),

        ("P50 y P90 con la incertidumbre declarada",
         "Producción esperada (P50) y el nivel de excedencia P90 con la sigma total "
         "que se usó y sus componentes. Un P90 que sea el P50 menos un porcentaje "
         "redondo no es un P90, es un descuento."),

        ("Sombreado y horizonte",
         "Análisis 3D de obstrucciones cercanas (equipos de azotea, pretiles, "
         "edificios vecinos) y perfil de horizonte lejano, con la pérdida anual que "
         "resulta. El sombreado es la pérdida más subestimada en cubierta industrial."),

        ("Alcance exacto del suministro",
         "Qué incluye y qué no: obra civil, refuerzo estructural, protecciones, "
         "medidor bidireccional, trámite de interconexión ante CFE, ingeniería, "
         "puesta en marcha, capacitación. Lo que no está listado no está cotizado."),
    ]


def formato_respuesta() -> list:
    """Tabla única de respuesta. Todos entregan lo mismo, en el mismo orden."""
    return [
        ("Potencia pico DC", "kWp", "Suma de la potencia nominal de los módulos"),
        ("Capacidad AC de inversores", "kW", "Suma de la potencia nominal AC"),
        ("Relación DC/AC", "—", "Resultado de las dos anteriores"),
        ("Generación año 1 — P50", "kWh/año", "Después de recorte y disponibilidad"),
        ("Generación año 1 — P90", "kWh/año", "Con sigma declarada"),
        ("Rendimiento específico", "kWh/kWp/año", "P50 dividido entre kWp"),
        ("Performance Ratio", "—", "Global, con desglose anexo"),
        ("Degradación primer año", "%", "LID/LeTID"),
        ("Degradación anual", "%/año", "Debe coincidir con la garantía del módulo"),
        ("Precio total llave en mano", "MXN sin IVA", "Alcance completo listado"),
        ("Precio unitario", "USD/Wp", "Precio total entre potencia pico DC"),
        ("O&M anual", "MXN/año", "Indicar años incluidos y qué cubre"),
        ("Garantía de producto del módulo", "años", "Defectos de fabricación"),
        ("Garantía de potencia del módulo", "años / %", "Ej. 30 años / 87.4 % residual"),
        ("Garantía del inversor", "años", "Indicar si es extendida y su costo"),
        ("Garantía de mano de obra e instalación", "años", ""),
        ("Garantía de desempeño del sistema", "% del P50", "Con ajuste por irradiancia real"),
        ("Plazo de ejecución", "semanas", "Desde anticipo hasta puesta en marcha"),
        ("Forma de pago", "%", "Anticipo, avance, contra entrega"),
        ("Vigencia de la oferta", "días", ""),
    ]


def criterios_evaluacion() -> list:
    """
    Cómo se decide. Publicarlo con la solicitud cambia lo que los proveedores
    optimizan: si saben que gana el costo nivelado y no el precio, dejan de
    recortar calidad para bajar el total.
    """
    return [
        ("Costo nivelado de la energía (LCOE)", 40,
         "Precio total y O&M contra la generación VERIFICADA sobre supuestos "
         "comunes — no la que declara el proveedor. Es el único número que "
         "compara propuestas de distinto tamaño y calidad."),
        ("Solidez técnica de la propuesta", 25,
         "Coherencia entre PR, rendimiento específico y DC/AC; entrega del archivo "
         "de simulación; análisis de sombras real; desglose de pérdidas."),
        ("Garantías y respaldo", 20,
         "Años y alcance de las garantías, tier del fabricante de módulo e "
         "inversor, presencia del fabricante en México para hacerlas válidas, "
         "garantía de desempeño del sistema con ajuste por irradiancia."),
        ("Experiencia verificable", 10,
         "Proyectos de escala comparable en operación, con referencias "
         "contactables y datos de producción reales, no fotos."),
        ("Plazo y condiciones comerciales", 5,
         "Tiempo de ejecución, forma de pago, vigencia."),
    ]


def normalizar_cotizacion(nombre: str, precio_mxn: float, kwp: float,
                          gen_declarada: float, usd_mxn: float,
                          *, pr_declarado: float = 0.0,
                          degradacion: float = 0.0,
                          dc_ac: float = 0.0,
                          om_anual_mxn: float = 0.0,
                          gar_potencia: int = 0,
                          incluye_om_anios: int = 0,
                          gen_referencia_kwh_kwp: float = 0.0,
                          factor_transposicion: float = 1.0) -> dict:
    """
    Traduce una cotización a magnitudes comparables y levanta las banderas.

    `gen_referencia_kwh_kwp` es el rendimiento que la propia herramienta calculó
    para este sitio. Sirve de contraste: si el proveedor promete 20 % más que la
    referencia sin justificarlo con geometría, el sobrante es marketing.
    """
    kwp = max(kwp, 1e-6)
    usd_wp   = (precio_mxn / usd_mxn) / (kwp * 1000.0)
    rend     = gen_declarada / kwp
    mxn_kwp  = precio_mxn / kwp

    banderas = []

    lo, hi = RANGO_RENDIMIENTO_MX
    if factor_transposicion and factor_transposicion > 0:
        lo, hi = lo * factor_transposicion, hi * factor_transposicion
    if rend > hi:
        banderas.append(("alta",
            f"Rendimiento de {rend:,.0f} kWh/kWp/año por encima del rango observado "
            f"en México ({lo:,.0f}–{hi:,.0f}). Solo es defendible con inclinación "
            f"óptima, recurso excepcional y baja temperatura, y hay que verlo en la "
            f"simulación. Cada 100 kWh/kWp de más bajan artificialmente el costo "
            f"nivelado y desplazan a propuestas honestas."))
    elif rend < lo:
        banderas.append(("media",
            f"Rendimiento de {rend:,.0f} kWh/kWp/año por debajo del rango típico. "
            f"Puede ser conservadurismo — que es bueno — o indicar sombreado, "
            f"orientación desfavorable o equipo de baja calidad. Pregunta cuál."))

    if gen_referencia_kwh_kwp > 0:
        _d = (rend / gen_referencia_kwh_kwp - 1.0) * 100.0
        if _d > 12:
            banderas.append(("alta",
                f"Promete {_d:+.0f} % más generación que la referencia calculada "
                f"para este sitio ({gen_referencia_kwh_kwp:,.0f} kWh/kWp). Exige la "
                f"simulación que lo sostenga."))
        elif _d < -12:
            banderas.append(("baja",
                f"Ofrece {_d:+.0f} % respecto a la referencia del sitio "
                f"({gen_referencia_kwh_kwp:,.0f} kWh/kWp). Propuesta conservadora."))

    if pr_declarado > 0:
        plo, phi = RANGO_PR_POA
        if pr_declarado > phi:
            banderas.append(("alta",
                f"PR declarado de {pr_declarado:.2f} por encima de {phi:.2f}. Un PR "
                f"así exige clima frío, arreglo limpio y cableado sobredimensionado; "
                f"pide el desglose por componente."))
        elif pr_declarado < plo:
            banderas.append(("baja",
                f"PR de {pr_declarado:.2f}, conservador. Verifica si refleja "
                f"sombreado real del sitio."))

    if degradacion > 0:
        dlo, dhi = RANGO_DEGRADACION
        if degradacion < dlo:
            banderas.append(("alta",
                f"Degradación de {degradacion:.2f} %/año por debajo de {dlo:.2f} %. "
                f"Ninguna garantía comercial vigente respalda esa tasa; infla la "
                f"generación de los años 10 a 25, que es donde se decide el "
                f"proyecto. Pide la hoja de garantía del módulo cotizado."))
        elif degradacion > dhi:
            banderas.append(("media",
                f"Degradación de {degradacion:.2f} %/año, alta para módulos "
                f"mono-Si actuales. Puede indicar tecnología de generación anterior."))

    if dc_ac > 0:
        clo, chi = RANGO_DC_AC
        if dc_ac > chi:
            banderas.append(("media",
                f"DC/AC de {dc_ac:.2f} por encima de {chi:.2f}. Verifica que la "
                f"pérdida por recorte esté descontada de la generación ofertada."))
        elif dc_ac < clo + 0.02:
            banderas.append(("baja",
                f"DC/AC de {dc_ac:.2f}, inversor sobredimensionado. Encarece sin "
                f"aportar energía."))

    ulo, uhi = RANGO_COSTO_USD_WP
    if usd_wp < ulo:
        banderas.append(("alta",
            f"Precio de {usd_wp:.2f} USD/Wp por debajo de {ulo:.2f}. A ese nivel "
            f"algo falta del alcance — estructura, protecciones, trámite de "
            f"interconexión, ingeniería — o el equipo es de segunda línea. Pide "
            f"el desglose partida por partida."))
    elif usd_wp > uhi:
        banderas.append(("media",
            f"Precio de {usd_wp:.2f} USD/Wp por encima de {uhi:.2f}. Puede estar "
            f"justificado por obra civil, refuerzo estructural o condiciones de "
            f"sitio: pide que se separe del suministro fotovoltaico."))

    if om_anual_mxn <= 0 and incluye_om_anios <= 0:
        banderas.append(("alta",
            "Sin O&M cotizado. El O&M de un sistema en cubierta industrial cuesta "
            "entre 1.2 % y 2.2 % del CAPEX al año, incluyendo limpieza, monitoreo y "
            "seguros. Omitirlo hace ver más barata la propuesta y traslada el costo "
            "al comprador después de firmar."))

    if 0 < gar_potencia < 25:
        banderas.append(("media",
            f"Garantía de potencia de {gar_potencia} años. El estándar del mercado "
            f"es 25–30 años; por debajo indica módulo de segunda línea o "
            f"fabricante sin respaldo local."))

    return {
        "nombre": nombre, "precio_mxn": precio_mxn, "kwp": kwp,
        "gen": gen_declarada, "usd_wp": usd_wp, "rendimiento": rend,
        "mxn_kwp": mxn_kwp, "om_anual": om_anual_mxn,
        "banderas": banderas,
        "n_alta": sum(1 for b in banderas if b[0] == "alta"),
    }


def lcoe_cotizacion(precio_mxn: float, gen_anio1: float, om_anual_mxn: float,
                    *, horizonte: int = 25, tasa: float = 12.0,
                    degradacion: float = 0.5, lid: float = 1.0,
                    inflacion_om: float = 4.0,
                    isr_pct: float = 30.0, aplicar_isr: bool = True,
                    art34: bool = True) -> float:
    """
    Costo nivelado de una cotización sobre supuestos COMUNES a todos los
    licitantes. Lo único que cambia entre propuestas es el precio, la generación
    y el O&M; el resto lo fija el comprador para que la comparación sea limpia.

    LCOE = VP(costos) / VP(energía). Ambos descontados: es un error frecuente
    dividir un valor presente entre energía nominal.
    """
    n   = max(1, int(horizonte))
    isr = (isr_pct / 100.0) if aplicar_isr else 0.0
    gen = _serie_generacion(gen_anio1, degradacion, lid, n)
    om  = [om_anual_mxn * (1.0 + inflacion_om / 100.0) ** i * (1.0 - isr)
           for i in range(n)]
    vp_costos = precio_mxn + _vp(om, tasa)
    if aplicar_isr and art34:
        vp_costos -= (precio_mxn * isr) / (1.0 + tasa / 100.0)
    vp_energia = _vp(gen, tasa)
    return (vp_costos / vp_energia) if vp_energia > 0 else 0.0


def calc_precio_hurdle(gen1: float, inv_usd: float, plazo: int,
                       wacc_pct: float, spread_pct: float,
                       esc_ppa: float, deg: float,
                       om_pct: float, inf_om: float, seg_pct: float,
                       usd_mx: float, equity_pct: float,
                       tasa_deuda: float, plazo_deuda: int, con_fin: bool,
                       vida_util_total: int = 25,
                       dimensionar_por_dscr: bool = False,
                       dscr_objetivo: float = 1.30,
                       lid_pct: float = 1.5,
                       descuento_merchant: float = 30.0,
                       perfil_esculpido: bool = False,
                       disponibilidad: float = 1.0,
                       inv_replace_year: int = 0,
                       inv_replace_mxn: float = 0.0,
                       inv_replace_esc: float = 0.0,
                       isr_pct: float = 0.0,
                       deduccion_art34: bool = False,
                       escudo_inmediato: bool = True,
                       ke_dinamico: bool = True,
                       dsra_meses: float = 0.0):
    """Precio PPA donde la TIR del equity alcanza el hurdle rate.

    FIX — el objetivo es Ke + spread, no WACC + spread. La TIR que devuelve
    calc_ppa_result se calcula sobre flujos al accionista (FCFE) partiendo de
    -equity_mxn, así que la referencia correcta es el costo del equity. Comparar
    una TIR de equity contra el WACC subestimaba el precio requerido en
    proyectos apalancados.

    Retorna None si no existe solución en el rango de precios evaluado.
    """
    def _res(p):
        return calc_ppa_result(gen1, inv_usd, p, plazo, wacc_pct, esc_ppa,
                               deg, om_pct, inf_om, seg_pct, usd_mx,
                               equity_pct, tasa_deuda, plazo_deuda, con_fin,
                               vida_util_total, None,
                               dimensionar_por_dscr, dscr_objetivo,
                               lid_pct, descuento_merchant, perfil_esculpido,
                               disponibilidad, inv_replace_year, inv_replace_mxn,
                               inv_replace_esc, isr_pct, deduccion_art34,
                               escudo_inmediato, ke_dinamico, dsra_meses)
    # Ke no depende del precio PPA — se evalúa una sola vez.
    tir_objetivo = _res(1.0)["ke_pct"] + spread_pct

    def tir_at(p):
        r = _res(p)
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
                 p90_real, annual_gen: float,
                 usd_to_mxn: float,
                 gen_por_anio: dict = None) -> dict:
    """Construye los tres escenarios de sensibilidad para Turnkey.

    FIX — antes esta función leía la degradación y el O&M vía
    `fm.get("panel_degradation", 0.5)` / `fm.get("om_pct", 1.0)`, pero
    calc_financial_model no devolvía esas claves: los `.get()` caían SIEMPRE al
    default. Si el usuario configuraba degradación 0.8 %/año y O&M 2.5 %, el caso
    base lo honraba y los tres escenarios revertían en silencio a 0.5 % y 1.0 %,
    haciendo que el escenario pesimista saliera optimista. Ahora la configuración
    se lee del propio `fm`, que ya la devuelve explícitamente.

    Escenarios (con P90 como base, coherente con el dashboard):
      base  : generación P90 — el mismo número que se muestra en pantalla
      best  : P50 +5 %, CAPEX -10 %, inflación CFE +3 pts
      worst : peor año histórico real de la serie NASA, CAPEX +15 %, infl. -2 pts

    El peor caso ya no reutiliza P90 (que es la base); usa el mínimo observado en
    los ~20 años de irradiancia, que es un dato, no un factor inventado.
    """
    # Configuración real del caso base — sin defaults silenciosos.
    _deg   = fm["panel_degradation"]
    _om    = fm["om_pct"]
    _af    = fm["autoconsumo_frac"]
    _lid   = fm["lid_pct"]
    _iry   = fm["inv_replace_year"]
    _irp   = fm["inv_replace_pct"]
    _irm   = fm["inv_replace_mxn"]
    _ire   = fm["inv_replace_esc"]
    _isr   = fm["isr_pct"]
    _a34   = fm["deduccion_art34"]
    _esc   = fm["escudo_inmediato"]
    _seg   = fm["seguro_pct"]
    _cd    = fm["con_deuda"]
    _dp    = fm["deuda_pct"]
    _td    = fm["tasa_deuda_pct"]
    _pd    = fm["plazo_deuda_tk"]

    def _run(capex_factor, inf_factor, gen_base):
        return calc_financial_model(
            gen_base, kwp, (inversion_mxn * capex_factor) / usd_to_mxn,
            fm["tarifas_y"][0], inflacion_cfe + inf_factor, wacc,
            _deg, vida_util, usd_to_mxn, _om,
            autoconsumo_frac=_af, lid_pct=_lid,
            inv_replace_year=_iry, inv_replace_pct=_irp,
            inv_replace_mxn=_irm, inv_replace_esc=_ire,
            isr_pct=_isr, deduccion_art34=_a34,
            escudo_inmediato=_esc, seguro_pct=_seg,
            con_deuda=_cd, deuda_pct=_dp,
            tasa_deuda_pct=_td, plazo_deuda_tk=_pd,
        )

    gen_p90  = p90_real if p90_real else annual_gen * 0.92
    gen_best = annual_gen * 1.05
    # Peor año observado en la serie histórica; si no hay serie, P90 × 0.95.
    if gen_por_anio:
        _peor_anio = min(gen_por_anio, key=gen_por_anio.get)
        gen_worst  = gen_por_anio[_peor_anio]
        _nota_worst_gen = f"Peor año histórico ({_peor_anio})"
    else:
        gen_worst = gen_p90 * 0.95
        _nota_worst_gen = "P90 -5 % (sin serie histórica)"

    def _fmt(s):
        _tir = f"{s['tir']:.1f}%" if s['tir'] is not None else "N/A"
        if s.get("tir_metodo") == "MIRR":
            _tir += " (MIRR)"
        _vpn = f"${s['vpn']/1e6:.2f}M MXN"
        _pb  = f"{s['pb_simple']:.1f}a" if s['pb_simple'] is not None else f">{vida_util}a"
        _pbd = f"{s['pb_disc']:.1f}a"  if s['pb_disc']  is not None else f">{vida_util}a"
        _lco = f"${s['lcoe']:.2f}/kWh"
        return dict(tir=_tir, vpn=_vpn, pb=_pb, pb_disc=_pbd, lcoe=_lco)

    best_fm  = _run(0.90, +3.0, gen_best)
    worst_fm = _run(1.15, -2.0, gen_worst)

    return {
        "base":  {**_fmt(fm),
                  "nota": f"CAPEX base · Inflación CFE {inflacion_cfe:.1f}% · Gen P90"},
        "best":  {**_fmt(best_fm),
                  "nota": "CAPEX -10% · Inflación CFE +3pts · Gen P50 +5%"},
        "worst": {**_fmt(worst_fm),
                  "nota": f"CAPEX +15% · Inflación CFE -2pts · {_nota_worst_gen}"},
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
        _tir = f"{res['tir']:.1f}%" if res['tir'] is not None else "N/A"
        _vpn = f"${res['vpn']/1e6:.2f}M MXN"
        _pb  = f"{res['pb']:.1f}a" if res['pb'] is not None else f">{plazo_obj}a"
        return dict(tir=_tir, vpn=_vpn, pb=_pb)

    ro = resultados[plazo_obj]
    base_tir = f"{ro['tir']:.1f}%" if ro['tir'] is not None else "N/A"
    base_vpn = f"${ro['vpn']/1e6:.2f}M MXN"
    base_pb  = f"{ro['pb']:.1f}a" if ro['pb'] is not None else f">{plazo_obj}a"

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
    gen_por_anio: dict = None,
) -> bytes:
    import os as _os
    escenarios = _esc_turnkey(
        fm, vida_util, wacc, kwp, inversion_mxn, inflacion_cfe,
        p90_real, annual_gen, usd_to_mxn, gen_por_anio
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
        "area_instalacion": area_used * (1 + HOLGURA_INSTALACION_PCT / 100),
        "holgura_pct":      HOLGURA_INSTALACION_PCT,
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
        "pb_simple":       f"{pb_simple:.1f}" if pb_simple is not None else None,
        "pb_disc":         f"{pb_disc:.1f}" if pb_disc is not None else None,
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
    ppa_precios_por_plazo=None,
) -> bytes:
    import os as _os
    if ppa_precios_por_plazo is None:
        ppa_precios_por_plazo = {pl: ppa_precio_manual for pl in ppa_plazos}

    plazos_data = []
    for pl in ppa_plazos:
        r = resultados[pl]
        _precio_pl = ppa_precios_por_plazo.get(pl, ppa_precio_manual)
        _desc_pl   = ((_precio_pl / ppa_tarifa_cliente) - 1) * 100
        _gen_cl   = r.get("gen_y", [])
        _prec_cl  = r.get("prec_y", [])
        _cfe_y    = [ppa_tarifa_cliente * (1 + ppa_inflacion_cfe / 100) ** i for i in range(pl)]
        _pago_ppa = [_gen_cl[i] * _prec_cl[i] for i in range(pl)] if _gen_cl else []
        _pago_cfe = [_gen_cl[i] * _cfe_y[i]   for i in range(pl)] if _gen_cl else []
        _ahorro_y = [_pago_cfe[i] - _pago_ppa[i] for i in range(pl)] if _pago_ppa else []
        _flujos = []
        for i in range(pl):
            _flujos.append({
                "anio":       i + 1,
                "gen_mwh":    round(_gen_cl[i] / 1000, 2) if _gen_cl else 0,
                "precio_ppa": round(_prec_cl[i], 4) if _prec_cl else 0,
                "ingreso":    round(r["ing_y"][i], 0) if r.get("ing_y") else 0,
                "om_seg":     round(r["om_y"][i] + r["seg_y"][i], 0) if r.get("om_y") else 0,
                "deuda":      round(r["deu_y"][i], 0) if r.get("deu_y") else 0,
                "fn":         round(r["fn_y"][i], 0) if r.get("fn_y") else 0,
                "cfe_kwh":    round(_cfe_y[i], 4),
                "ahorro":     round(_ahorro_y[i], 0) if _ahorro_y else 0,
            })
        plazos_data.append({
            "pl":                    pl,
            "precio_pl":             _precio_pl,
            "descuento_vs_cfe":      _desc_pl,
            "pm":                    r.get("pm"),
            "ph":                    r.get("ph"),
            "ph_label":              hurdle_label,
            "vpn_wacc":              r.get("vpn_wacc", r["vpn"]),
            "vpn_hurdle":            r.get("vpn_hurdle", r["vpn"]),
            "vpn":                   r["vpn"],
            "tir":                   r["tir"],
            "lcoe":                  r.get("lcoe"),
            "pi":                    r.get("pi"),
            "pb":                    r["pb"],
            "pb_disc":               r.get("pb_disc"),
            "vr":                    r.get("valor_residual", 0),
            "ing_total":             r["ing_total"],
            "ahorro_total_cliente":  sum(_ahorro_y),
            "flujos":                _flujos,
        })

    ro = resultados[ppa_plazo_minimo]
    _precio_obj = ppa_precios_por_plazo.get(ppa_plazo_minimo, ppa_precio_manual)
    escenarios = _esc_ppa(
        resultados, ppa_plazo_minimo, ppa_cache_kwargs,
        _precio_obj, ppa_spread_hurdle, ppa_usar_valor_residual, vida_util
    )
    data = {
        "logo_b64":            _get_logo_b64(),
        "fecha":               fecha,
        "ubicacion":           proj_loc,
        "lat":                 lat, "lon": lon,
        "kwp":                 kwp, "n_panels": n_panels,
        "inversion_usd":       int(inversion_usd),
        "inversion_mxn":       int(inversion_mxn),
        "usd_to_mxn":          usd_to_mxn,
        "gen_anual":           ppa_gen_anual,
        "gen_base_label":      gen_base_label,
        "hsp":                 hsp_anual,
        "co2_t":               co2_saved_t,
        "co2_factor":          CO2_FACTOR_KG_KWH,
        "pr_pct":              pr_pct,
        "degradacion":         ppa_degradacion,
        "vida_util":           vida_util,
        "wacc":                ppa_wacc,
        "spread":              ppa_spread_hurdle,
        "hurdle_label":        hurdle_label,
        "esc_ppa":             ppa_inflacion_tarifa,
        "inflacion_cfe":       ppa_inflacion_cfe,
        "om_pct":              ppa_om_pct,
        "seg_pct":             ppa_seguros_pct,
        "con_fin":             ppa_financiamiento,
        "equity_pct":          ppa_equity_pct,
        "tasa_deuda":          ppa_tasa_deuda,
        "plazo_deuda":         ppa_plazo_deuda,
        "usar_vr":             ppa_usar_valor_residual,
        "valor_residual_nota": valor_residual_nota,
        "precio_manual":       _precio_obj,
        "tarifa_cliente":      ppa_tarifa_cliente,
        "descuento_vs_cfe":    descuento_vs_cfe,
        "ahorro_total":        ahorro_total,
        "plazos":              plazos_data,
        "plazo_obj":           {
            "pl":        ppa_plazo_minimo,
            "precio_pl": _precio_obj,
            "pm":        ro.get("pm"),
            "ph":        ro.get("ph"),
            "vpn_wacc":  ro.get("vpn_wacc", ro["vpn"]),
            "vpn_hurdle": ro.get("vpn_hurdle", ro["vpn"]),
            "vpn":       ro["vpn"],
            "tir":       ro["tir"],
            "lcoe":      ro.get("lcoe"),
            "pi":        ro.get("pi"),
            "pb":        ro["pb"],
            "pb_disc":   ro.get("pb_disc"),
            "vr":        ro.get("valor_residual", 0),
            "ing_total": ro["ing_total"],
        },
        "escenarios": escenarios,
    }
    _script = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "word_gen", "gen_ppa.js")
    return _run_word_script(_script, data)


def _envolver(texto: str, ancho: int = 72) -> list:
    """Parte un párrafo en líneas de ancho fijo para el TOR en texto plano."""
    palabras, lineas, actual = texto.split(), [], ""
    for w in palabras:
        if len(actual) + len(w) + 1 > ancho:
            lineas.append(actual); actual = w
        else:
            actual = f"{actual} {w}".strip()
    if actual:
        lineas.append(actual)
    return lineas


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
        f"  Generación P90 anual : {f'{p90:,.0f} kWh/año  (P50·(1−1.282·σ_total) · σ compuesta sobre {len(gen_por_anio)} años NASA POWER {NASA_START}–{NASA_END})' if p90 else 'No disponible — cargar datos NASA POWER'}",
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
        "  • SUPUESTO CLAVE DE GEOMETRÍA:",
        *[f"    {l}" for l in _envolver(GEOM_NOTA, 72)],
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
        "  • El P90 (horizonte anual) se calcula como P50·(1−1.282·σ_total), con",
        "    σ_total = √(σ_interanual² + σ_recurso² + σ_modelo² + σ_degradación²).",
        "    El percentil empírico de la serie NO se usa: sólo captura variabilidad",
        "    interanual e ignora la incertidumbre del propio dato satelital.",
        "  • Este cálculo NO sustituye un Energy Yield Assessment firmado por",
        "    Ingeniero Independiente, que el prestamista exige antes del cierre.",
        f"    con {len(gen_por_anio) if gen_por_anio else 'N/A'} años de irradiancia real NASA POWER ({NASA_START}–{NASA_END}).",
        "  • La ingeniería detallada y la simulación definitiva son responsabilidad del proveedor.",
        "  • Verificar disponibilidad y capacidad de red CFE en el punto de interconexión.",
        "═══════════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)


# ── Helpers PDF ───────────────────────────────────────────────────────────────
# Solo usamos rl_colors (reportlab.lib.colors)
_DARK   = rl_color.HexColor("#1e2028")
_PANEL  = rl_color.HexColor("#1e2028")
_AMBER  = rl_color.HexColor("#f59e0b")
_TEAL   = rl_color.HexColor("#14b8a6")
_ROSE   = rl_color.HexColor("#f43f5e")
_GREY   = rl_color.HexColor("#94a3b8")
_WHITE  = rl_color.HexColor("#f9fafb")
_LIGHT  = rl_color.HexColor("#d1d5db")
_BG2    = rl_color.HexColor("#1e2028")


def _pdf_styles():
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
        ("GRID",         (0, 0), (-1, -1),              0.4, rl_color.HexColor("#343841")),
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
        ("GRID",          (0, 0), (-1, -1), 0.4, rl_color.HexColor("#343841")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    return Table(rows, colWidths=cw, style=ts)


def _hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=rl_color.HexColor("#343841"), spaceAfter=6, spaceBefore=2)


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
        ("Generación P90",    f"{p90/1000:.1f} MWh/año" if p90 else "—", "Horizonte anual · σ compuesta"),
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
         Paragraph("O&M + seguros", S["td_l"]),    Paragraph(f"{om_pct:.2f}% inv.", S["td"])],
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
        GEOM_NOTA,
        "Los valores son estimados de pre-sizing (±15%). El proveedor deberá realizar diseño detallado con software especializado (PVSyst, Helioscope, etc.) con la geometría real del sitio: inclinación, azimut, sombras 3D y desglose de pérdidas por componente.",
        f"El P90 de horizonte anual se calcula como P50·(1−1.282·σ_total), donde σ_total combina en cuadratura la variabilidad interanual medida sobre {NASA_END - NASA_START + 1} años de NASA POWER ({NASA_START}–{NASA_END}) con la incertidumbre del dato satelital, del modelo de pérdidas y de la tasa de degradación. No sustituye un Energy Yield Assessment de Ingeniero Independiente.",
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
    story.append(_kpi_table([
        ("Precio PPA año 1",     f"${ppa_precio_manual:.4f}/kWh", "Evaluado"),
        ("Precio minimo viable", pm_str,                           f"VPN=0 a {ppa_plazo_minimo}a"),
        ("Descuento vs CFE hoy", f"{descuento_vs_cfe:+.1f}%",     "precio PPA vs tarifa"),
        ("Ahorro total cliente", f"${ahorro_total:,.0f}",          f"MXN en {ppa_plazo_minimo} años"),
    ], S))
    story.append(Spacer(1, 6))
    story.append(_kpi_table([
        # Los flujos son al accionista (FCFE): se descuentan a Ke, no al WACC.
        ("VPN a Ke",           f"${ro['vpn_wacc']:,.0f} MXN",     f"Ke {ro.get('ke_pct', ppa_wacc):.1f}%"),
        ("VPN a hurdle rate",   f"${ro['vpn_hurdle']:,.0f} MXN",   f"Ke+{ppa_spread_hurdle:.0f}% = {ro.get('disc_pct', 0):.1f}%"),
        ("TIR equity",         f"{ro['tir']:.1f}%" if ro["tir"] else "—", "sobre capital propio"),
        ("DSCR mínimo",        f"{ro['dscr_min']:.2f}x" if ro.get("dscr_min") else "sin deuda",
                               f"objetivo {ro.get('dscr_objetivo', 0):.2f}x · {ro.get('metodo_deuda','')}"),
        ("LLCR",               f"{ro['llcr']:.2f}x" if ro.get("llcr") else "sin deuda",
                               "VP(CFADS) ÷ saldo de deuda"),
        ("Deuda / equity",     (f"${ro['deuda_mxn']:,.0f} / ${ro['equity_mxn']:,.0f}"
                                if ro.get("deuda_mxn") else f"${ro.get('equity_mxn',0):,.0f} equity"),
                               f"{ro.get('apalancamiento',0):.0f}% del CAPEX"),
        ("Payback simple",     f"{ro['pb']} años" if ro["pb"] else f">{ppa_plazo_minimo}a", "nominal s/descontar"),
        ("Payback descontado",  f"{ro['pb_disc']} años" if ro.get("pb_disc") is not None else f">{ppa_plazo_minimo}a", f"Ke {ro.get('ke_pct', ppa_wacc):.1f}%"),
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
        ("Payback simple",  lambda r: f"{r['pb']}" if r["pb"] is not None else f">{ppa_plazo_minimo}a"),
        ("Payback desc.",    lambda r: f"{r['pb_disc']}" if r.get("pb_disc") is not None else f">{ppa_plazo_minimo}a"),
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

# Componentes de irradiancia (GHI / difusa / DNI) para la transposición.
# None = no disponibles → la herramienta trabaja en modo coplanar.
if "nasa_componentes" not in st.session_state:
    st.session_state.nasa_componentes = None

# Ratio POA/GHI mensual aplicado. None o lista de 1.0 = coplanar.
if "poa_ratio" not in st.session_state:
    st.session_state.poa_ratio = None



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
                # Componentes para transposición — opcional, no bloquea si falla
                st.session_state.nasa_componentes = get_nasa_power_componentes(lat, lon)
                st.success(f"✅ Datos de NASA POWER cargados — {n_anios} años históricos ({NASA_START}–{NASA_END})")
                if st.session_state.nasa_componentes is None:
                    st.warning("⚠️ Sin datos de difusa: la transposición queda deshabilitada.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.nasa_irradiance   = DEFAULT_IRR.copy()
                st.session_state.nasa_irr_por_anio = {}
                st.session_state.nasa_source_label = None
                st.session_state.nasa_componentes  = None
                st.session_state.poa_ratio         = None

    lbl = st.session_state.get("nasa_source_label", None)
    st.caption(f"Fuente: NASA POWER (2005–2024) · {lbl}" if lbl else "Valores por defecto: CDMX")

    st.markdown("---")

    # ── Geometría del arreglo · transposición GHI → POA ──────────────────────
    st.markdown("#### 🧭 Geometría del arreglo")

    _comp = st.session_state.get("nasa_componentes")

    if _comp is None:
        st.session_state.poa_ratio = None
        st.caption("Modo **coplanar**. Carga NASA POWER para habilitar la "
                   "transposición a plano inclinado.")
        geom_modo = "Coplanar"
        geom_tilt = 0.0
        geom_azim = 180.0
        geom_alb  = ALBEDO_DEFAULT
    else:
        _ghi_c, _dif_c, _dni_c = _comp

        geom_modo = st.radio(
            "Montaje",
            ["Coplanar (sigue la cubierta)", "Inclinado (definir geometría)"],
            index=0, key="geom_modo",
            help="Coplanar es el supuesto conservador y el más común en nave "
                 "industrial con cubierta de lámina: los módulos van paralelos "
                 "al techo y la irradiancia sobre el plano es prácticamente la "
                 "horizontal. Inclinado aplica el modelo Hay-Davies y sube la "
                 "generación entre 2 % y 17 % según latitud y orientación — "
                 "pero exige estructura, lastre y separación entre filas que "
                 "hay que costear aparte.")

        if geom_modo.startswith("Coplanar"):
            st.session_state.poa_ratio = None
            geom_tilt = 0.0
            geom_azim = 180.0
            geom_alb  = ALBEDO_DEFAULT
            _b_opt, _r_opt = inclinacion_optima(lat, _ghi_c, _dif_c)
            st.caption(f"Referencia: a **{_b_opt:.0f}°** hacia el sur ganarías "
                       f"**{(_r_opt-1)*100:+.1f} %** de irradiancia.")
        else:
            _b_opt, _r_opt = inclinacion_optima(lat, _ghi_c, _dif_c)
            geom_tilt = st.slider(
                "Inclinación β (°)", 0.0, 40.0, float(round(_b_opt)), 1.0,
                key="geom_tilt",
                help=f"Óptimo anual en esta latitud: {_b_opt:.0f}°. El barrido se "
                     "corta en 40° porque pasando ~30° la estructura necesita "
                     "lastre significativo y la separación entre filas crece, así "
                     "que la ganancia de irradiancia se la come el costo de "
                     "estructura y la superficie perdida.")

            _AZ = {"Sur (óptimo)": 180.0, "Sureste": 135.0, "Suroeste": 225.0,
                   "Este": 90.0, "Oeste": 270.0, "Norte": 0.0, "Personalizado": None}
            _az_lbl = st.selectbox("Orientación (azimut)", list(_AZ.keys()),
                                   index=0, key="geom_az_lbl")
            if _AZ[_az_lbl] is None:
                geom_azim = st.slider("Azimut de brújula (°)", 0.0, 359.0, 180.0, 5.0,
                                      key="geom_azim",
                                      help="0 = Norte · 90 = Este · 180 = Sur · 270 = Oeste")
            else:
                geom_azim = _AZ[_az_lbl]

            geom_alb = st.slider(
                "Albedo del entorno", 0.10, 0.40, ALBEDO_DEFAULT, 0.01,
                key="geom_albedo",
                help="Reflectancia del suelo alrededor del arreglo. Concreto "
                     "envejecido y grava 0.20; lámina clara o concreto nuevo "
                     "0.30–0.40; césped 0.20. Solo importa a inclinaciones altas.")

            _tr = poa_mensual_hay_davies(lat, _ghi_c, _dif_c,
                                         geom_tilt, geom_azim, geom_alb)
            st.session_state.poa_ratio = _tr["ratio"]

            _g = (_tr["ratio_an"] - 1.0) * 100.0
            _color = "#4ade80" if _g >= 0 else "#f87171"
            st.markdown(
                f'<div style="background:#1e2028;border:1px solid #2e3138;'
                f'border-radius:8px;padding:10px 12px;margin-top:8px;">'
                f'<div style="font-size:11px;color:#94a3b8;letter-spacing:.4px;">'
                f'FACTOR DE TRANSPOSICIÓN POA/GHI</div>'
                f'<div style="font-size:24px;font-weight:700;color:{_color};'
                f'line-height:1.2;">{_tr["ratio_an"]:.4f}</div>'
                f'<div style="font-size:11px;color:#94a3b8;">'
                f'{_g:+.1f} % de irradiancia vs coplanar · β={geom_tilt:.0f}° '
                f'az={geom_azim:.0f}°</div></div>',
                unsafe_allow_html=True)

            _fd = sum(_tr["difusa"]) / 12
            st.caption(f"Fracción difusa media {_fd*100:.0f} % · albedo {geom_alb:.2f} · "
                       f"modelo Hay-Davies sobre día representativo mensual.")

            if geom_tilt >= 25:
                st.caption("⚠️ Arriba de 25° verifica separación entre filas: la "
                           "superficie de cubierta necesaria crece rápido y el "
                           "área que reporta la herramienta asume coplanar.")

    st.markdown("---")

    # ── Ficha técnica del panel ───────────────────────────────────────────────
    st.markdown("#### 📋 Panel (datos básicos)")
    panel_wp           = st.number_input("Potencia pico Pmax (Wp)", 100, 900, 650, 5)
    panel_eff_declared = st.number_input("Eficiencia (%)", 10.0, 26.0, 24.1, 0.01)
    panel_largo_mm     = st.number_input("Largo (mm)", 1000, 2500, 2382, 1)
    panel_ancho_mm     = st.number_input("Ancho (mm)", 700, 1300, 1134, 1)
    panel_peso_kg      = st.number_input("Peso (kg)", 5.0, 40.0, 32.7, .1)

    disponibilidad_pct = st.slider(
        "Disponibilidad del sistema (%)", 90.0, 100.0, 100.0, 0.1,
        key="disponibilidad_pct",
        help="Fracción del tiempo que la planta está operativa. Default 100 % porque el "
             "PR ya incorpora ~1 % de indisponibilidad típica; bajarlo sin subir el PR "
             "cuenta la pérdida dos veces.\n\n"
             "Úsalo para modelar un escenario concreto: un contrato de O&M que garantiza "
             "99.5 % con penalizaciones, o el caso de incumplimiento que el banco quiere "
             "ver estresado.")

    st.markdown("---")

    # ── Inversores ────────────────────────────────────────────────────────────
    costo_dc_marginal = st.number_input(
        "Costo marginal del kWp DC (USD/kWp)", 100.0, 1500.0, 600.0, 25.0,
        key="costo_dc_marginal",
        help="Costo de añadir UN kWp más de panel a un inversor ya dimensionado: "
             "módulo, estructura y cableado DC. NO incluye inversor, interconexión ni "
             "costos fijos, porque esos no cambian al agregar paneles. Suele ser "
             "50–65 % del costo total por kWp. Se usa sólo para calcular el DC/AC óptimo.")
    st.markdown("#### 🔌 Inversores")
    inv_unit_kw = st.number_input(
        "Potencia AC por inversor (kW)", 1.0, 5000.0, 25.0, 1.0,
        key="inv_unit_kw",
        help="Potencia nominal de salida AC de cada unidad. En modo pre-sizing sólo "
             "sirve para reportar un número equivalente de unidades; en modo detalle "
             "define la capacidad AC real.")
    _modo_inv = st.radio(
        "Dimensionamiento del inversor",
        ["Pre-sizing (por relación DC/AC)", "Detalle (por unidades)"],
        key="modo_inversores",
        help="**Pre-sizing**: capturas la relación DC/AC y la capacidad AC se deriva de "
             "ella. Es el criterio de PVWatts para estimación preliminar, cuando "
             "todavía no conoces el modelo de inversor.\n\n"
             "**Detalle**: capturas cuántas unidades y de qué potencia; la relación "
             "DC/AC pasa a ser un resultado, con la granularidad real del catálogo. "
             "Úsalo cuando ya tengas equipo cotizado.")
    if _modo_inv.startswith("Detalle"):
        n_inv_manual = st.number_input(
            "Número de inversores", 1, 500, 6, 1, key="n_inv_manual",
            help="La relación DC/AC resultante y el recorte se recalculan solos.")
        dc_ac_objetivo = st.slider(
            "Relación DC/AC de referencia", 1.00, 1.60, 1.20, 0.01,
            key="dc_ac_obj",
            help="Sólo como comparación contra la configuración capturada y para el "
                 "área máxima compatible con Generación Distribuida.")
    else:
        n_inv_manual = 0
        dc_ac_objetivo = st.slider(
            "Relación DC/AC", 1.00, 1.60, 1.20, 0.01,
            key="dc_ac_obj",
            help="kWp DC por kW AC. Típico en México 1.15–1.30: sobredimensionar el DC "
                 "aprovecha mejor el inversor a costa de recortar los picos. "
                 "La capacidad AC se deriva de aquí (kW AC = kWp ÷ DC/AC), sin "
                 "redondear a unidades: la granularidad del catálogo se resuelve en "
                 "ingeniería de detalle.")

    st.markdown("---")

    # ── PR del Sistema ───────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Performance Ratio (PR) del sistema")

    # El PR significa cosas distintas según se haya transpuesto o no. Sin
    # transposición absorbe además la pérdida de orientación; con ella queda
    # como PR de sistema puro y por tanto es más alto.
    _TRANSP = bool(st.session_state.get("poa_ratio"))

    st.markdown(f"""
    <div style="font-size:13px; color:#cbd5e1; margin-bottom:10px;">
        PR global (inversor, cableado, suciedad, mismatch y temperatura){
        '' if _TRANSP else ' + <b>pérdida por orientación</b>'}.
        <br><span style="color:#94a3b8;font-size:12px;">
        Medido sobre {'POA — plano del generador' if _TRANSP else 'GHI — plano horizontal'}.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 0.80 sobre POA es el centro conservador del rango real 0.78–0.84; sobre
    # GHI, 0.79 ya lleva dentro la pérdida de orientación de un arreglo coplanar.
    _pr_default = 0.80 if _TRANSP else 0.79

    effective_pr = st.slider(
        "Performance Ratio (PR)",
        min_value=0.60,
        max_value=0.95,
        value=_pr_default,
        step=0.01,
        format="%.2f",
        key=f"pr_slider_{'poa' if _TRANSP else 'ghi'}",
        help=(
            "MODO INCLINADO — la irradiancia ya está transpuesta al plano del "
            "generador con Hay-Davies, así que este PR es el PR de sistema puro: "
            "solo pérdidas eléctricas, térmicas, de suciedad y mismatch. Rango "
            "real 0.78–0.84. Arriba de 0.85 hay que sostenerlo con simulación."
            if _TRANSP else
            "MODO COPLANAR — la generación se calcula sobre irradiancia HORIZONTAL "
            "(GHI de NASA POWER), sin transposición. Este PR absorbe además la "
            "diferencia de orientación e inclinación, por eso es menor que el PR "
            "de placa de una simulación con plano inclinado.\n\n"
            "SUPUESTO: arreglo COPLANAR sobre cubierta plana o de baja pendiente "
            "(POA/GHI = 1.00). Si el arreglo va inclinado al sur, la irradiancia "
            "real en el plano es hasta 6 % mayor y este PR subestima; si va al "
            "poniente, hasta 4 % menor y sobreestima. Para captarlo, activa el "
            "modo inclinado en Geometría del arreglo."
        ))

    pr_pct = effective_pr * 100

    # Umbrales distintos según el plano de referencia. Aplicar los umbrales
    # clásicos (0.82 / 0.75, definidos sobre plano inclinado) a un PR medido
    # sobre GHI marcaría en rojo cualquier configuración normal.
    if _TRANSP:
        if   pr_pct >= 85: badge_class, badge_text = "pr-red",    "● Optimista — exige simulación que lo respalde"
        elif pr_pct >= 78: badge_class, badge_text = "pr-green",  "● Rango de trabajo"
        elif pr_pct >= 72: badge_class, badge_text = "pr-yellow", "● Conservador"
        else:              badge_class, badge_text = "pr-red",    "● Muy bajo para plano inclinado — revisar diseño"
    else:
        if   pr_pct >= 82: badge_class, badge_text = "pr-red",    "● Demasiado alto sobre GHI — implica orientación no modelada"
        elif pr_pct >= 77: badge_class, badge_text = "pr-green",  "● Rango de trabajo"
        elif pr_pct >= 70: badge_class, badge_text = "pr-yellow", "● Conservador"
        else:              badge_class, badge_text = "pr-red",    "● Muy bajo — revisar diseño u orientación"

    st.markdown(f"""
    <div class="pr-badge {badge_class}" style="margin:10px 0 8px 0;">
        {badge_text} — PR {pr_pct:.1f}%
    </div>
    """, unsafe_allow_html=True)

    # Rendimiento implícito — la prueba de olfato que cualquiera puede verificar
    # contra plantas reales. Se calcula sobre la irradiancia efectiva del modelo.
    _r_mes = st.session_state.get("poa_ratio") or [1.0] * 12
    _rend = sum(v * r * d for v, r, d
                in zip(st.session_state.nasa_irradiance, _r_mes, MONTH_DAYS)) * effective_pr

    # La banda de referencia (1,500–1,750 kWh/kWp) está observada en arreglos
    # coplanares o de baja inclinación, que es como está montada la mayoría de la
    # GD industrial mexicana. Al inclinar el arreglo la banda entera se desplaza
    # hacia arriba en la misma proporción que la irradiancia captada: si no se
    # desplazara, la herramienta recomendaría inclinar y acto seguido marcaría el
    # resultado como optimista, contradiciéndose sola.
    _tf = 1.0
    if _TRANSP:
        _r_ = st.session_state["poa_ratio"]
        _num = sum(st.session_state.nasa_irradiance[m] * _r_[m] * MONTH_DAYS[m] for m in range(12))
        _den = sum(st.session_state.nasa_irradiance[m] * MONTH_DAYS[m] for m in range(12))
        _tf = (_num / _den) if _den > 0 else 1.0

    _b_lo, _b_hi = 1500 * _tf, 1750 * _tf
    _techo, _piso = 1900 * _tf, 1450 * _tf

    if   _rend > _techo: _rc, _rn = "#f87171", "por encima de lo que entrega una planta real en México"
    elif _rend > _b_hi:  _rc, _rn = "#fbbf24", "alto — solo con recurso excepcional y baja temperatura"
    elif _rend >= _piso: _rc, _rn = "#4ade80", "dentro del rango observado en México"
    else:                _rc, _rn = "#fbbf24", "por debajo del piso observado — revisa PR o recurso"

    st.markdown(
        f'<div style="font-size:12px;color:#94a3b8;margin-top:4px;">'
        f'Rendimiento implícito '
        f'<b style="color:{_rc};font-size:14px;">{_rend:,.0f} kWh/kWp/año</b> — {_rn}.'
        f'<br>Banda de referencia {_b_lo:,.0f}–{_b_hi:,.0f} kWh/kWp'
        + (f' (1,500–1,750 observados en coplanar, escalados por el factor de '
           f'transposición {_tf:.3f}).' if _TRANSP else
           ' observados en sistemas reales en México.')
        + '</div>',
        unsafe_allow_html=True)

    # Degradación anual
    st.markdown("---")
    panel_degradation = st.slider(
        "Degradación anual (%/año)", 0.0, 2.0, 0.50, 0.05, key="degradacion_anual",
        help="Pérdida de potencia por año después del primer año (el escalón inicial "
             "se configura aparte como LID). Las garantías de módulos mono-Si actuales "
             "rondan 0.40–0.55 %/año, así que 0.50 % es el valor de trabajo y 1.00 % un "
             "supuesto conservador. El paso de 0.05 % permite capturar la tasa exacta "
             "de la garantía del fabricante.")
    lid_pct = st.slider(
        "Pérdida de primer año · LID (%)", 0.0, 3.0, 1.0, 0.1, key="lid_pct",
        help="Light Induced Degradation / LeTID: caída inicial del módulo durante el "
             "primer año, adicional a la degradación anual. Típico 1–2 % en mono-Si "
             "PERC/TOPCon. Las garantías de potencia se escriben con este escalón.")

    st.markdown("---")
    st.markdown("#### 💰 Referencia financiera")
    st.markdown("""
<div style="background:#1a1008;border-left:3px solid #f59e0b;border-radius:0 6px 6px 0;
     padding:8px 10px;font-size:11px;color:#92400e;margin-bottom:10px;">
  ⚠️ <b>Solo se usan en la pestaña Turnkey Solar.</b><br>
  En la pestaña PPA estos parámetros <u>no aplican</u>; el PPA tiene sus propias
  tasas y costos configurables dentro de esa pestaña.
</div>
""", unsafe_allow_html=True)
    tarifa    = st.slider("Tarifa ref. área (MXN/kWh)", 1.0, 8.0, 2.80, 0.10, key="tarifa",
                          help="Usada en modo 'Por área'. En modo recibo CFE se usa la tarifa del recibo.")
    inflation = st.slider("Inflación tarifa anual (%)", 0.0, 10.0, 4.0, 0.5, key="inflation")
    discount_rate = st.slider("Tasa de descuento (%)", 0.0, 30.0, 12.0, 0.5, key="discount_rate",
                              help="Tasa usada para evaluación")
    usd_to_mxn    = st.slider("Tipo de Cambio (MXN por USD)", 16.0, 22.0, 17.50, 0.1, key="usd_to_mxn",
                              help="Tipo de cambio para evaluación financiera")
    vida_util = st.slider("Vida útil (años)", 10, 30, 25, 1, key="vida_util")
    costo_kwp = st.slider("Costo ref. instalación (USD/kWp)", 400, 2000, 700, 25, key="costo_kwp")
    om_pct_sidebar = st.slider("O&M anual (% inversión MXN)", 0.5, 4.0, 1.7, 0.1, key="om_pct_sidebar",
                               help="Operación y mantenimiento anual como % de la inversión en MXN")
    seguro_pct_sidebar = st.slider(
        "Seguros y otros (% inversión MXN)", 0.0, 1.5, 0.50, 0.05, key="seguro_pct_sidebar",
        help="Seguro de daños y responsabilidad civil sobre el activo. El modelo PPA ya lo "
             "cobraba; se añade aquí para que el mismo sistema físico tenga la misma "
             "estructura de costo en ambas pestañas.")

    st.markdown("##### Reposición de equipo")
    inv_replace_year = st.slider(
        "Año de reemplazo del inversor", 0, 25, 12, 1, key="inv_replace_year",
        help="0 = sin reemplazo. El inversor es el componente de vida más corta del "
             "sistema (garantías típicas 10–12 años frente a 25 del módulo); omitir "
             "su reposición sobreestima el VPN a 25 años.")
    inv_costo_kw = st.number_input(
        "Costo de reposición (USD/kW AC)", 0.0, 500.0, 90.0, 5.0, key="inv_costo_kw",
        help="Costo TOTAL de reponer el inversor por kW AC instalado: equipo más mano de "
             "obra, maniobra y puesta en marcha. El equipo solo ronda 40–70 USD/kW; con "
             "instalación, 80–110. Se multiplica por los kW AC efectivos, así que se "
             "ajusta solo al cambiar el dimensionamiento o la relación DC/AC.")
    inv_replace_esc = st.slider(
        "Escalador del precio del inversor (%/año)", -3.0, 5.0, 0.0, 0.5,
        key="inv_replace_esc",
        help="Default 0 %: los inversores llevan años bajando de precio en términos "
             "reales. Inflarlos al INPC sobreestima el costo futuro (~38 % a 11 años). "
             "Ponlo negativo si esperas que la tendencia continúe.")
    inv_replace_pct = 10.0   # respaldo si no hay dimensionamiento de inversores

    st.markdown("##### Financiamiento")
    con_deuda_tk = st.checkbox(
        "Apalancar el proyecto", value=False, key="tk_con_deuda",
        help="Sin marcar, el modelo asume compra de contado y el desembolso inicial es el "
             "CAPEX completo. Al marcarlo, los flujos pasan a ser al accionista (FCFE), el "
             "desembolso inicial es sólo el equity y la TIR reportada es la del capital propio.")
    if con_deuda_tk:
        deuda_pct_tk   = st.slider("Deuda (% del CAPEX)", 0, 90, 70, 5, key="tk_deuda_pct")
        tasa_deuda_tk  = st.slider("Tasa de la deuda (%)", 5.0, 25.0, 13.0, 0.5, key="tk_tasa_deuda")
        plazo_deuda_tk = st.slider("Plazo del crédito (años)", 3, 20, 10, 1, key="tk_plazo_deuda")
    else:
        deuda_pct_tk   = 0.0
        tasa_deuda_tk  = 0.0
        plazo_deuda_tk = 0

    st.markdown("##### Impuestos")
    aplicar_isr = st.checkbox(
        "Modelar ISR", value=False, key="aplicar_isr",
        help="Sin marcar, todos los resultados son ANTES de impuestos.")
    if aplicar_isr:
        isr_pct = st.slider("Tasa de ISR (%)", 0.0, 40.0, 30.0, 1.0, key="isr_pct")
        deduccion_art34 = st.checkbox(
            "Deducción acelerada Art. 34 LISR (100 % año 1)", value=True,
            key="deduccion_art34",
            help="LISR Art. 34 fracc. XIII: deducción del 100 % de la inversión en "
                 "maquinaria de generación de energía de fuentes renovables en el "
                 "ejercicio de la inversión, sujeta a operar el equipo un mínimo de "
                 "5 años. Sin marcar se aplica línea recta sobre la vida útil. "
                 "Verificar la redacción vigente con tu asesor fiscal.")
        _perfil = st.radio(
            "¿Quién capta el escudo fiscal?",
            ["Causante con otras utilidades", "SPV sin otros ingresos"],
            key="perfil_fiscal",
            help="Con la deducción del Art. 34 la base gravable del año 1 se vuelve muy "
                 "negativa. Convertir eso en efectivo inmediato SÓLO es válido si el "
                 "contribuyente tiene otras utilidades contra las cuales aplicarlo. "
                 "Una sociedad de propósito específico debe arrastrarlo como pérdida "
                 "fiscal amortizable contra utilidades futuras del propio proyecto.")
        escudo_inmediato = _perfil.startswith("Causante")
    else:
        isr_pct = 0.0
        deduccion_art34 = False
        escudo_inmediato = True

    st.markdown("---")
    st.markdown(f"<div style='font-size:11px;color:#4b5563;'>v3.1 · NASA POWER {NASA_START}–{NASA_END} · México</div>",
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


tab1, tab3, tab4 = st.tabs(["  ☀️ Turnkey Solar", "  📄 PPA Solar", "  🧾 Comprador"])
# La irradiancia que consume el modelo es la del PLANO DEL GENERADOR (POA).
# En modo coplanar POA = GHI y el ratio es None, así que no se toca nada.
# En modo inclinado se aplica el factor Hay-Davies mes a mes, tanto al promedio
# climatológico como a cada año de la serie histórica — el P90 tiene que
# calcularse sobre la misma magnitud que la generación, no sobre GHI cruda.
_POA_R = st.session_state.get("poa_ratio")

if _POA_R and len(_POA_R) == 12:
    active_irr = [st.session_state.nasa_irradiance[m] * _POA_R[m] for m in range(12)]
    active_irr_por_anio = {
        _y: [_v[m] * _POA_R[m] for m in range(12)]
        for _y, _v in st.session_state.nasa_irr_por_anio.items()
    }
    IRR_PLANO = "POA (plano inclinado)"
else:
    active_irr          = st.session_state.nasa_irradiance
    active_irr_por_anio = st.session_state.nasa_irr_por_anio
    IRR_PLANO = "GHI (horizontal · coplanar)"

# Nota metodológica sobre el plano de cálculo. Se inyecta en el banner de la UI,
# en el PDF y en los Términos de Referencia para que el proveedor sepa contra qué
# supuesto está cotizando. Un número de generación sin decir sobre qué plano se
# calculó no es auditable.
if _POA_R and len(_POA_R) == 12:
    _b_ = st.session_state.get("geom_tilt", 0.0)
    _a_ = st.session_state.get("geom_azim", 180.0)
    _az_l = st.session_state.get("geom_az_lbl", "Sur (óptimo)")
    _f_ = (sum(_POA_R[m] * st.session_state.nasa_irradiance[m] * MONTH_DAYS[m]
               for m in range(12))
           / max(1e-9, sum(st.session_state.nasa_irradiance[m] * MONTH_DAYS[m]
                           for m in range(12))))
    GEOM_ETIQUETA = f"β={_b_:.0f}° · azimut {_a_:.0f}° ({_az_l}) · POA/GHI={_f_:.4f}"
    GEOM_NOTA = (
        f"CÁLCULO SOBRE PLANO INCLINADO: la irradiancia horizontal de NASA POWER se "
        f"transpuso al plano del generador con el modelo Hay-Davies para una "
        f"inclinación de {_b_:.0f}° y azimut de brújula {_a_:.0f}°, dando un factor "
        f"POA/GHI de {_f_:.4f}. El PR es por tanto un PR de sistema, no absorbe "
        f"pérdida de orientación. La transposición usa el día representativo mensual "
        f"y no modela sombreado cercano ni el perfil horario real."
    )
    GEOM_NOTA_CORTA = (
        f"Plano inclinado β={_b_:.0f}°, azimut {_a_:.0f}°. Transposición Hay-Davies, "
        f"factor POA/GHI {_f_:.4f}."
    )
else:
    GEOM_ETIQUETA = "Coplanar · POA/GHI = 1.0000"
    GEOM_NOTA = (
        "CÁLCULO COPLANAR: la generación se estima sobre irradiancia HORIZONTAL "
        "(GHI de NASA POWER), sin transposición al plano del generador. Equivale a "
        "suponer módulos coplanares sobre cubierta plana o de baja pendiente; el PR "
        "absorbe la pérdida de orientación. Un arreglo inclinado al sur puede rendir "
        "hasta 6 % más y uno al poniente hasta 4 % menos."
    )
    GEOM_NOTA_CORTA = "Coplanar sobre irradiancia horizontal (GHI), sin transposición."


# True cuando NO se han cargado datos de NASA para el sitio y la herramienta está
# corriendo sobre DEFAULT_IRR — una climatología fija de CDMX. Aplicarla a
# Mexicali o a Villahermosa produce un error de recurso de dos dígitos, así que
# los entregables quedan bloqueados hasta cargar el dato real.
usando_irr_default = not st.session_state.get("nasa_source_label")


def irr_source_banner():
    lbl = st.session_state.nasa_source_label
    if lbl:
        st.markdown(
            f'<div class="nasa-box">🌍 NASA POWER · Climatología {NASA_START}–{NASA_END} · {lbl} · Editable</div>',
            unsafe_allow_html=True)
    else:
        st.error(
            "🔴 **Irradiancia de respaldo — NO es el recurso de este sitio.** "
            "Se está usando la climatología fija de CDMX porque no se han cargado "
            "datos de NASA POWER. La generación, el P90 y todo el modelo financiero "
            "son inválidos para cualquier otra ubicación. "
            "Pulsa **🌍 Obtener irradiancia NASA POWER** en el sidebar. "
            "La exportación de PDF y Word está deshabilitada hasta entonces."
        )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRE-SIZING / TOR
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    # Espacio reservado para el encabezado de resultados. Streamlit ejecuta el
    # script de arriba abajo, así que el hero no puede calcularse antes de leer
    # los inputs; el placeholder aparta el lugar en la parte superior y se llena
    # más abajo, una vez que ya existen los números.
    _hero_slot = st.empty()

    col_p, col_r = st.columns([1.2, 1], gap="large")

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
            paper_bgcolor="#17191f",
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
    with col_r:
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

    # ── Datos del recibo CFE — a ancho completo ──────────────────────────────
    if not uso_area:
        # ── Datos del recibo CFE — histórico mensual ──────────────────────
        st.markdown('<div class="section-header">Histórico mensual (12 meses)</div>', unsafe_allow_html=True)
        st.markdown('<div class="nasa-box">📅 Ingresa el consumo y tarifa de cada mes. El importe se calcula automáticamente. Puedes obtener los datos de tus recibos bimestrales (divide entre 2) o del portal CFE.</div>', unsafe_allow_html=True)

        uso_historico = True  # único modo disponible

        # Defaults razonables
        cons_default = [500.0, 480.0, 460.0, 450.0, 470.0, 550.0,
                        600.0, 580.0, 510.0, 470.0, 460.0, 520.0]
        tar_default  = [2.80] * 12

        st.markdown('<div class="section-header">Consumo y tarifa mensual</div>', unsafe_allow_html=True)

        # Construir df base
        # ── Tabla editable: solo Consumo y Tarifa son editables ──────────
        # El Importe se recalcula automáticamente cada render.
        df_input = pd.DataFrame({
            "Mes":              MONTHS,
            "Consumo (kWh)":    cons_default,
            "Tarifa (MXN/kWh)": tar_default,
        })

        # Las dos tablas van lado a lado: a la izquierda la editable, a la
        # derecha el importe recalculado. Antes iban apiladas y repetían las
        # mismas tres columnas, obligando a hacer scroll para comparar.
        _t_edit, _t_calc = st.columns(2, gap="small")

        with _t_edit:
            df_edit = st.data_editor(
                df_input,
                column_config={
                    "Mes":              st.column_config.TextColumn(disabled=True, width="small"),
                    "Consumo (kWh)":    st.column_config.NumberColumn(
                        min_value=0.0, max_value=12_000_000.0, step=10.0, format="%.0f"),
                    "Tarifa (MXN/kWh)": st.column_config.NumberColumn(
                        min_value=0.0, max_value=50.0, step=0.0001, format="%.4f",
                        help="Precio medio pagado ese mes"),
                },
                hide_index=True, use_container_width=True, key="hist_mensual",
                num_rows="fixed", height=460,
            )

        cons_edit = [float(v) for v in df_edit["Consumo (kWh)"].tolist()]
        tar_edit  = [float(v) for v in df_edit["Tarifa (MXN/kWh)"].tolist()]
        imp_calc  = [round(cons_edit[i] * tar_edit[i], 0) for i in range(12)]

        with _t_calc:
            # Sólo el importe: consumo y tarifa ya se ven en la tabla de al lado.
            df_show = pd.DataFrame({
                "Mes":           MONTHS,
                "Importe (MXN)": [f"${v:,.0f}" for v in imp_calc],
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True,
                         height=460)

        st.caption("Importe = Consumo × Tarifa · se recalcula al editar la tabla de la izquierda.")

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



    # ── Cálculos y resultados — ancho completo ───────────────────────────────

    irr_tuple = tuple(irr_vals)

    if uso_area:
        sz = dict(calc_sizing_area(area_total, occ_factor, panel_wp, panel_area,
                                   irr_tuple, effective_pr))
        monthly_cons_ref = None
        monthly_tar_ref  = None
        tarifa_efectiva  = tarifa
        uso_historico_r  = False
    else:
        uso_historico_r = uso_historico
        if uso_historico:
            _ok_r, _msg_r = _validate_recibo_inputs(monthly_cons_input, monthly_tar_input)
            if not _ok_r:
                # El hero nunca llega a calcularse en este camino: se llena el
                # placeholder reservado arriba para que no quede un hueco mudo.
                _hero_slot.warning(
                    f"⚠️ **Datos de recibo inválidos** — {_msg_r} "
                    f"Corrige la tabla de consumo y tarifa para ver los resultados.")
                st.error(f"⚠️ Datos de recibo inválidos: {_msg_r}")
                st.stop()
            # dict(...) rompe la referencia al objeto cacheado por Streamlit:
            # más abajo se recalculan cobertura y ahorro sobre generación AC y
            # mutar el cache directamente contaminaría llamadas posteriores.
            sz = dict(calc_sizing_recibo_kwp(
                monthly_cons_input, monthly_tar_input,
                max(kwp_manual, 0.5),
                panel_wp, panel_area,
                irr_tuple, effective_pr,
                occ_factor=occ_factor))  # FIX: pasar factor de ocupación del usuario
            monthly_cons_ref = sz["monthly_cons"]
            monthly_tar_ref  = sz["monthly_tarifas"]
            tarifa_efectiva  = sz["tarifa_media_pond"]

    # Referencias de consumo/tarifa previas al ajuste por inversor.
    monthly_cons_ref_pre = monthly_cons_ref
    monthly_tar_ref_pre  = monthly_tar_ref


    n_panels   = sz["n_panels"]
    kwp        = sz["kwp"]
    area_util  = sz["area_util"]
    area_used  = sz["area_used"]          # superficie neta de módulos
    # Área que realmente ocupa la instalación: módulos + separación entre
    # filas, pasillos de mantenimiento y retiros de perímetro.
    area_instalacion = area_used * (1 + HOLGURA_INSTALACION_PCT / 100)
    # Generación antes de saturación del inversor. NO es DC: el PR ya incluye
    # la eficiencia de conversión. Ver nota en compute_p90().
    monthly_gen_pre_clip = sz["monthly_gen"]

    # ── Inversores: dimensionamiento y recorte (clipping) ─────────────────
    # La generación que se usa de aquí en adelante es AC (post-inversor), que
    # es la que efectivamente llega al punto de medición y desplaza consumo.
    inv_res = calc_inversores(kwp, inv_unit_kw, dc_ac_objetivo,
                              irr_tuple, effective_pr, monthly_gen_pre_clip,
                              n_inv_manual=n_inv_manual)
    # La disponibilidad se aplica después del inversor: es tiempo fuera de
    # servicio, no una pérdida de conversión.
    _disp = disponibilidad_pct / 100.0
    monthly_gen = [round(g * _disp, 1) for g in inv_res["monthly_gen_ac"]]
    annual_gen  = sum(monthly_gen)

    # Recalcular cobertura y ahorro sobre generación AC (el sizing los había
    # calculado sobre DC, antes de conocer el recorte del inversor).
    if not uso_area and monthly_cons_ref_pre is not None:
        _cons = monthly_cons_ref_pre
        _tar  = monthly_tar_ref_pre
        sz["energia_cubierta"] = [min(monthly_gen[m], _cons[m]) for m in range(12)]
        sz["ahorro_mensual"]   = [sz["energia_cubierta"][m] * _tar[m] for m in range(12)]
        sz["ahorro_anual"]     = sum(sz["ahorro_mensual"])
        sz["excedente"]        = [monthly_gen[m] - _cons[m] for m in range(12)]
        sz["cobertura_pct"]    = [min(100.0, monthly_gen[m] / _cons[m] * 100)
                                  if _cons[m] > 0 else 0.0 for m in range(12)]
        sz["cobertura_anual"]  = (sum(sz["energia_cubierta"]) / sum(_cons) * 100
                                  if sum(_cons) > 0 else 0.0)
        sz["monthly_gen"]      = monthly_gen
        sz["annual_gen"]       = annual_gen

    # Fracción de la generación que efectivamente desplaza consumo.
    # El excedente vertido a la red se valora en $0 (criterio conservador).
    if not uso_area and "energia_cubierta" in sz and annual_gen > 0:
        autoconsumo_frac = min(1.0, sum(sz["energia_cubierta"]) / annual_gen)
    else:
        autoconsumo_frac = 1.0

    daily_avg   = annual_gen / 365
    # CO2 evitado. Se calcula más abajo sobre `annual_gen_base` para que use
    # la MISMA base de excedencia que el resto de la herramienta (P90). Aquí
    # queda el valor provisional a P50 por si no hay serie NASA cargada.
    co2_saved   = annual_gen * CO2_FACTOR_KG_KWH   # kg/año  (factor SEN)
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

    # ── P50 / P75 / P90 / P99 desde la serie interanual NASA POWER ────────
    # Una sola llamada devuelve todos los niveles YA EN AC: el recorte del
    # inversor y la disponibilidad se aplican año por año dentro de
    # compute_p90, antes de la estadística, porque son transformaciones
    # físicas del recurso y no ajustes sobre percentiles ya calculados.
    # `ratio_irr` propaga la edición manual de la tabla de irradiancia, de
    # modo que P50 y P90 siempre salen de la misma serie.
    _irr_edit = sum(irr_vals[m] * MONTH_DAYS[m] for m in range(12))
    _irr_nasa = sum(active_irr[m] * MONTH_DAYS[m] for m in range(12))
    p50_real, p90_real, gen_por_anio, sigma_det = compute_p90(
        active_irr_por_anio, kwp, effective_pr,
        ratio_irr=(_irr_edit / _irr_nasa) if _irr_nasa > 0 else 1.0,
        dc_ac_real=inv_res["dc_ac_real"],
        disponibilidad=_disp,
    )
    has_p90  = p50_real is not None
    p75_real = sigma_det.get("p75") if has_p90 else None
    p99_real = sigma_det.get("p99") if has_p90 else None

    # Para el TOR usamos P50 = generación con irr media editada
    p50 = annual_gen
    p90 = p90_real if has_p90 else None

    # Escalar el ahorro capeado a la base P90, que es la que alimenta el
    # modelo financiero. Sin esto el hero mostraría un payback calculado a
    # P50 y el modelo otro a P90 — y ambos se imprimían en el mismo PDF.
    # `base_label_gen` identifica sobre qué nivel de excedencia está construido
    # TODO lo que se muestra: hero, tabla mensual y modelo financiero. Antes el
    # hero reportaba P90 mientras la tabla mensual seguía en P50, así que la suma
    # de los doce meses no daba el número del hero.
    _esc_p90       = 1.0
    base_label_gen = "P50"
    if has_p90 and p50_real and p50_real > 0:
        _esc_p90       = p90_real / p50_real
        base_label_gen = "P90"

    # Desglose mensual en la MISMA base que el hero. De aquí salen la tabla, las
    # gráficas y el ahorro anual, de modo que Σ(meses) = ahorro del hero.
    monthly_gen_base = [g * _esc_p90 for g in monthly_gen]
    if not uso_area and monthly_cons_ref_pre is not None:
        monthly_cub_base = [min(monthly_gen_base[m], monthly_cons_ref_pre[m])
                            for m in range(12)]
        monthly_ahorro_base = [monthly_cub_base[m] * monthly_tar_ref_pre[m]
                               for m in range(12)]
        monthly_exc_base = [monthly_gen_base[m] - monthly_cons_ref_pre[m]
                            for m in range(12)]
        monthly_cob_base = [min(100.0, monthly_gen_base[m] / monthly_cons_ref_pre[m] * 100)
                            if monthly_cons_ref_pre[m] > 0 else 0.0 for m in range(12)]
        ahorro1 = sum(monthly_ahorro_base)
        _sg = sum(monthly_gen_base)
        autoconsumo_frac = min(1.0, sum(monthly_cub_base) / _sg) if _sg > 0 else 1.0
        cobertura_anual_base = (sum(monthly_cub_base) / sum(monthly_cons_ref_pre) * 100
                                if sum(monthly_cons_ref_pre) > 0 else 0.0)
    else:
        # Modo por área: no hay recibo, así que toda la generación se valora a la
        # tarifa de referencia. El desglose mensual se construye igual para que la
        # suma cuadre con el hero.
        monthly_cub_base    = list(monthly_gen_base)
        monthly_ahorro_base = [g * tarifa_efectiva for g in monthly_gen_base]
        monthly_exc_base    = [0.0] * 12
        monthly_cob_base    = [0.0] * 12
        ahorro1 = sum(monthly_ahorro_base)
        cobertura_anual_base = 0.0
    annual_gen_base = sum(monthly_gen_base)
    # Recalcular el CO2 sobre la base efectiva (P90 si hay serie histórica).
    # Subestimar el abatimiento es el lado seguro de un claim ambiental.
    co2_saved   = annual_gen_base * CO2_FACTOR_KG_KWH
    co2_saved_t = co2_saved / 1000
    payback = inversion_mxn / ahorro1 if ahorro1 > 0 else 999

    # ── Modelo financiero — cacheado ──────────────────────────────────────
    # Si P90 está disponible se usa como base conservadora (recomendado);
    # si no, se cae a P50 (generación con irradiancia media).
    gen_para_fm = p90_real if has_p90 else annual_gen
    fm_base_label = "P90" if has_p90 else "P50"
    fm = calc_financial_model(
        gen_para_fm, kwp, float(inversion),
        tarifa_efectiva, inflation, discount_rate,
        panel_degradation, vida_util, usd_to_mxn,
        om_pct=om_pct_sidebar,
        autoconsumo_frac=autoconsumo_frac,
        lid_pct=lid_pct,
        inv_replace_year=inv_replace_year,
        inv_replace_pct=inv_replace_pct,
        inv_replace_mxn=inv_res["ac_total_kw"] * inv_costo_kw * usd_to_mxn,
        inv_replace_esc=inv_replace_esc,
        isr_pct=isr_pct,
        deduccion_art34=deduccion_art34,
        escudo_inmediato=escudo_inmediato,
        seguro_pct=seguro_pct_sidebar,
        con_deuda=con_deuda_tk,
        deuda_pct=deuda_pct_tk,
        tasa_deuda_pct=tasa_deuda_tk,
        plazo_deuda_tk=plazo_deuda_tk,
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
    # Desembolso inicial del inversionista: el CAPEX si compra de contado, o
    # sólo el equity si el proyecto está apalancado. acum_nominal / acum_desc
    # ya arrancan de este valor dentro de calc_financial_model.
    desembolso_inicial = fm.get("equity_mxn", fm["inv_mxn"])
    deuda_mxn_tk  = fm.get("deuda_mxn", 0.0)
    vpn           = fm["vpn"]
    tir           = fm["tir"]
    tir_metodo    = fm.get("tir_metodo", "TIR")
    tir_str       = f"{tir:.1f}%" if tir is not None else "N/A"
    # Etiqueta del KPI: si hubo múltiples cambios de signo en los flujos (p. ej.
    # por el reemplazo del inversor) se reporta MIRR, que sí es única.
    tir_sub       = (f"MIRR · vs {discount_rate}% tasa desc." if tir_metodo == "MIRR"
                     else f"vs {discount_rate}% tasa desc.")
    pb_simple     = fm["pb_simple"]
    pb_simple_str = f"{pb_simple:.1f} años" if pb_simple is not None else f">{vida_util} años"
    pb_disc       = fm["pb_disc"]
    pb_disc_str   = f"{pb_disc:.1f} años" if pb_disc is not None else f">{vida_util} años"
    lcoe          = fm["lcoe"]

    # ── TOR HERO — se pinta en el placeholder reservado arriba del todo ────
    area_label = (f"{area_instalacion:,.0f} m² de instalación ({area_used:,.0f} de módulos) "
                  f"sobre {area_util:,.0f} m² útiles" if uso_area
                  else f"{area_instalacion:,.0f} m² de instalación estimados")
    _hero_slot.markdown(f"""
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
      <span class="th-label">ÁREA INSTALACIÓN</span>
      <span class="th-val">{area_instalacion:,.0f}</span>
      <span class="th-unit">m² · +{HOLGURA_INSTALACION_PCT:.0f}% sobre módulos</span>
    </div>
    <div class="th-item">
      <span class="th-label">RELACIÓN DC/AC</span>
      <span class="th-val">{inv_res['dc_ac_real']:.2f}</span>
      <span class="th-unit">{inv_res['ac_total_kw']:,.0f} kW AC{f" · {inv_res['n_inv']}×{inv_res['inv_unit_kw']:,.0f} kW" if inv_res['modo_dim']=='manual' else ' · asignada'}</span>
    </div>
    <div class="th-item">
      <span class="th-label">GENERACIÓN AÑO 1</span>
      <span class="th-val">{p50/1000:,.1f}</span>
      <span class="th-unit">MWh/año · P50</span>
    </div>
    <div class="th-item">
      <span class="th-label">GENERACIÓN P90</span>
      <span class="th-val">{"—" if not has_p90 else f"{p90/1000:,.1f}"}</span>
      <span class="th-unit">{"Carga NASA" if not has_p90 else "MWh/año · base del modelo"}</span>
    </div>
    <div class="th-item">
      <span class="th-label">COBERTURA SOLAR</span>
      <span class="th-val">{"—" if uso_area or not monthly_cons_ref else f"{cobertura_anual_base:.1f}"}</span>
      <span class="th-unit">{"sin recibo de referencia" if uso_area or not monthly_cons_ref else f"% del consumo · base {base_label_gen}"}</span>
    </div>
    <div class="th-item">
      <span class="th-label">CO₂ EVITADO</span>
      <span class="th-val">{co2_saved_t:,.0f}</span>
      <span class="th-unit">t/año · base {base_label_gen} · {CO2_FACTOR_KG_KWH} kg/kWh</span>
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
      <span class="th-unit">años · flujos nominales</span>
    </div>
    <div class="th-item">
      <span class="th-label">PAYBACK DESCONTADO</span>
      <span class="th-val">{f"{pb_disc:.1f}" if pb_disc is not None else f">{vida_util}"}</span>
      <span class="th-unit">años · a {discount_rate:.0f}% de descuento</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── ALERTA REGULATORIA para Generación Distribuida ─────────────────────
    # FIX — el umbral regulatorio aplica a la capacidad de INTERCONEXIÓN, que es
    # la potencia AC del inversor, no a la potencia pico DC del generador. Antes
    # se comparaba kWp DC contra 699, un número que además contradecía el propio
    # texto del TOR de esta herramienta ("Permiso CRE si > 0.5 MW"). Con DC/AC de
    # 1.30, un arreglo de 690 kWp DC entrega 531 kW AC y excedía el umbral sin
    # que la herramienta avisara.
    _ac_kw     = inv_res["ac_total_kw"]
    _dc_ac     = inv_res["dc_ac_real"]
    if _ac_kw > LIMITE_GD_KW_AC:
        st.error(
            f"⚠️ **{_ac_kw:,.0f} kW AC — supera el límite de Generación Distribuida "
            f"({LIMITE_GD_KW_AC:,.0f} kW AC).** El proyecto requiere permiso CRE y "
            f"deja de calificar para el contrato de interconexión simplificado. "
            f"El generador es de {kwp:,.1f} kWp DC con relación DC/AC {_dc_ac:.2f}."
        )
    elif _ac_kw > LIMITE_GD_KW_AC * 0.92:
        st.warning(
            f"⚠️ **{_ac_kw:,.0f} kW AC — a menos de 8 % del límite de GD "
            f"({LIMITE_GD_KW_AC:,.0f} kW AC).** Cualquier ajuste al alza cruza el umbral."
        )
    if uso_area:
        # Área máxima compatible con GD: se parte del límite AC y se sube a DC
        # con la relación DC/AC configurada.
        max_kwp_gd  = LIMITE_GD_KW_AC * dc_ac_objetivo
        area_max_gd = max_kwp_gd * 1000 / panel_wp * panel_area / (occ_factor / 100)
        st.caption(
            f"📏 Área máx. para GD: **{area_max_gd:,.0f} m²** "
            f"(≈{max_kwp_gd:,.0f} kWp DC = {LIMITE_GD_KW_AC:,.0f} kW AC "
            f"con DC/AC {dc_ac_objetivo:.2f} y {occ_factor}% de ocupación)")
    else:
        consumo_anual_ref = sum(monthly_cons_ref) if monthly_cons_ref else 0
        # OJO: esta razón NO es la cobertura. Es generación total entre consumo
        # total, sin capear mes a mes, así que puede superar el 100 % cuando el
        # sistema sobregenera en algunos meses. La cobertura real —cuánto del
        # consumo desplaza el sistema— es cobertura_anual_base y nunca pasa de 100.
        dimensionamiento_pct = annual_gen_base / max(consumo_anual_ref, 1) * 100
        st.caption(
            f"📊 Consumo anual: **{consumo_anual_ref:,.0f} kWh** · "
            f"Cobertura solar: **{cobertura_anual_base:.1f}%** (del consumo que desplaza) · "
            f"Dimensionamiento: **{dimensionamiento_pct:.1f}%** (generación ÷ consumo) · "
            f"Tarifa media: **${tarifa_efectiva:.3f}/kWh**")

    # ── Aviso de configuración manual de inversores ──────────────────────
    # ── Óptimo económico del DC/AC ───────────────────────────────────────
    # Se compara el ratio elegido contra el que maximiza el VPN por kW AC.
    # El óptimo NO es una constante: sube cuando baja el panel o sube la
    # tarifa, así que conviene revisarlo en cada proyecto y no fijar un
    # número de catálogo para siempre.
    _fd_opt = sum((1 - panel_degradation / 100) ** _y
                  * (1 + inflation / 100) ** _y
                  / (1 + discount_rate / 100) ** (_y + 1)
                  for _y in range(vida_util))
    _om_vp = ((om_pct_sidebar + seguro_pct_sidebar) / 100) * sum(
        (1 + inflation / 100) ** _y / (1 + discount_rate / 100) ** (_y + 1)
        for _y in range(vida_util))
    # Generación por kWp en cada mes, para que el óptimo vea cómo cae el
    # autoconsumo al subir el ratio.
    _irr_pr_mes = [irr_vals[m] * effective_pr * MONTH_DAYS[m] * _disp for m in range(12)]
    _r_opt, _af_opt = dc_ac_optimo(
        costo_dc_usd_kwp=costo_dc_marginal,
        rendimiento_kwh_kwp=(annual_gen / kwp) if kwp > 0 else 0.0,
        valor_kwh_mxn=tarifa_efectiva,
        usd_mxn=usd_to_mxn,
        factor_descuento=_fd_opt,
        ac_total_kw=inv_res["ac_total_kw"],
        monthly_irr_pr=_irr_pr_mes,
        monthly_cons=monthly_cons_ref_pre,
        om_frac_vp=_om_vp,
    )
    if _r_opt:
        _dcac_act = inv_res["dc_ac_real"]
        def _vpn_por_kwac(r):
            _kwp = inv_res["ac_total_kw"] * r
            _c = 1 - _clip_desde_dcac(r)
            _mg = [_kwp * _irr_pr_mes[m] * _c for m in range(12)]
            _t = sum(_mg)
            if monthly_cons_ref_pre and sum(monthly_cons_ref_pre) > 0 and _t > 0:
                _af = sum(min(_mg[m], monthly_cons_ref_pre[m]) for m in range(12)) / _t
            else:
                _af = 1.0
            return (_t * _af * tarifa_efectiva * _fd_opt
                    - _kwp * costo_dc_marginal * usd_to_mxn * (1 + _om_vp))
        _delta = _vpn_por_kwac(_r_opt) - _vpn_por_kwac(_dcac_act)
        _col = "#4ade80" if abs(_dcac_act - _r_opt) < 0.05 else "#facc15"
        st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:6px 0 4px;">
  <div class="snap-card">
    <div class="sc-label">DC/AC actual</div>
    <div class="sc-val" style="color:{_col};">{_dcac_act:.3f}</div>
    <div class="sc-sub">{inv_res['n_inv']} × {inv_res['inv_unit_kw']:,.0f} kW</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">DC/AC óptimo</div>
    <div class="sc-val" style="color:#22d3ee;">{_r_opt:.3f}</div>
    <div class="sc-sub">maximiza VPN por kW AC</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">VPN sobre la mesa</div>
    <div class="sc-val" style="color:{'#94a3b8' if _delta < 5000 else '#f59e0b'};font-size:14px;">
      ${_delta:,.0f}</div>
    <div class="sc-sub">MXN si movieras al óptimo</div>
  </div>
</div>
""", unsafe_allow_html=True)
        st.caption(
            f"El óptimo depende del costo marginal del panel (**{costo_dc_marginal:,.0f} USD/kWp**), "
            f"del valor del kWh (**${tarifa_efectiva:.3f}**) y — si hay recibo — de **cuánto "
            f"consume el cliente**"
            + (f": en el óptimo el autoconsumo baja a **{_af_opt*100:.1f}%** porque el excedente "
               f"se vierte a $0." if _af_opt is not None else ".")
            + f" Quedarse **por debajo** del óptimo cuesta ~4× menos que pasarse, así que en "
              f"propuesta conviene sesgarse a la baja y ajustar en ingeniería de detalle."
        )

    if inv_res.get("fuera_de_curva"):
        st.error(
            f"🔴 **DC/AC {inv_res['dc_ac_real']:.2f} fuera del rango validado.** "
            f"{inv_res['nota']}")
    if inv_res["modo_dim"] == "manual":
        _auto = inv_res["n_inv_auto"]
        if inv_res["estado"] in ("excesivo", "alto"):
            st.warning(
                f"⚠️ **{inv_res['n_inv']} inversores dan DC/AC {inv_res['dc_ac_real']:.2f}** "
                f"y un recorte de **{inv_res['clip_frac']*100:.2f}%** "
                f"({inv_res['clip_kwh']:,.0f} kWh/año). {inv_res['nota']} "
                f"Con {_auto} unidades quedarías en el objetivo de {dc_ac_objetivo:.2f}.")
        elif inv_res["estado"] == "sub":
            st.info(
                f"ℹ️ **{inv_res['n_inv']} inversores dan DC/AC {inv_res['dc_ac_real']:.2f}** — "
                f"inversor sobredimensionado, sin recorte pero con CAPEX AC desaprovechado. "
                f"Con {_auto} unidades alcanzarías el objetivo de {dc_ac_objetivo:.2f}.")

    # ── Aviso de excedentes vertidos ─────────────────────────────────────
    # El modelo valora el excedente en $0. Mientras la cobertura se mantiene
    # por debajo de ~80 % el efecto es nulo; arriba de ahí crece rápido y el
    # usuario debe verlo antes de leer el VPN.
    if autoconsumo_frac < 0.995:
        _exc_kwh = annual_gen * (1 - autoconsumo_frac)
        st.warning(
            f"⚠️ **{(1 - autoconsumo_frac) * 100:.1f}% de la generación se vierte a la red** "
            f"({_exc_kwh:,.0f} kWh/año) y el modelo la valora en **$0**. "
            f"El retorno marginal de cada kWp adicional cae con fuerza a partir de este punto. "
            f"Si tu contrato de interconexión liquida excedentes, el ahorro real será mayor "
            f"que el mostrado."
        )
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
  <div style="border-top:1px solid #343841;margin-top:10px;padding-top:10px;">
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
    <span class="pc-val" style="color:#cbd5e1;">+35% montura/BOS</span>
      </div>
    </div>
  </div>

  <!-- Inversores -->
  <div style="border-top:1px solid #343841;margin-top:10px;padding-top:10px;">
    <div class="pc-title" style="margin-bottom:8px;">🔌 Bloque de inversores</div>
    <div class="pc-grid">
      <div class="pc-item">
    <span class="pc-label">{'Inversores' if inv_res['modo_dim']=='manual' else 'Equivalente en unidades'}</span>
    <span class="pc-val">{inv_res['n_inv']} × {inv_res['inv_unit_kw']:,.0f} kW</span>
      </div>
      <div class="pc-item">
    <span class="pc-label">Potencia AC total</span>
    <span class="pc-val">{inv_res['ac_total_kw']:,.0f} kW</span>
      </div>
      <div class="pc-item">
    <span class="pc-label">Relación DC/AC {'real' if inv_res['modo_dim']=='manual' else 'asignada'}</span>
    <span class="pc-val" style="color:{'#4ade80' if inv_res['estado']=='ok' else ('#facc15' if inv_res['estado'] in ('alto','sub') else '#f87171')};">
      {inv_res['dc_ac_real']:.3f}</span>
      </div>
      <div class="pc-item">
    <span class="pc-label">Pérdida por recorte</span>
    <span class="pc-val" style="color:{'#cbd5e1' if inv_res['clip_frac'] < 0.01 else '#f87171'};">
      {inv_res['clip_frac']*100:.2f}% · {inv_res['clip_kwh']:,.0f} kWh/a</span>
      </div>
    </div>
    <div style="font-size:10.5px;color:#94a3b8;margin-top:8px;line-height:1.45;">
      {inv_res['nota']}<br>
      {'Capacidad AC derivada de la relación asignada, sin redondear a unidades.' if inv_res['modo_dim']=='auto' else 'Capacidad AC de las unidades capturadas; el DC/AC es resultado.'}<br>
      Antes de saturación {inv_res['annual_gen_pre_clip']:,.0f} kWh → AC entregada {inv_res['annual_gen_ac']:,.0f} kWh/año.
      Recorte estimado con una ley de potencia ajustada a valores publicados para
      sistemas fijos, aplicada como <b>factor uniforme</b> a los doce meses. El total
      anual es el que alimenta el modelo; el perfil mensual del recorte requiere
      simulación horaria en PVsyst o Helioscope.
    </div>
  </div>

  <!-- HSP promedio anual -->
  <div style="border-top:1px solid #2e3138;margin-top:10px;padding-top:10px;">
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
  <div style="border-top:1px solid #2e3138;margin-top:10px;padding-top:10px;">
    <div class="pc-title" style="margin-bottom:8px;">🌿 Impacto ambiental año 1</div>
    <div class="pc-grid">
      <div class="pc-item">
    <span class="pc-label">CO₂ evitado</span>
    <span class="pc-val" style="color:#4ade80;">{co2_saved_t:,.2f} ton/año</span>
      </div>
      <div class="pc-item">
    <span class="pc-label">Factor de emisión utilizado</span>
    <span class="pc-val" style="font-size:11px;color:#94a3b8;font-family:Inter,sans-serif;">{CO2_FACTOR_KG_KWH} kg CO₂e/kWh · SEN 2024 · SEMARNAT/CRE 28-Feb-2025</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Si modo recibo: mostrar comparativa consumo vs generación ───────────
    if not uso_area and monthly_cons_ref:
        st.markdown(f'<div class="section-header">Generación vs Consumo mensual · base {base_label_gen}</div>',
                    unsafe_allow_html=True)

        # Todo el desglose sale de la misma base que el hero, de forma que
        # Σ(ahorro mensual) coincida exactamente con el ahorro año 1 reportado.
        excedente_m = monthly_exc_base
        coverage_m  = monthly_cob_base
        ahorro_m    = monthly_ahorro_base
        energy_cov  = monthly_cub_base
        gen_display = monthly_gen_base

        fig_cv = go.Figure()
        fig_cv.add_trace(go.Bar(x=MONTHS, y=monthly_cons_ref, name="Consumo",
            marker_color="#374151",
            hovertemplate="<b>%{x}</b><br>Consumo: %{y:,.0f} kWh<extra></extra>"))
        fig_cv.add_trace(go.Bar(x=MONTHS, y=energy_cov, name="Cubierto solar",
            marker_color=AMBER,
            hovertemplate="<b>%{x}</b><br>Cubierto: %{y:,.0f} kWh<extra></extra>"))
        fig_cv.add_trace(go.Scatter(x=MONTHS, y=gen_display, mode="lines+markers",
            name=f"Generación {base_label_gen}", line=dict(color=TEAL, width=2, dash="dot"),
            marker=dict(size=6, color=TEAL),
            hovertemplate="<b>%{x}</b><br>Generación: %{y:,.0f} kWh<extra></extra>"))
        lyt_cv = copy.deepcopy(PLOT_LAYOUT)
        lyt_cv.update({"height": 270, "barmode": "overlay",
                       "yaxis": dict(title="kWh", gridcolor="#343841"),
                       "legend": dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
                       "margin": dict(l=20, r=20, t=30, b=40)})
        fig_cv.update_layout(**lyt_cv)
        st.plotly_chart(fig_cv, use_container_width=True)

        # ── Resumen de ahorro por mes (reemplaza gráfica de tarifa) ──────────
        if uso_historico_r and monthly_tar_ref:
            st.markdown(f'<div class="section-header">Ahorro mensual · base {base_label_gen} · '
                        f'suma = ahorro año 1 del encabezado</div>', unsafe_allow_html=True)
            ahorro_html = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:0.75rem;">'
            for i, m in enumerate(MONTHS):
                color = "#4ade80" if ahorro_m[i] > 0 else "#f87171"
                ahorro_html += f"""
  <div style="background:#1e2028;border:0.5px solid #2e3138;border-radius:10px;padding:8px 6px;text-align:center;">
    <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">{m}</div>
    <div style="font-size:13px;font-weight:600;color:{color};font-family:'JetBrains Mono',monospace;">${ahorro_m[i]:,.0f}</div>
    <div style="font-size:9px;color:#94a3b8;margin-top:2px;">${monthly_tar_ref[i]:.3f}/kWh</div>
  </div>"""
            ahorro_html += '</div>'
            ahorro_html += f"""<div style="display:flex;justify-content:flex-end;font-size:12px;color:#94a3b8;margin-top:2px;">
  Ahorro anual total: <span style="color:#4ade80;font-weight:600;margin-left:6px;">${sum(ahorro_m):,.0f} MXN</span>
</div>"""
            st.markdown(ahorro_html, unsafe_allow_html=True)

        # ── Tabla mensual ──────────────────────────────────────────────────
        st.markdown(f'<div class="section-header">Tabla mensual detallada · base {base_label_gen}</div>',
                    unsafe_allow_html=True)
        tar_display = monthly_tar_ref if monthly_tar_ref else [tarifa_efectiva]*12
        df_tabla = pd.DataFrame({
            "Mes":               MONTHS,
            "Consumo (kWh)":    [f"{v:,.0f}" for v in monthly_cons_ref],
            "Generación (kWh)": [f"{v:,.0f}" for v in gen_display],
            "Cubierto (kWh)":   [f"{v:,.0f}" for v in energy_cov],
            "Cobertura (%)":    [f"{v:.1f}%" for v in coverage_m],
            "Excedente (kWh)":  [f"+{v:,.0f}" if v >= 0 else f"{v:,.0f}" for v in excedente_m],
            "Tarifa ($/kWh)":   [f"${t:.3f}" for t in tar_display],
            "Ahorro (MXN)":     [f"${v:,.0f}" for v in ahorro_m],
        })
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        st.caption(
            f"Generación, cobertura y ahorro están en base **{base_label_gen}** — la misma "
            f"que alimenta el modelo financiero. La suma de la columna Ahorro "
            f"(**${sum(ahorro_m):,.0f}**) es exactamente el *Ahorro año 1* del encabezado. "
            f"El ahorro de cada mes es min(generación, consumo) × tarifa de ese mes: "
            f"el excedente vertido a la red se valora en $0.")

        # cobertura_anual = Σ min(gen_mes, cons_mes) / Σ cons_mes × 100
        # Fórmula correcta: no cuenta excedente que va a red como cobertura del consumo
        cobertura_anual = cobertura_anual_base
        st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:8px;">
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Consumo anual</div>
    <div class="sc-val" style="font-size:14px;">{sum(monthly_cons_ref):,.0f}</div>
    <div class="sc-sub">kWh/año</div>
  </div>
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Cobertura solar</div>
    <div class="sc-val" style="color:#f59e0b;font-size:14px;">{cobertura_anual:.1f}%</div>
    <div class="sc-sub">del consumo que desplaza · máx 100%</div>
  </div>
  <div class="snap-card" style="min-height:80px;">
    <div class="sc-label">Dimensionamiento</div>
    <div class="sc-val" style="color:#94a3b8;font-size:14px;">{annual_gen_base / max(sum(monthly_cons_ref), 1) * 100:.1f}%</div>
    <div class="sc-sub">generación ÷ consumo · puede pasar 100%</div>
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

    # ── Gráfica mensual y variabilidad interanual, apiladas a ancho completo ──
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
        "height": 420, "barmode": "group",
        "title": dict(text="Generación Mensual (P50 con irradiancia media)", font=dict(size=15)),
        "yaxis":  dict(title="kWh generados", gridcolor="#343841", tickformat=",", rangemode="tozero"),
        "yaxis2": dict(title="Irradiancia (kWh/m²/día)", overlaying="y", side="right",
                       range=[0, max(irr_vals) * 1.25],
                       tickfont=dict(color=ROSE), tickformat=".2f"),
        "legend": dict(orientation="h", y=-0.22, x=0.5, xanchor="center", yanchor="top",
                       font=dict(size=13), bgcolor="rgba(0,0,0,0)",
                       bordercolor="#343841", borderwidth=1),
        "margin": dict(l=20, r=80, t=60, b=100),
        "hovermode": "x unified",
    })
    fig1.update_layout(**layout1)
    st.plotly_chart(fig1, use_container_width=True)
    if _POA_R and len(_POA_R) == 12:
        st.info(
            f"**Plano inclinado — {GEOM_ETIQUETA}.** La irradiancia horizontal de "
            "NASA POWER se transpuso al plano del generador con el modelo "
            "**Hay-Davies**, que separa la difusa en su parte circunsolar y su parte "
            "isotrópica. El PR que estás usando es un PR de sistema: ya no absorbe "
            "pérdida de orientación.\n\n"
            "Lo que este método **sí** captura: inclinación, azimut, albedo y el "
            "reparto estacional (un arreglo inclinado gana en invierno y pierde en "
            "verano respecto al horizontal).\n\n"
            "Lo que **no** captura: sombreado cercano, perfil horario real, "
            "suciedad diferencial por fila ni la separación entre filas que exige "
            "esta inclinación — el área que reporta la herramienta sigue asumiendo "
            "densidad coplanar y se queda corta.\n\n"
            "Para números de diseño hay que correr **PVsyst o Helioscope** con la "
            "geometría real del sitio."
        )
    else:
        st.info(
            "**Cálculo coplanar.** La generación se estima sobre irradiancia "
            "horizontal (GHI de NASA POWER), sin transposición al plano del "
            "generador. Equivale a suponer módulos coplanares sobre cubierta plana o "
            "de baja pendiente, y el PR absorbe la pérdida de orientación.\n\n"
            "Un arreglo inclinado hacia el sur puede generar **hasta 6 % más** que "
            "este estimado, y uno orientado al poniente **hasta 4 % menos**; entre un "
            "techo al sur y uno al norte hay más de 20 puntos de diferencia que este "
            "método no distingue. Para capturarlo, activa **Geometría del arreglo → "
            "Inclinado** en la barra lateral.\n\n"
            "Tampoco modela sombreado cercano ni el perfil horario. Para números de "
            "diseño hay que correr **PVsyst o Helioscope**."
        )

    # ── Distribución interanual + P90 ───────────────────────────
    if has_p90:
        st.markdown('<div class="section-header">Variabilidad interanual · P90 riguroso</div>',
                    unsafe_allow_html=True)
        n_anios = len(gen_por_anio)


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
            "height": 400,
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
        margin-top:-8px; margin-bottom:12px; font-size:12px; color:#cbd5e1;">
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
        # Tres decimales a propósito: con uno solo el delta no reconcilia a mano
        # (7.0/7.8 da −10.3 % mientras el real es −9.2 %) y parece error de cálculo
        # cuando sólo es redondeo de pantalla.
        #
        # El delta cumple la identidad exacta P90/P50 − 1 = −z·σ_total, que es la
        # forma en que se construye el P90. Verificado a 1e-15.
        _anio_max = max(gen_por_anio, key=gen_por_anio.get)
        _anio_min = min(gen_por_anio, key=gen_por_anio.get)
        mp1, mp2, mp3, mp4 = st.columns(4)
        mp1.metric("P50 · mediana", f"{p50_mwh:,.3f} MWh")
        mp2.metric("P90 anual", f"{p90_mwh:,.3f} MWh",
                   f"{(p90_real / p50_real - 1) * 100:+.2f}% vs P50")
        mp3.metric("Máximo observado", f"{max(gen_v):,.3f} MWh",
                   f"{(max(gen_v) / p50_mwh - 1) * 100:+.2f}% · {_anio_max}")
        mp4.metric("Mínimo observado", f"{min(gen_v):,.3f} MWh",
                   f"{(min(gen_v) / p50_mwh - 1) * 100:+.2f}% · {_anio_min}")
        if min(gen_v) * 1000 > p90_real:
            st.caption(
                f"El P90 (**{p90_mwh:,.3f} MWh**) queda por debajo del peor año observado "
                f"(**{min(gen_v):,.3f} MWh**, {_anio_min}). No es inconsistencia: el P90 no es "
                f"el peor año de la serie, sino el nivel que además incorpora la incertidumbre "
                f"del dato satelital, del modelo de pérdidas y de la degradación — errores que "
                f"la serie histórica no puede mostrar por sí sola.")

    else:
        st.info("ℹ️ Carga datos de NASA POWER desde el sidebar para calcular el P90.")



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
    <div class="sc-label">{tir_metodo if tir_metodo != "—" else "TIR"}</div>
    <div class="sc-val" style="color:#22d3ee;">{tir_str}</div>
    <div class="sc-sub">{tir_sub}</div>
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
    <div class="sc-label">O&amp;M + seguros año 1</div>
    <div class="sc-val" style="color:#94a3b8;">${om_anual[0]:,.0f}</div>
    <div class="sc-sub">MXN · O&amp;M {om_pct_sidebar:.1f}% + seg. {seguro_pct_sidebar:.2f}% = {om_pct_sidebar + seguro_pct_sidebar:.2f}% inv.</div>
  </div>

</div>
""", unsafe_allow_html=True)

    # ── Gráficas en dos columnas — fila 1 ─────────────────────────────────
    fm_col1, fm_col2 = st.columns(2, gap="medium")

    with fm_col1:
        st.markdown('<div class="section-header">Flujos de efectivo anuales</div>',
                    unsafe_allow_html=True)
        # Cascada completa: se grafican TODOS los componentes del flujo neto para
        # que el usuario pueda reconciliar la resta a ojo. Antes sólo aparecían
        # ingreso, flujo neto y O&M — faltaban impuestos, reposición y servicio de
        # deuda, así que las barras no cuadraban con nada.
        _imp   = fm.get("impuestos", [0.0] * len(years))
        _rep   = fm.get("capex_reposicion", [0.0] * len(years))
        _srv   = fm.get("servicio_deuda_y", [0.0] * len(years))
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(
            x=years, y=flujo_nominal, name="Ahorro bruto",
            marker_color=TEAL, opacity=0.85,
            hovertemplate="<b>Año %{x}</b><br>Ahorro: $%{y:,.0f}<extra></extra>"))
        fig_cf.add_trace(go.Bar(
            x=years, y=[-v for v in om_anual], name="O&M + seguros",
            marker_color=ROSE, opacity=0.85,
            hovertemplate="<b>Año %{x}</b><br>O&M+seg: $%{y:,.0f}<extra></extra>"))
        if any(_imp):
            fig_cf.add_trace(go.Bar(
                x=years, y=[-v for v in _imp], name="ISR",
                marker_color=VIOLET, opacity=0.85,
                hovertemplate="<b>Año %{x}</b><br>ISR: $%{y:,.0f}<extra></extra>"))
        if any(_rep):
            fig_cf.add_trace(go.Bar(
                x=years, y=[-v for v in _rep], name="Reposición inversor",
                marker_color="#f87171", opacity=0.95,
                hovertemplate="<b>Año %{x}</b><br>Reposición: $%{y:,.0f}<extra></extra>"))
        if any(_srv):
            fig_cf.add_trace(go.Bar(
                x=years, y=[-v for v in _srv], name="Servicio de deuda",
                marker_color="#94a3b8", opacity=0.9,
                hovertemplate="<b>Año %{x}</b><br>Deuda: $%{y:,.0f}<extra></extra>"))
        fig_cf.add_trace(go.Scatter(
            x=years, y=flujo_neto, name="Flujo neto",
            mode="lines+markers",
            line=dict(color=AMBER, width=2.5),
            marker=dict(size=5, color=AMBER),
            hovertemplate="<b>Año %{x}</b><br>Flujo neto: $%{y:,.0f}<extra></extra>"))
        lay_cf = copy.deepcopy(PLOT_LAYOUT)
        lay_cf.update({
            "height": 400, "barmode": "relative",
            "yaxis": dict(title="MXN", gridcolor="#2e3138", tickformat=","),
            "xaxis": dict(title="Año", tickmode="linear", dtick=max(1, vida_util // 10), gridcolor="#2e3138"),
            "legend": dict(orientation="h", y=1.12, x=0.5, xanchor="center", bgcolor="rgba(0,0,0,0)"),
            "margin": dict(l=10, r=10, t=50, b=40),
            "hovermode": "x unified",
        })
        fig_cf.update_layout(**lay_cf)
        st.plotly_chart(fig_cf, use_container_width=True)
        st.caption(
            "Las barras suman al flujo neto: ahorro bruto − O&M y seguros − ISR "
            "− reposición del inversor − servicio de deuda. La línea ámbar es el resultado.")

    with fm_col2:
        st.markdown('<div class="section-header">VPN acumulado y payback</div>',
                    unsafe_allow_html=True)
        fig_vpn = go.Figure()
        fig_vpn.add_trace(go.Scatter(
            x=[0] + years, y=[-desembolso_inicial] + acum_desc,
            name="VPN acumulado (desc.)",
            mode="lines+markers",
            line=dict(color=TEAL, width=3),
            marker=dict(size=6, color=TEAL),
            fill="tozeroy",
            fillcolor="rgba(20,184,166,0.08)",
            hovertemplate="<b>Año %{x}</b><br>VPN acum.: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_vpn.add_trace(go.Scatter(
            x=[0] + years, y=[-desembolso_inicial] + acum_nominal,
            name="Acum. nominal",
            mode="lines",
            line=dict(color=AMBER, width=2, dash="dash"),
            hovertemplate="<b>Año %{x}</b><br>Acum. nominal: $%{y:,.0f} MXN<extra></extra>",
        ))
        fig_vpn.add_hline(y=0, line_color="#94a3b8", line_dash="solid", line_width=1)
        if pb_disc is not None:
            fig_vpn.add_vline(x=pb_disc, line_color=TEAL, line_dash="dot", line_width=1.5,
                              annotation_text=f"PB desc. {pb_disc:.1f}a",
                              annotation_font=dict(color=TEAL, size=10))
        if pb_simple is not None and pb_simple != pb_disc:
            fig_vpn.add_vline(x=pb_simple, line_color=AMBER, line_dash="dot", line_width=1.5,
                              annotation_text=f"PB simple {pb_simple:.1f}a",
                              annotation_font=dict(color=AMBER, size=10),
                              annotation_position="bottom right")
        lay_vpn = copy.deepcopy(PLOT_LAYOUT)
        lay_vpn.update({
            "height": 400,
            "yaxis": dict(title="MXN acumulados", gridcolor="#2e3138", tickformat=","),
            "xaxis": dict(title="Año", tickmode="linear", dtick=max(1, vida_util // 10), gridcolor="#2e3138"),
            "legend": dict(orientation="h", y=1.12, x=0.5, xanchor="center", bgcolor="rgba(0,0,0,0)"),
            "margin": dict(l=10, r=10, t=50, b=40),
            "hovermode": "x unified",
        })
        fig_vpn.update_layout(**lay_vpn)
        st.plotly_chart(fig_vpn, use_container_width=True)

    # ── Tabla anual auditable ─────────────────────────────────────────────
    # Cada columna es un término de la resta y la última verifica el cierre.
    with st.expander("Tabla año a año — desglose auditable del flujo"):
        _rows = []
        _cfads = fm.get("cfads_y") or []
        _dscr  = fm.get("dscr_y") or []
        for i, y in enumerate(years):
            _chk = (flujo_nominal[i] - om_anual[i] - _imp[i] - _rep[i]
                    - _srv[i] - flujo_neto[i])
            _rows.append({
                "Año": y,
                "Gen (kWh)": f"{fm['gen_proj'][i]:,.0f}",
                "Tarifa": f"${fm['tarifas_y'][i]:.3f}",
                "(+) Ahorro": f"${flujo_nominal[i]:,.0f}",
                "(−) O&M+seg": f"${om_anual[i]:,.0f}",
                "(−) ISR": f"${_imp[i]:,.0f}",
                "(−) Reposición": f"${_rep[i]:,.0f}",
                "(−) Deuda": f"${_srv[i]:,.0f}",
                "(=) Flujo neto": f"${flujo_neto[i]:,.0f}",
                "CFADS": f"${_cfads[i]:,.0f}" if _cfads else "—",
                "DSCR": (f"{_dscr[i]:.2f}x" if _dscr and _dscr[i] is not None else "—"),
                "Acum. nominal": f"${acum_nominal[i]:,.0f}",
                "Δ": "✓" if abs(_chk) < 0.5 else f"{_chk:,.2f}",
            })
        st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True,
                     height=520)
        _desc = desembolso_inicial
        st.caption(
            f"Desembolso inicial (año 0): **−${_desc:,.0f}**"
            + (f" = CAPEX ${inversion_mxn:,.0f} − deuda ${deuda_mxn_tk:,.0f}"
               if deuda_mxn_tk > 0 else " (compra de contado, sin deuda)")
            + f" · El acumulado nominal arranca de ahí. La columna Δ verifica que "
              f"cada renglón cierre: ahorro − O&M − ISR − reposición − deuda = flujo neto. "
              f"Un ISR negativo es escudo fiscal a favor. "
              f"**Nota fiscal:** el ahorro NO es ingreso acumulable — es una menor "
              f"deducción por consumo eléctrico. El efecto sobre la utilidad gravable "
              f"es el mismo, pero la naturaleza contable difiere y el tratamiento de "
              f"IVA no es equivalente. Confírmalo con tu asesor."
            + (f" **CFADS** = ahorro − O&M − ISR, antes del servicio de deuda; "
               f"**DSCR** = CFADS ÷ servicio. Mínimo del periodo: "
               f"**{fm['dscr_min']:.2f}x**."
               if fm.get("dscr_min") else
               " Sin deuda: CFADS y DSCR no aplican.")
        )

    # ── Gráfica sensibilidad + tabla — fila 2 ─────────────────────────────
    fm_col3, fm_col4 = st.columns([1.15, 1.45], gap="medium")

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
        fig_sens.add_hline(y=0, line_color="#94a3b8", line_width=1)
        lay_sens = copy.deepcopy(PLOT_LAYOUT)
        lay_sens.update({
            "height": 560,   # emparejado con la altura de la tabla financiera
            "yaxis": dict(title="VPN (MXN)", gridcolor="#2e3138", tickformat=","),
            "xaxis": dict(title="WACC (%)", gridcolor="#2e3138",
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
            # En turnkey NO hay ingreso: el sistema reduce un gasto deducible.
            # El efecto fiscal es equivalente, pero la naturaleza contable no.
            "Ahorro (MXN)":      [f"${v:,.0f}" for v in flujo_nominal],
            "O&M+seg (MXN)":     [f"${v:,.0f}" for v in om_anual],
            "Flujo neto (MXN)":  [f"${v:,.0f}" for v in flujo_neto],
            "Flujo desc. (MXN)": [f"${v:,.0f}" for v in flujo_desc],
            "VPN acum. (MXN)":   [f"${v:,.0f}" for v in acum_desc],
        })
        st.dataframe(tabla_fin, use_container_width=True, hide_index=True, height=560)

    # ── Totales — ancho completo ───────────────────────────────────────────
    st.markdown(f"""
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:12px;">
  <div class="snap-card">
    <div class="sc-label">Ahorro bruto total</div>
    <div class="sc-val" style="color:#f9fafb;">${sum(flujo_nominal):,.0f}</div>
    <div class="sc-sub">MXN nominales</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">O&amp;M total (nominal)</div>
    <div class="sc-val" style="color:#94a3b8;">${sum(om_anual):,.0f}</div>
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
        # Base P90, la misma que alimenta ahorro1 y el modelo financiero.
        # Antes iba monthly_gen (base P50) junto a un ahorro P90: el TOR
        # mostraba una tabla mensual que no cuadraba con su propia cifra.
        monthly_gen_base,
        annual_gen_base,
        p50,
        p90,
        co2_saved,
        inversion,
        ahorro1,
        payback,
        gen_por_anio,
    )

    if usando_irr_default:
        st.error(
            "🔒 **Exportación bloqueada** — la irradiancia es el respaldo de CDMX, "
            "no el recurso de este sitio. Carga NASA POWER desde el sidebar para "
            "habilitar TOR, PDF y Word."
        )

    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        st.download_button(
            "⬇️ Descargar TOR (.txt)",
            data=tor_text.encode("utf-8"),
            file_name=f"TOR_Solar_{proj_loc[:20].replace(' ','_')}.txt",
            mime="text/plain",
            disabled=usando_irr_default,
            use_container_width=True)
    with ex2:
        pdf_sizing_bytes = build_pdf_sizing(
            proj_loc=proj_loc, lat=lat, lon=lon,
            panel_wp=panel_wp, panel_eff_declared=panel_eff_declared,
            panel_largo_mm=panel_largo_mm, panel_ancho_mm=panel_ancho_mm,
            panel_peso_kg=panel_peso_kg, panel_area=panel_area,
            n_panels=n_panels, kwp=kwp, pr_pct=pr_pct,
            # FIX — la gráfica mensual y el total van en base P90, la misma que
            # alimenta ahorro1, el CO2 y el modelo financiero. Antes se exportaba
            # monthly_gen (base P50) junto a un ahorro base P90: el mismo PDF
            # mostraba una gráfica que no cuadraba con su propia cifra de ahorro
            # por ~9.6 %.
            irr_vals=irr_vals, monthly_gen=monthly_gen_base, annual_gen=annual_gen_base,
            p50=p50, p90=p90, co2_saved=co2_saved,
            inversion_usd=float(inversion), usd_to_mxn=usd_to_mxn,
            ahorro1=ahorro1, payback=payback,
            vpn=vpn, tir=tir, lcoe=lcoe, pb_disc=pb_disc,
            tarifa_efectiva=tarifa_efectiva, inflation=inflation,
            discount_rate=discount_rate, vida_util=vida_util,
            # El modelo cobra O&M + seguros; el PDF debe reportar el total.
            om_pct=om_pct_sidebar + seguro_pct_sidebar,
            sizing_mode_label="Por área" if uso_area else "Por recibo CFE",
        )
        st.download_button(
            "📄 Exportar PDF — Sizing",
            data=pdf_sizing_bytes,
            file_name=f"Sizing_Solar_{proj_loc[:20].replace(' ','_')}.pdf",
            mime="application/pdf",
            disabled=usando_irr_default,
            use_container_width=True,
            type="primary",
        )
    with ex3:
        if st.button("📝 Generar Caso de Negocio (.docx)",
                     disabled=usando_irr_default,
                     use_container_width=True, key="btn_word_turnkey"):
            with st.spinner("Generando Word…"):
                try:
                    import datetime as _dt
                    _consumo_a = sum(monthly_cons_ref) if monthly_cons_ref else 0
                    _cob_pct   = cobertura_anual_base if not uso_area else 0
                    _word_bytes = build_word_turnkey(
                        proj_loc=proj_loc, lat=lat, lon=lon,
                        fecha=_dt.date.today().strftime("%B %Y"),
                        kwp=kwp, n_panels=n_panels,
                        panel_wp=panel_wp, panel_eff_declared=panel_eff_declared,
                        panel_largo_mm=panel_largo_mm, panel_ancho_mm=panel_ancho_mm,
                        panel_peso_kg=panel_peso_kg,
                        area_used=area_instalacion, inversion_usd=float(inversion),
                        inversion_mxn=inversion_mxn, usd_to_mxn=usd_to_mxn,
                        costo_kwp=costo_kwp,
                        ahorro1=ahorro1, co2_saved_t=co2_saved_t,
                        hsp_anual=hsp_anual, annual_gen=annual_gen_base,
                        p50=p50, p90_real=p90_real,
                        pr_pct=pr_pct, panel_degradation=panel_degradation,
                        vida_util=vida_util, wacc=discount_rate,
                        inflacion_cfe=inflation,
                        tarifa_efectiva=tarifa_efectiva,
                        om_pct_sidebar=om_pct_sidebar + seguro_pct_sidebar,
                        vpn=vpn, tir=tir, pb_simple=pb_simple,
                        pb_disc=pb_disc, lcoe=lcoe,
                        fm=fm,
                        consumo_anual=_consumo_a,
                        cobertura_pct=_cob_pct,
                        # Datos para gráficas embebidas:
                        # irr_vals editada por el usuario, no active_irr (NASA cruda):
                        # si edita la tabla, la gráfica del Word debe reflejarlo.
                        irr_vals=list(irr_vals),
                        monthly_gen=list(monthly_gen_base),
                        monthly_cons=list(monthly_cons_ref) if monthly_cons_ref else None,
                        gen_por_anio=gen_por_anio,
                    )
                    st.session_state["word_turnkey_bytes"] = _word_bytes
                    st.success("✅ Documento generado")
                except Exception as _e:
                    st.error(f"❌ Error generando Word: {_e}")
        if "word_turnkey_bytes" in st.session_state:
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

        # ── Fuente de datos: Turnkey Solar o Recibo CFE ──────────────────────
        # El sistema base siempre se hereda del sizing de Turnkey Solar, que ya
        # incorpora el modo elegido allá (área o recibo CFE), el recorte del
        # inversor y la irradiancia editada. Antes existía aquí un radio
        # "Turnkey Solar / Recibo CFE" que era un no-op: ambas ramas calculaban
        # exactamente los mismos valores y sólo cambiaban la etiqueta y el color.
        _kwp_fuente   = _kwp_turnkey
        _p50_val      = max(100.0, round(float(annual_gen), 0))
        _p90_val      = max(100.0, round(float(p90_real), 0)) if p90_real else None
        _inv_fuente   = _inv_turnkey
        _fuente_label = ("Turnkey Solar · por área" if uso_area
                         else "Turnkey Solar · por recibo CFE")
        _fuente_color = "info-box"
        _fuente_icon  = "📐" if uso_area else "🧾"

        _has_p90 = _p90_val is not None

        st.markdown(f"""
<div class="{_fuente_color}" style="margin-bottom:0.5rem;">
  {_fuente_icon} <b>Fuente: {_fuente_label}</b> —
  {_kwp_fuente:.1f} kWp &nbsp;·&nbsp; ${_inv_fuente:,.0f} USD inversión
  &nbsp;·&nbsp; Gen P50: {_p50_val:,.0f} kWh/año
  {f'&nbsp;·&nbsp; P90: {_p90_val:,.0f} kWh/año' if _has_p90 else ''}.
  Puedes editarlos abajo para simular un escenario diferente.
</div>
""", unsafe_allow_html=True)

        ppa_kwp = st.number_input("Capacidad (kWp)", 1.0, 50000.0,
                                   float(_kwp_fuente), 1.0, key="ppa_kwp")

        # ── Generación base: siempre P90 cuando está disponible ──────────────
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

        # FIX — la generación debe seguir al kWp que el usuario capture aquí.
        # Antes `ppa_gen_anual` era un input suelto con el valor de Turnkey como
        # default: si cambiabas el kWp del PPA la generación NO se recalculaba y
        # quedabas evaluando una capacidad con la energía de otra.
        # Se escala con el mismo rendimiento específico del sizing, que ya trae
        # recorte del inversor y disponibilidad.
        _rend_kwh_kwp = (_p90_val / kwp) if (_has_p90 and kwp > 0) else (
                        (_p50_val / kwp) if kwp > 0 else 0.0)
        _gen_default = max(100.0, round(_rend_kwh_kwp * ppa_kwp, 0))
        _gen_label   = f"Generación año 1 — {'P90' if _has_p90 else 'P50'} (kWh/año)"
        if abs(ppa_kwp - _kwp_fuente) > 0.05:
            st.caption(
                f"Capacidad ajustada a **{ppa_kwp:,.1f} kWp**: la generación se recalculó "
                f"a **{_gen_default:,.0f} kWh/año** con el rendimiento específico del "
                f"sizing ({_rend_kwh_kwp:,.0f} kWh/kWp, ya con recorte del inversor).")

        ppa_gen_anual = st.number_input(_gen_label, 100.0, 50_000_000.0,
                                         float(_gen_default), 100.0, key="ppa_gen")
        ppa_inversion_usd = st.number_input(
            "Inversión total (USD)", 1000.0, 50_000_000.0,
            float(max(1000.0, round(ppa_kwp * costo_kwp, 0))), 100.0, key="ppa_inv",
            help="Se recalcula con el kWp capturado arriba y el costo de referencia "
                 "del sidebar. Puedes sobrescribirlo con una cotización real.")
        st.caption(f"≈ ${ppa_inversion_usd * usd_to_mxn:,.0f} MXN al tipo de cambio configurado")

        st.markdown('<div class="section-header">Parámetros técnicos</div>', unsafe_allow_html=True)
        ppa_degradacion  = st.slider("Degradación anual (%)", 0.0, 1.5, 0.5, 0.05, key="ppa_deg")
        ppa_om_pct       = st.slider("O&M anual (% inv. MXN)", 0.3, 3.0, 1.70, 0.05, key="ppa_om")
        ppa_seguros_pct  = st.slider("Seguros / otros (% inv. MXN)", 0.0, 1.5, 0.50, 0.05, key="ppa_seg")

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
            ppa_tasa_deuda  = st.slider("Tasa deuda anual (%)", 5.0, 25.0, 12.0, 0.5, key="ppa_debt_r")
            ppa_plazo_deuda = st.slider("Plazo deuda (años)", 3, 20, 10, 1, key="ppa_debt_p")
            _modo_deuda = st.radio(
                "¿Cómo se determina la deuda?",
                ["Por cobertura (DSCR)", "Equity fijo"],
                key="ppa_modo_deuda",
                help="Por cobertura: el banco calcula el CFADS del proyecto, lo divide entre "
                     "el DSCR objetivo para obtener el servicio de deuda máximo sostenible y "
                     "de ahí despeja el principal; el equity sale por diferencia. Es como "
                     "opera el project finance real. Equity fijo: tú impones la estructura y "
                     "el servicio cae donde caiga, sin verificar que el proyecto lo aguante.")
            ppa_dim_dscr = _modo_deuda.startswith("Por cobertura")
            if ppa_dim_dscr:
                ppa_dscr_obj = st.slider(
                    "DSCR objetivo (x)", 1.00, 2.00, 1.30, 0.05, key="ppa_dscr_obj",
                    help="Cobertura mínima exigida sobre el año más débil del periodo de "
                         "crédito. Solar contratado en México suele pedir 1.20–1.35x. "
                         "Por debajo de 1.20x la deuda difícilmente se coloca.")
                ppa_esculpido = st.checkbox(
                    "Amortización esculpida (DSCR constante)", value=True,
                    key="ppa_esculpido",
                    help="El servicio de deuda de cada año se modela sobre el CFADS de ese "
                         "año para mantener el DSCR exactamente en el objetivo. Es la "
                         "práctica estándar en project finance renovable y libera más deuda "
                         "que una anualidad plana, porque con el escalador del PPA el CFADS "
                         "crece y la anualidad desperdicia esa holgura. Sin marcar: "
                         "anualidad constante dimensionada por el año más débil.")
                ppa_equity_pct = 30   # se recalcula; sólo evita indefinición
            else:
                ppa_dscr_obj   = 1.30
                ppa_esculpido  = False
                ppa_equity_pct = st.slider("Capital propio (%)", 10, 100, 30, 5, key="ppa_eq")
        else:
            ppa_equity_pct  = 100
            ppa_tasa_deuda  = 0.0
            ppa_plazo_deuda = 0
            ppa_dim_dscr    = False
            ppa_dscr_obj    = 1.30
            ppa_esculpido   = False

        st.markdown('<div class="section-header">Costos de propiedad y fiscal</div>',
                    unsafe_allow_html=True)
        st.caption("En un PPA el dueño del sistema es el desarrollador: la reposición "
                   "del inversor y el ISR corren por su cuenta.")
        ppa_rep_year = st.slider(
            "Año de reposición del inversor", 0, 25, 12, 1, key="ppa_rep_year",
            help="0 = sin reemplazo. Turnkey ya lo modelaba y el PPA no, pese a que "
                 "aquí el dueño del activo es el desarrollador.")
        ppa_rep_kw = st.number_input(
            "Costo de reposición (USD/kW AC)", 0.0, 500.0, 90.0, 5.0, key="ppa_rep_kw",
            help="Equipo más mano de obra y maniobra, por kW AC instalado.")
        ppa_disp = st.slider(
            "Disponibilidad del sistema (%)", 90.0, 100.0, 100.0, 0.1, key="ppa_disp",
            help="Default 100 %: el PR ya incorpora ~1 % de indisponibilidad típica.")
        ppa_isr_on = st.checkbox("Modelar ISR", value=False, key="ppa_isr_on",
                                 help="Sin marcar, los resultados son antes de impuestos.")
        if ppa_isr_on:
            ppa_isr = st.slider("Tasa de ISR (%)", 0.0, 40.0, 30.0, 1.0, key="ppa_isr")
            ppa_a34 = st.checkbox("Deducción acelerada Art. 34 LISR", value=True, key="ppa_a34")
            ppa_esc_inm = st.radio(
                "¿Quién capta el escudo fiscal?",
                ["Causante con otras utilidades", "SPV sin otros ingresos"],
                key="ppa_perfil_fiscal").startswith("Causante")
        else:
            ppa_isr = 0.0; ppa_a34 = False; ppa_esc_inm = True
        ppa_ke_din = st.checkbox(
            "Ke dinámico (baja al amortizar la deuda)", value=True, key="ppa_ke_din",
            help="La deuda amortiza y el apalancamiento cae, así que el riesgo del "
                 "accionista baja. Sin marcar se usa el Ke del año 1 todo el plazo, "
                 "lo que sobre-descuenta los años tardíos.")
        ppa_dsra = st.slider(
            "DSRA — meses de servicio en reserva", 0.0, 12.0, 0.0, 1.0, key="ppa_dsra",
            help="Cuenta de reserva exigida por el prestamista. Sale del bolsillo del "
                 "accionista al inicio y se libera al último pago. 0 = no modelarla.")

        ppa_desc_merchant = st.slider(
            "Descuento merchant post-contrato (%)", 0.0, 60.0, 30.0, 5.0,
            key="ppa_merchant",
            help="Al vencer el PPA ya no existe el precio contractual. Este castigo se aplica "
                 "sobre el último precio contratado para valorar la energía post-contrato en "
                 "el valor de rescate. 0 % asume que el offtaker renueva al mismo precio "
                 "escalado, supuesto agresivo.")

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
                                              max(0.5, round(float(tarifa_efectiva), 4)),
                                              0.0001, format="%.4f",key="ppa_tar")
        ppa_inflacion_cfe  = st.slider("Inflación CFE anual (%)", 0.0, 12.0, 6.0, 0.5, key="ppa_inf_cfe")

    with ppa_col3:
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

        st.markdown('<div class="section-header">Precio PPA por plazo</div>', unsafe_allow_html=True)
        st.caption("Ingresa el precio PPA año 1 (MXN/kWh) para cada plazo activo.")
        # Construir dict de precio por plazo
        ppa_precios_por_plazo = {}
        _pp_cols = st.columns(len(ppa_plazos))
        for _pi, _pl in enumerate(ppa_plazos):
            ppa_precios_por_plazo[_pl] = _pp_cols[_pi].number_input(
                f"Precio {_pl}a",
                min_value=0.50, max_value=10.0,
                value=1.80, step=0.05,
                format="%.4f",
                key=f"ppa_price_{_pl}",
                help=f"Precio PPA año 1 para el plazo de {_pl} años"
            )
        # Precio del plazo objetivo (para mostrar en el hero y cálculos generales)
        st.markdown('<div class="section-header">Plazo objetivo</div>', unsafe_allow_html=True)
        ppa_plazo_minimo = st.selectbox("Plazo para análisis detallado", ppa_plazos, key="ppa_pmin_plazo")
        ppa_precio_manual = ppa_precios_por_plazo[ppa_plazo_minimo]

    # ── Calcular todos los plazos — usando funciones cacheadas globales ──────
    # Si el usuario desactivó el valor de rescate, se pasa vida_util_total = plazo
    # para que anios_restantes = 0 y valor_residual = 0 en todos los escenarios.
    # kW AC del bloque de inversores para el PPA: se deriva del kWp con la misma
    # relación DC/AC de la pestaña Turnkey, para que las dos usen el mismo criterio.
    _ppa_ac_kw = ppa_kwp / max(inv_res["dc_ac_real"], 0.01)

    ppa_cache_kwargs = dict(
        gen1=ppa_gen_anual, inv_usd=ppa_inversion_usd,
        wacc_pct=ppa_wacc, esc_ppa=ppa_inflacion_tarifa,
        deg=ppa_degradacion, om_pct=ppa_om_pct,
        inf_om=ppa_inflacion_om, seg_pct=ppa_seguros_pct,
        usd_mx=usd_to_mxn, equity_pct=ppa_equity_pct,
        tasa_deuda=ppa_tasa_deuda, plazo_deuda=ppa_plazo_deuda,
        con_fin=ppa_financiamiento,
        vida_util_total=vida_util,
        dimensionar_por_dscr=ppa_dim_dscr,
        dscr_objetivo=ppa_dscr_obj,
        lid_pct=lid_pct,
        descuento_merchant=ppa_desc_merchant,
        perfil_esculpido=ppa_esculpido,
        disponibilidad=ppa_disp / 100.0,
        inv_replace_year=ppa_rep_year,
        inv_replace_mxn=_ppa_ac_kw * ppa_rep_kw * usd_to_mxn,
        inv_replace_esc=0.0,
        isr_pct=ppa_isr,
        deduccion_art34=ppa_a34,
        escudo_inmediato=ppa_esc_inm,
        ke_dinamico=ppa_ke_din,
        dsra_meses=ppa_dsra)

    resultados = {}
    # ── Hurdle rate ──────────────────────────────────────────────────────────
    # FIX — antes el hurdle se inyectaba como wacc_pct. Ese parámetro alimenta la
    # tasa de descuento Y la fórmula Ke = WACC + (D/E)(WACC − Kd), así que subirlo
    # re-apalancaba Ke: con estructura 70/30 un spread de 4 puntos inflaba Ke ~13
    # puntos y castigaba el VPN ~35 % en vez del ~11 % correspondiente, declarando
    # inviables proyectos que sí lo eran.
    # Ahora el spread se suma a Ke y se pasa por `descuento_pct`, que sólo afecta
    # el descuento. Ke se mantiene derivado del WACC real del usuario.
    _ke_base = calc_ppa_result(precio_ppa=1.0, plazo=max(ppa_plazos),
                               **ppa_cache_kwargs)["ke_pct"]
    _hurdle_pct = _ke_base + ppa_spread_hurdle
    ppa_cache_kwargs_hurdle = {**ppa_cache_kwargs, "descuento_pct": _hurdle_pct}
    for pl in ppa_plazos:
        _vida_util_eff = vida_util if ppa_usar_valor_residual else pl
        _precio_pl = ppa_precios_por_plazo[pl]   # precio específico para este plazo
        _kwargs_pl        = {**ppa_cache_kwargs,        "vida_util_total": _vida_util_eff}
        _kwargs_pl_hurdle = {**ppa_cache_kwargs_hurdle, "vida_util_total": _vida_util_eff}
        # VPN y payback descontado se calculan con hurdle rate (tasa que ve el usuario)
        res = dict(calc_ppa_result(precio_ppa=_precio_pl, plazo=pl, **_kwargs_pl_hurdle))
        # TIR y payback simple no dependen de la tasa de descuento — se toman del calculo base (WACC)
        res_base = dict(calc_ppa_result(precio_ppa=_precio_pl, plazo=pl, **_kwargs_pl))
        res["tir"] = res_base["tir"]
        res["pb"]  = res_base["pb"]
        # VPN a WACC base y VPN a precio ofrecido (precio manual) con hurdle rate
        res["vpn_wacc"]     = res_base["vpn"]   # VPN descontado a Ke (tasa base)
        res["vpn_hurdle"]   = res["vpn"]        # VPN descontado a Ke + spread
        res["precio_pl"]    = _precio_pl        # guardar precio del plazo para referencia
        # ── LCOE ─────────────────────────────────────────────────────────────
        # Se usa WACC, no Ke: el LCOE es métrica del proyecto completo (deuda+equity),
        # no de la perspectiva equity. Consistente con calc_financial_model (Turnkey).
        #
        # FIX S2 — el LCOE se nivela sobre la VIDA ÚTIL del activo, no sobre el plazo
        # del contrato. Repartir todo el CAPEX entre la energía del contrato hacía que
        # el mismo sistema físico "costara" $4.30/kWh a 5 años y $2.50/kWh a 25: puro
        # artefacto de asignación contable, no economía. Se reportan ambos para que la
        # diferencia sea visible.
        _wacc_r   = ppa_wacc / 100
        _n_lcoe   = max(pl, vida_util)
        _gen_ext, _om_ext = [], []
        for i in range(_n_lcoe):
            if i < pl:
                _gen_ext.append(res_base["gen_y"][i])
                _om_ext.append(res_base["om_y"][i] + res_base["seg_y"][i])
            else:
                # Extensión post-contrato: misma degradación y misma inflación de O&M.
                _gen_ext.append(res_base["gen_y"][-1] * (1 - ppa_degradacion / 100) ** (i - pl + 1))
                _om_ext.append((res_base["om_y"][-1] + res_base["seg_y"][-1])
                               * (1 + ppa_inflacion_om / 100) ** (i - pl + 1))
        _pv_gen_v  = sum(_gen_ext[i] / (1 + _wacc_r) ** (i + 1) for i in range(_n_lcoe))
        _pv_cost_v = res_base["inv_mxn"] + sum(_om_ext[i] / (1 + _wacc_r) ** (i + 1)
                                               for i in range(_n_lcoe))
        res["lcoe"] = _pv_cost_v / _pv_gen_v if _pv_gen_v > 0 else 0.0

        # LCOE sobre el plazo del contrato — sólo como referencia comparativa.
        _pv_gen_c  = sum(res_base["gen_y"][i] / (1 + _wacc_r) ** (i + 1) for i in range(pl))
        _pv_cost_c = res_base["inv_mxn"] + sum(
            (res_base["om_y"][i] + res_base["seg_y"][i]) / (1 + _wacc_r) ** (i + 1)
            for i in range(pl))
        res["lcoe_contrato"] = _pv_cost_c / _pv_gen_c if _pv_gen_c > 0 else 0.0
        # VPN / Equity (%) — cuántos pesos de VPN por cada 100 de equity aportado.
        # NOTA: no es el Profitability Index clásico (PV entradas / PV salidas,
        # donde 1.0 es el punto de equilibrio). El PI equivalente sería 1 + pi/100.
        _equity_mxn = res_base.get("equity_mxn", res_base["inv_mxn"])
        res["pi"] = (res_base["vpn"] / _equity_mxn * 100) if _equity_mxn > 0 else 0.0
        res["pm"] = calc_precio_minimo(
            plazo=pl, vida_util_total=_vida_util_eff,
            **{k: v for k, v in _kwargs_pl.items() if k != "vida_util_total"})
        res["ph"] = calc_precio_hurdle(
            plazo=pl, vida_util_total=_vida_util_eff,
            spread_pct=ppa_spread_hurdle,
            **{k: v for k, v in _kwargs_pl.items() if k != "vida_util_total"})
        resultados[pl] = res

    # Negativo = el PPA está por debajo de la tarifa CFE (favorable al cliente).
    descuento_vs_cfe = ((ppa_precio_manual / ppa_tarifa_cliente) - 1) * 100
    # Mismo dato con el signo orientado a "ahorro": positivo = el cliente ahorra.
    ahorro_pct_cliente = -descuento_vs_cfe
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
        _vr_color = "#94a3b8"
    elif val_res > 0:
        val_res_str = f"${val_res:,.0f} MXN"
        _nota_rescate = (
            f"Gordon generalizado · suma finita exacta · {_anios_rest} años restantes · "
            f"g_ingreso = {_g_ing:+.2f}%/año (escalador {ppa_inflacion_tarifa:.1f}% - degradación {ppa_degradacion:.2f}%) · "
            f"descontado a {ro_obj.get('disc_pct', _hurdle_pct):.1f}% desde t={ppa_plazo_minimo}"
        )
        _vr_color = "#14b8a6"
    else:
        val_res_str = "Contrato = vida útil" if vida_util <= ppa_plazo_minimo else "—"
        _nota_rescate = "Contrato cubre toda la vida útil del sistema" if vida_util <= ppa_plazo_minimo else "Sin años restantes"
        _vr_color = "#94a3b8"
    _hurdle_label = f"Ke+{ppa_spread_hurdle:.0f}% = {_hurdle_pct:.1f}%  (Ke {_ke_base:.1f}%)"
    st.markdown(f"""
<div class="tor-hero" style="margin-top:1rem;">
  <div class="th-project">📄 ANÁLISIS PPA · Plazo objetivo {ppa_plazo_minimo} años
    &nbsp;·&nbsp; Valor de rescate: <span style="color:{'#14b8a6' if ppa_usar_valor_residual else '#94a3b8'}">{'INCLUIDO' if ppa_usar_valor_residual else 'EXCLUIDO'}</span>
  </div>
  <div class="th-meta">
    Precio evaluado: <b style="color:#f59e0b">${ppa_precio_manual:.4f}/kWh</b>
    &nbsp;·&nbsp; Ahorro cliente vs CFE hoy: <b style="color:{'#14b8a6' if ahorro_pct_cliente > 0 else '#f87171'}">{ahorro_pct_cliente:+.1f}%</b>
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
      <span class="th-val" style="color:#f1f5f9;font-size:15px;">{f"{ro_obj['pb_disc']} años" if ro_obj.get('pb_disc') is not None else f'>{ppa_plazo_minimo}a'}</span>
      <span class="th-unit">a hurdle {ppa_wacc+ppa_spread_hurdle:.1f}%</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Cobertura de deuda — criterio bancario ────────────────────────────────
    # Ningún banco evalúa un PPA por TIR de equity: dimensiona por DSCR y verifica
    # el LLCR. Sin estas métricas el modelo no pasa un comité de crédito.
    if ppa_financiamiento and ro_obj.get("deuda_mxn", 0) > 0:
        st.markdown('<div class="section-header">Cobertura de deuda · criterio bancario</div>',
                    unsafe_allow_html=True)
        _dmin  = ro_obj.get("dscr_min")
        _dprom = ro_obj.get("dscr_prom")
        _llcr  = ro_obj.get("llcr")
        _dobj  = ro_obj.get("dscr_objetivo", 1.30)
        _ok    = _dmin is not None and _dmin >= _dobj - 1e-9
        _cmin  = "#4ade80" if _ok else "#f87171"
        _cllcr = "#4ade80" if (_llcr or 0) >= 1.30 else ("#facc15" if (_llcr or 0) >= 1.10 else "#f87171")
        st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:10px;">
  <div class="snap-card">
    <div class="sc-label">DSCR mínimo</div>
    <div class="sc-val" style="color:{_cmin};">{f"{_dmin:.2f}x" if _dmin else "—"}</div>
    <div class="sc-sub">objetivo {_dobj:.2f}x</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">DSCR promedio</div>
    <div class="sc-val">{f"{_dprom:.2f}x" if _dprom else "—"}</div>
    <div class="sc-sub">vida del crédito</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">LLCR</div>
    <div class="sc-val" style="color:{_cllcr};">{f"{_llcr:.2f}x" if _llcr else "—"}</div>
    <div class="sc-sub">VP(CFADS)/deuda</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Deuda colocable</div>
    <div class="sc-val" style="font-size:14px;">${ro_obj.get('deuda_mxn',0):,.0f}</div>
    <div class="sc-sub">{ro_obj.get('apalancamiento',0):.0f}% del CAPEX</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Equity requerido</div>
    <div class="sc-val" style="font-size:14px;">${ro_obj.get('equity_mxn',0):,.0f}</div>
    <div class="sc-sub">MXN</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Servicio anual</div>
    <div class="sc-val" style="font-size:14px;">${ro_obj.get('serv_deuda',0):,.0f}</div>
    <div class="sc-sub">{ro_obj.get('plazo_deuda_eff',0)} años · {ro_obj.get('metodo_deuda','')}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        # ── Cola de deuda (tail) ─────────────────────────────────────────────
        # El banco exige que el crédito venza ANTES que el contrato que respalda el
        # flujo, con margen. Esa diferencia es la cola: si el proyecto se retrasa o
        # el recurso falla, quedan años de ingreso contratado para recuperar.
        _tail = ppa_plazo_minimo - ro_obj.get("plazo_deuda_eff", 0)
        if _tail < 1:
            st.error(
                f"🔴 **Sin cola de deuda.** El crédito vence en el año "
                f"{ro_obj.get('plazo_deuda_eff', 0)} y el PPA en el {ppa_plazo_minimo}: "
                f"cola de {_tail} años. Los prestamistas exigen típicamente **2–3 años** de "
                f"ingreso contratado después del último pago. Sin cola, cualquier retraso o "
                f"año de recurso pobre deja al crédito sin respaldo contractual. "
                f"Acorta el plazo del crédito o alarga el PPA.")
        elif _tail < 2:
            st.warning(
                f"⚠️ **Cola de deuda de {_tail} año.** Por debajo de los 2–3 años que suelen "
                f"exigir los prestamistas. Es negociable, pero espera spread más alto o "
                f"garantías adicionales del patrocinador.")
        else:
            st.caption(
                f"✅ Cola de deuda: **{_tail} años** de PPA contratado después del "
                f"vencimiento del crédito (año {ro_obj.get('plazo_deuda_eff', 0)} de "
                f"{ppa_plazo_minimo}).")

        if not _ok and _dmin is not None:
            st.error(
                f"🔴 **DSCR mínimo {_dmin:.2f}x por debajo del objetivo {_dobj:.2f}x.** "
                f"En el año más débil el proyecto no genera flujo suficiente para el servicio "
                f"de deuda con el colchón exigido. El crédito no se coloca con esta estructura: "
                f"hay que subir el precio PPA, alargar el plazo o aportar más equity.")
        if _llcr is not None and _llcr < 1.10:
            st.warning(
                f"⚠️ **LLCR {_llcr:.2f}x.** El valor presente del flujo disponible apenas cubre "
                f"el saldo de la deuda; sin margen ante desviaciones del recurso.")

        # ── Estrés a P99 — dimensionamiento de la DSRA ───────────────────────
        # La deuda se dimensiona sobre P90, pero el banco quiere saber qué pasa en
        # un año P99 para calibrar la cuenta de reserva de servicio de deuda.
        if p99_real and p90_real and p90_real > 0:
            _f99 = p99_real / p90_real
            _cf99 = [c * _f99 for c in ro_obj.get("cfads_y", [])]
            _serv = ro_obj.get("serv_deuda", 0.0)
            _nn   = ro_obj.get("plazo_deuda_eff", 0)
            if _serv > 0 and _nn > 0:
                _d99 = [c / _serv for c in _cf99[:_nn]]
                _d99min = min(_d99) if _d99 else None
                # Déficit del peor año: cuánto flujo falta para cubrir el servicio.
                _def = max(0.0, _serv - min(_cf99[:_nn])) if _cf99 else 0.0
                _c99 = "#4ade80" if (_d99min or 0) >= 1.0 else "#f87171"
                st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0 4px;">
  <div class="snap-card">
    <div class="sc-label">DSCR mínimo a P99</div>
    <div class="sc-val" style="color:{_c99};">{f"{_d99min:.2f}x" if _d99min else "—"}</div>
    <div class="sc-sub">escenario de estrés</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Déficit en el peor año</div>
    <div class="sc-val" style="font-size:14px;">${_def:,.0f}</div>
    <div class="sc-sub">MXN · flujo faltante</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">DSRA sugerida</div>
    <div class="sc-val" style="font-size:14px;">${_serv * 0.5:,.0f}</div>
    <div class="sc-sub">6 meses de servicio</div>
  </div>
</div>
""", unsafe_allow_html=True)
                if _d99min is not None and _d99min < 1.0:
                    st.warning(
                        f"⚠️ **En un año P99 el DSCR cae a {_d99min:.2f}x** — por debajo de 1.00x el "
                        f"proyecto no cubre el servicio con flujo propio y tendría que echar mano de "
                        f"la reserva. Faltarían ${_def:,.0f}. Es el escenario que el banco usa para "
                        f"dimensionar la DSRA, no un motivo para rechazar la operación.")
        _cf = ro_obj.get("cfads_y", []); _dy = ro_obj.get("dscr_y", [])
        if _dy and any(d is not None for d in _dy):
            _nn = ro_obj.get("plazo_deuda_eff", 0)
            fig_ds = go.Figure()
            fig_ds.add_trace(go.Bar(
                x=list(range(1, _nn + 1)), y=[d for d in _dy[:_nn]],
                marker_color=[TEAL if (d or 0) >= _dobj else ROSE for d in _dy[:_nn]],
                name="DSCR",
                hovertemplate="<b>Año %{x}</b><br>DSCR: %{y:.2f}x<extra></extra>"))
            fig_ds.add_hline(y=_dobj, line_color=AMBER, line_dash="dash", line_width=2,
                             annotation_text=f"objetivo {_dobj:.2f}x")
            _lay = copy.deepcopy(PLOT_LAYOUT)
            _lay.update({"height": 240, "showlegend": False,
                         "yaxis": dict(title="DSCR (x)", gridcolor="#343841", rangemode="tozero"),
                         "xaxis": dict(title="Año del crédito", tickmode="linear", dtick=1),
                         "margin": dict(l=20, r=20, t=30, b=40)})
            fig_ds.update_layout(**_lay)
            st.plotly_chart(fig_ds, use_container_width=True)

    # ── Tarjetas comparativas por plazo ───────────────────────────────────────
    st.markdown(f'<div class="section-header">Comparativo de plazos · Hurdle rate {_hurdle_label}</div>',
                unsafe_allow_html=True)
    cols_pl = st.columns(len(ppa_plazos))
    for idx, pl in enumerate(ppa_plazos):
        r   = resultados[pl]
        _precio_este_plazo = ppa_precios_por_plazo[pl]
        vc  = "#4ade80" if r["vpn"]>0 else "#f87171"
        tis = f"{r['tir']:.1f}%" if r["tir"] is not None else "N/A"
        pbs      = f"{r['pb']} años" if r["pb"] is not None else f">{pl}a"
        pbs_disc = f"{r['pb_disc']} años" if r.get("pb_disc") is not None else f">{pl}a"
        pmc = "#4ade80" if r["pm"] and _precio_este_plazo>=r["pm"] else "#f87171"
        pms = f"${r['pm']:.4f}" if r["pm"] else "No viable"
        phs = f"${r['ph']:.4f}" if r.get("ph") else "N/A"
        phc = "#f59e0b" if r.get("ph") and _precio_este_plazo >= r["ph"] else "#94a3b8"
        lcoe_pl = r.get("lcoe", 0)
        pi_pl   = r.get("pi", 0)
        with cols_pl[idx]:
            st.markdown(f"""
<div class="snap-card" style="min-height:300px;padding:18px 12px;">
  <div class="sc-label" style="font-size:14px;font-weight:700;color:#f59e0b;margin-bottom:12px;">{pl} AÑOS</div>
  <div style="width:100%;text-align:left;display:flex;flex-direction:column;gap:8px;">
    <div><div class="sc-label" style="color:#f59e0b;">Precio evaluado</div>
         <div class="sc-val" style="color:#f59e0b;font-size:14px;">${_precio_este_plazo:.4f}/kWh</div></div>
    <div><div class="sc-label">VPN a WACC {ppa_wacc:.1f}%</div>
         <div class="sc-val" style="color:{'#4ade80' if r['vpn_wacc']>0 else '#f87171'};font-size:13px;">${r['vpn_wacc']:,.0f}</div></div>
    <div><div class="sc-label">VPN a hurdle {_hurdle_label}</div>
         <div class="sc-val" style="color:{vc};font-size:13px;">${r['vpn_hurdle']:,.0f}</div></div>
    <div><div class="sc-label">TIR equity</div>
         <div class="sc-val" style="color:#22d3ee;font-size:13px;">{tis}</div></div>
    <div><div class="sc-label">PI (VPN/Equity)</div>
         <div class="sc-val" style="color:{'#4ade80' if pi_pl>0 else '#f87171'};font-size:13px;">{pi_pl:+.1f}%</div></div>
    <div><div class="sc-label">LCOE</div>
         <div class="sc-val" style="color:#8b5cf6;font-size:13px;">${lcoe_pl:.4f}/kWh</div></div>
    <div><div class="sc-label">Payback simple</div>
         <div class="sc-val" style="color:#f9fafb;font-size:13px;">{pbs}</div></div>
    <div><div class="sc-label">Payback descontado</div>
         <div class="sc-val" style="color:#cbd5e1;font-size:13px;">{pbs_disc}</div></div>
    <div style="border-top:1px solid #2e3138;padding-top:8px;margin-top:2px;">
      <div class="sc-label">Precio mínimo viable (VPN=0)</div>
      <div class="sc-val" style="color:{pmc};font-size:13px;">{pms}/kWh</div></div>
    <div><div class="sc-label">Tarifa objetivo ({_hurdle_label})</div>
         <div class="sc-val" style="color:{phc};font-size:13px;">{phs}/kWh</div></div>
    <div><div class="sc-label">Valor de rescate</div>
         <div class="sc-val" style="color:#14b8a6;font-size:13px;">${r['valor_residual']:,.0f}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    # Tabla resumen
    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
    tabla_ppa = []
    for pl in ppa_plazos:
        r = resultados[pl]
        _precio_pl = ppa_precios_por_plazo[pl]
        tabla_ppa.append({
            "Plazo":                        f"{pl} años",
            "Precio evaluado":              f"${_precio_pl:.4f}/kWh",
            "Precio mínimo (VPN=0)":        f"${r['pm']:.4f}/kWh" if r["pm"] else "No viable",
            f"Tarifa obj. ({_hurdle_label})": f"${r['ph']:.4f}/kWh" if r.get("ph") else "N/A",
            f"VPN WACC {ppa_wacc:.1f}%":           f"${r['vpn_wacc']:,.0f}",
            f"VPN hurdle {_hurdle_label}":  f"${r['vpn_hurdle']:,.0f}",
            "TIR equity":                   f"{r['tir']:.1f}%" if r["tir"] else "N/A",
            "PI (VPN/Equity)":              f"{r.get('pi', 0):+.1f}%",
            "LCOE":                         f"${r.get('lcoe', 0):.4f}/kWh",
            "Payback simple":               f"{r['pb']} años" if r["pb"] is not None else f">{pl}a",
            "Payback desc.":               f"{r['pb_disc']} años" if r.get("pb_disc") is not None else f">{pl}a",
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
        fig_vp.add_hline(y=0, line_color="#94a3b8", line_width=1.5)
        lyt_vp = copy.deepcopy(PLOT_LAYOUT)
        lyt_vp.update({"height":300, "barmode": "group",
                       "yaxis": dict(title="VPN (MXN)", gridcolor="#343841", tickformat=","),
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
                       "yaxis": dict(title="MXN/kWh", gridcolor="#343841", tickformat=".4f"),
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
                   "yaxis": dict(title="MXN",gridcolor="#343841",tickformat=","),
                   "xaxis": dict(title="Año",tickmode="linear",dtick=max(1,ppa_plazo_minimo//10)),
                   "legend": dict(orientation="h",y=1.12,x=0.5,xanchor="center",bgcolor="rgba(0,0,0,0)"),
                   "margin": dict(l=20,r=20,t=50,b=40),"hovermode":"x unified"})
    fig_fl.update_layout(**lyt_fl)
    st.plotly_chart(fig_fl, use_container_width=True)

    # ═════════════════════════════════════════════════════════════════════════
    # PERSPECTIVA DEL COMPRADOR
    # ═════════════════════════════════════════════════════════════════════════
    # Todo lo anterior es la vista del desarrollador. Aquí se invierte el punto
    # de vista: el comprador no quiere saber la TIR del proyecto, quiere saber
    # si le conviene firmar el PPA, comprar el sistema, o no hacer nada.
    st.markdown('<div class="section-header">🧾 Perspectiva del comprador · '
                '¿comprar, contratar, o no hacer nada?</div>',
                unsafe_allow_html=True)

    with st.expander("⚙️ Supuestos del comprador — cámbialos, cambian la respuesta", expanded=False):
        _cc1, _cc2, _cc3 = st.columns(3)

        with _cc1:
            cli_tasa = st.slider(
                "Costo de capital del comprador (%)", 4.0, 30.0, 12.0, 0.5,
                key="cli_tasa",
                help="La tasa a la que el comprador descuenta sus propios flujos. "
                     "NO es el WACC del desarrollador. Para una industria mexicana "
                     "mediana suele estar entre 10 % y 16 %: es el costo de su "
                     "línea de crédito o el rendimiento de su mejor uso alterno "
                     "de capital. Este número decide la comparación más que "
                     "ningún otro.")
            cli_horizonte = st.slider(
                "Horizonte de comparación (años)", 10, 30, int(vida_util), 1,
                key="cli_horiz",
                help="Todas las modalidades se comparan sobre el mismo horizonte. "
                     "Comparar un PPA a 15 años contra un sistema propio a 25 en "
                     "sus plazos respectivos no es una comparación, es un truco.")
            cli_autoconsumo = st.slider(
                "Autoconsumo (%)", 50.0, 100.0, 100.0, 1.0, key="cli_ac",
                help="Fracción de la generación que se consume en sitio y por "
                     "tanto desplaza tarifa completa. El excedente bajo net "
                     "metering se acredita a un valor menor. Suponer 100 % cuando "
                     "el perfil de carga no acompaña a la curva solar es el error "
                     "más común de una propuesta comercial.") / 100.0

        with _cc2:
            cli_isr_on = st.checkbox(
                "Aplicar ISR (base después de impuestos)", value=True, key="cli_isr_on",
                help="El pago a CFE y el pago del PPA son gasto deducible; el "
                     "CAPEX del sistema propio también. Comparar antes de "
                     "impuestos infla el atractivo del PPA porque le quita al "
                     "sistema propio su ventaja fiscal.")
            cli_isr = st.slider("Tasa de ISR (%)", 0.0, 40.0, 30.0, 1.0,
                                key="cli_isr", disabled=not cli_isr_on)
            cli_art34 = st.checkbox(
                "Deducción Art. 34 LISR al 100 %", value=True, key="cli_art34",
                disabled=not cli_isr_on,
                help="El Art. 34 fracción XIII LISR permite deducir al 100 % en el "
                     "ejercicio la inversión en maquinaria de generación con "
                     "fuentes renovables, con la condición de mantenerla en "
                     "operación cinco años. Solo vale si hay utilidad fiscal "
                     "contra la cual aplicarlo — una empresa en pérdidas no "
                     "monetiza el escudo y debe desactivarlo.")

        with _cc3:
            cli_transfiere = st.checkbox(
                f"El activo se transfiere al cliente al año {ppa_plazo_minimo}",
                value=True, key="cli_transf",
                help="LA CLÁUSULA MÁS CARA DEL CONTRATO. Si al terminar el PPA el "
                     "sistema pasa al cliente, los años restantes cuestan solo "
                     "O&M. Si no, el cliente vuelve a pagar tarifa CFE completa. "
                     "La diferencia entre ambos supuestos suele superar todo el "
                     "ahorro del contrato. Si el borrador no lo dice, no está "
                     "pactado.")
            cli_deuda_pct = st.slider(
                "Deuda sobre CAPEX — turnkey financiado (%)", 0.0, 90.0, 70.0, 5.0,
                key="cli_deuda")
            _dc1, _dc2 = st.columns(2)
            cli_tasa_deuda = _dc1.number_input("Tasa (%)", 5.0, 30.0, 13.0, 0.5,
                                               key="cli_tasa_deuda")
            cli_plazo_deuda = _dc2.number_input("Plazo (años)", 1, 20, 7, 1,
                                                key="cli_plazo_deuda")

    _cap_mxn_cli = ppa_inversion_usd * usd_to_mxn

    ac_res = analisis_comprador(
        gen_anio1=ppa_gen_anual,
        tarifa_cfe=ppa_tarifa_cliente,
        inflacion_cfe=ppa_inflacion_cfe,
        precio_ppa=ppa_precio_manual,
        escalador_ppa=ppa_inflacion_tarifa,
        plazo_ppa=int(ppa_plazo_minimo),
        capex_mxn=_cap_mxn_cli,
        horizonte=int(cli_horizonte),
        degradacion_pct=ppa_degradacion,
        lid_pct=lid_pct,
        om_pct=ppa_om_pct,
        seguros_pct=ppa_seguros_pct,
        inflacion_om=ppa_inflacion_om,
        tasa_descuento=cli_tasa,
        isr_pct=cli_isr,
        aplicar_isr=cli_isr_on,
        deduccion_art34=cli_art34,
        deuda_pct=cli_deuda_pct,
        tasa_deuda=cli_tasa_deuda,
        plazo_deuda=int(cli_plazo_deuda),
        ppa_transfiere_activo=cli_transfiere,
        autoconsumo_frac=cli_autoconsumo,
    )
    _ops, _et = ac_res["opciones"], ac_res["etiquetas"]

    # ── Veredicto ────────────────────────────────────────────────────────────
    _mejor = ac_res["mejor"]
    _segundo = ac_res["orden"][1]
    _brecha = _ops[_segundo]["vp"] - _ops[_mejor]["vp"]

    st.markdown(
        f'<div style="background:linear-gradient(90deg,#1e2028,#17191f);'
        f'border-left:3px solid #f59e0b;border-radius:8px;padding:14px 18px;'
        f'margin:4px 0 14px;">'
        f'<div style="font-size:11px;color:#94a3b8;letter-spacing:1px;">'
        f'MENOR COSTO EN VALOR PRESENTE A {ac_res["n"]} AÑOS</div>'
        f'<div style="font-size:26px;font-weight:700;color:#f59e0b;line-height:1.3;">'
        f'{_et[_mejor]}</div>'
        f'<div style="font-size:13px;color:#cbd5e1;">'
        f'${_brecha:,.0f} MXN por debajo de la siguiente opción '
        f'({_et[_segundo]}) · costo nivelado '
        f'<b>${_ops[_mejor]["lcoe"]:.3f}/kWh</b> vs '
        f'<b>${_ops["nada"]["lcoe"]:.3f}/kWh</b> de la red</div></div>',
        unsafe_allow_html=True)

    # ── Tabla comparativa de modalidades ─────────────────────────────────────
    st.markdown('<div class="section-header">Comparativo de modalidades · '
                'misma energía, mismo horizonte, misma tasa</div>',
                unsafe_allow_html=True)

    _filas = []
    for _k in ["nada", "tk", "tkf", "ppa"]:
        _x = _ops[_k]
        _rank = ac_res["orden"].index(_k) + 1
        _filas.append({
            "#": f"{_rank}º" + (" ✓" if _rank == 1 else ""),
            "Modalidad": _et[_k],
            "Desembolso inicial": f"${_x['desembolso']:,.0f}",
            f"VP costo {ac_res['n']}a": f"${_x['vp']:,.0f}",
            "Costo nivelado": f"${_x['lcoe']:.3f}/kWh",
            "vs red": ("—" if _k == "nada"
                       else f"{(_x['lcoe']/_ops['nada']['lcoe']-1)*100:+.0f}%"),
            "Ahorro en VP": ("—" if _k == "nada" else f"${_x['ahorro_vp']:,.0f}"),
            "Costo año 1": f"${_x['flujo'][0]:,.0f}",
        })
    st.dataframe(pd.DataFrame(_filas), use_container_width=True, hide_index=True)

    st.caption(
        f"Costos después de {'ISR ' + format(cli_isr, '.0f') + ' %' if cli_isr_on else 'impuestos NO aplicados'}"
        f"{' con deducción Art. 34 al 100 %' if (cli_isr_on and cli_art34) else ''} · "
        f"descontados al {cli_tasa:.1f} % · autoconsumo {cli_autoconsumo*100:.0f} % · "
        f"{'activo transferido al cliente' if cli_transfiere else 'sin transferencia de activo'} "
        f"al término del PPA. **Menor VP gana**: las cuatro opciones entregan la misma energía, "
        f"así que la única diferencia relevante es cuánto cuesta obtenerla."
    )
    if any(_ops[_k]["flujo"][0] < 0 for _k in ("tk", "tkf")):
        st.caption(
            "El **costo año 1** del turnkey sale negativo: el escudo fiscal del "
            "Art. 34 supera al gasto de O&M de ese ejercicio, así que el primer "
            "año es de entrada neta de efectivo. No incluye el desembolso del "
            "CAPEX, que va aparte en su propia columna."
        )

    # ── Decisión incremental ─────────────────────────────────────────────────
    _tir_i = ac_res["tir_incremental"]
    _ind   = ac_res["tasa_indiferencia"]
    _vpn_i = ac_res["vpn_incremental"]
    _conv  = _vpn_i > 0

    _ind_txt = f"{_ind:.1f}%" if _ind is not None else "n/d"
    _tir_txt = f"{_tir_i:.1f}%" if _tir_i is not None else "n/d"
    _tir_met = ac_res.get("tir_metodo", "TIR")

    st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px;">
  <div class="snap-card">
    <div class="sc-label">VPN incremental · comprar vs PPA</div>
    <div class="sc-val" style="color:{'#4ade80' if _conv else '#f87171'};">${_vpn_i:,.0f}</div>
    <div class="sc-sub">{'comprar crea valor' if _conv else 'el PPA crea valor'}</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">{_tir_met} del CAPEX incremental</div>
    <div class="sc-val" style="color:#f59e0b;">{_tir_txt}</div>
    <div class="sc-sub">vs {cli_tasa:.1f}% de costo de capital{' · flujo con varios cambios de signo' if _tir_met == 'MIRR' else ''}</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Tasa de indiferencia</div>
    <div class="sc-val" style="color:#cbd5e1;">{_ind_txt}</div>
    <div class="sc-sub">arriba de esto conviene el PPA</div>
  </div>
  <div class="snap-card">
    <div class="sc-label">Escudo fiscal Art. 34</div>
    <div class="sc-val" style="color:#4ade80;">${ac_res['escudo_capex']:,.0f}</div>
    <div class="sc-sub">{'monetizable en el ejercicio 1' if ac_res['escudo_capex']>0 else 'no aplicado'}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.info(
        f"**Cómo leer la tasa de indiferencia.** Comprar el sistema exige "
        f"${_cap_mxn_cli:,.0f} MXN hoy para dejar de pagarle al desarrollador "
        f"durante {ppa_plazo_minimo} años. Ese desembolso rinde **{_tir_txt}**. "
        f"Si el capital del comprador cuesta menos que **{_ind_txt}**, comprar "
        f"gana; si cuesta más — porque ese dinero rinde más en su negocio, o "
        f"porque simplemente no lo tiene — el PPA gana.\n\n"
        f"El PPA no es peor por definición: convierte un CAPEX en un gasto "
        f"operativo y traslada el riesgo técnico al desarrollador. Lo que hay "
        f"que saber es **cuánto cuesta ese traslado**, y esta cifra lo dice."
    )

    # ── Trayectoria de precios y año de cruce ────────────────────────────────
    st.markdown('<div class="section-header">Precio PPA vs tarifa CFE · '
                '¿en qué año deja de convenir?</div>', unsafe_allow_html=True)

    _yrs = list(range(1, ac_res["n"] + 1))
    fig_px = go.Figure()
    fig_px.add_trace(go.Scatter(
        x=_yrs, y=ac_res["cfe_precio"], name="Tarifa CFE proyectada",
        mode="lines", line=dict(color=ROSE, width=2.5),
        hovertemplate="<b>Año %{x}</b><br>CFE: $%{y:.4f}/kWh<extra></extra>"))
    fig_px.add_trace(go.Scatter(
        x=_yrs[:int(ppa_plazo_minimo)],
        y=ac_res["ppa_precio"][:int(ppa_plazo_minimo)],
        name="Precio PPA contratado",
        mode="lines", line=dict(color=AMBER, width=2.5),
        hovertemplate="<b>Año %{x}</b><br>PPA: $%{y:.4f}/kWh<extra></extra>"))
    if ac_res["n"] > ppa_plazo_minimo:
        fig_px.add_trace(go.Scatter(
            x=_yrs[int(ppa_plazo_minimo) - 1:],
            y=ac_res["ppa_precio"][int(ppa_plazo_minimo) - 1:],
            name="PPA si se extendiera", mode="lines",
            line=dict(color=AMBER, width=1.6, dash="dot"),
            hovertemplate="<b>Año %{x}</b><br>PPA extrapolado: $%{y:.4f}<extra></extra>"))
    fig_px.add_hline(y=_ops[_mejor]["lcoe"], line_dash="dash", line_color="#4ade80",
                     annotation_text=f"Costo nivelado {_et[_mejor]}: ${_ops[_mejor]['lcoe']:.3f}",
                     annotation_position="bottom right",
                     annotation_font=dict(size=11, color="#4ade80"))
    if ac_res["cruce_ppa_cfe"]:
        fig_px.add_vline(x=ac_res["cruce_ppa_cfe"], line_dash="dot", line_color="#f87171",
                         annotation_text=f"⚠ cruce año {ac_res['cruce_ppa_cfe']}",
                         annotation_position="top",
                         annotation_font=dict(size=11, color="#f87171"))
    _lyt_px = copy.deepcopy(PLOT_LAYOUT)
    _lyt_px.update({"height": 330,
                    "yaxis": dict(title="MXN/kWh", gridcolor="#343841", tickformat=".2f"),
                    "xaxis": dict(title="Año", gridcolor="#343841",
                                  tickmode="linear", dtick=max(1, ac_res["n"] // 12)),
                    "legend": dict(orientation="h", y=1.14, x=0.5, xanchor="center",
                                   bgcolor="rgba(0,0,0,0)"),
                    "margin": dict(l=20, r=20, t=52, b=40), "hovermode": "x unified"})
    fig_px.update_layout(**_lyt_px)
    st.plotly_chart(fig_px, use_container_width=True)

    if ac_res["cruce_ppa_cfe"]:
        st.error(
            f"**El PPA se vuelve más caro que la red en el año "
            f"{ac_res['cruce_ppa_cfe']}**, dentro del plazo contratado. Con un "
            f"escalador de {ppa_inflacion_tarifa:.1f} % contra una inflación "
            f"tarifaria de {ppa_inflacion_cfe:.1f} %, el descuento inicial de "
            f"{abs(descuento_vs_cfe):.1f} % se agota. Desde ese año el comprador "
            f"paga de más y sigue atado al contrato. Negociar el escalador a la "
            f"baja vale más que negociar el precio inicial."
        )
    elif ac_res["cruce_teorico"]:
        st.warning(
            f"El escalador del PPA ({ppa_inflacion_tarifa:.1f} %) supera la "
            f"inflación tarifaria supuesta ({ppa_inflacion_cfe:.1f} %). El cruce "
            f"cae en el año {ac_res['cruce_teorico']:.0f} — fuera del plazo, pero "
            f"el margen se erosiona todos los años. Verifica la sensibilidad si "
            f"CFE sube menos de lo previsto."
        )
    else:
        st.success(
            f"El escalador del PPA ({ppa_inflacion_tarifa:.1f} %) queda por debajo "
            f"de la inflación tarifaria supuesta ({ppa_inflacion_cfe:.1f} %), así "
            f"que el descuento vs CFE **crece** con el tiempo. Ojo: eso depende "
            f"enteramente del supuesto de inflación de CFE, que es la variable más "
            f"incierta de todo el modelo."
        )

    # ── Costo acumulado descontado ───────────────────────────────────────────
    st.markdown('<div class="section-header">Costo acumulado en valor presente</div>',
                unsafe_allow_html=True)

    fig_ac = go.Figure()
    _cols = {"nada": "#6b7280", "tk": TEAL, "tkf": BLUE, "ppa": AMBER}
    for _k in ["nada", "tk", "tkf", "ppa"]:
        _acc, _s = [], _ops[_k]["desembolso"]
        for _i, _f in enumerate(_ops[_k]["flujo"]):
            _s += _f / (1.0 + cli_tasa / 100.0) ** (_i + 1)
            _acc.append(_s)
        fig_ac.add_trace(go.Scatter(
            x=_yrs, y=_acc, name=_et[_k], mode="lines",
            line=dict(color=_cols[_k], width=2.5 if _k == _mejor else 1.8,
                      dash="solid" if _k != "nada" else "dot"),
            hovertemplate=f"<b>{_et[_k]}</b><br>Año %{{x}}<br>"
                          "VP acumulado: $%{y:,.0f}<extra></extra>"))
    _lyt_ac = copy.deepcopy(PLOT_LAYOUT)
    _lyt_ac.update({"height": 330,
                    "yaxis": dict(title="MXN · valor presente", gridcolor="#343841",
                                  tickformat=","),
                    "xaxis": dict(title="Año", gridcolor="#343841",
                                  tickmode="linear", dtick=max(1, ac_res["n"] // 12)),
                    "legend": dict(orientation="h", y=1.14, x=0.5, xanchor="center",
                                   bgcolor="rgba(0,0,0,0)"),
                    "margin": dict(l=20, r=20, t=52, b=40), "hovermode": "x unified"})
    fig_ac.update_layout(**_lyt_ac)
    st.plotly_chart(fig_ac, use_container_width=True)
    st.caption(
        "La curva que quede más abajo al final del horizonte es la opción más "
        "barata. El turnkey arranca arriba por el CAPEX y cruza a las demás "
        "cuando la energía gratis compensa el desembolso: ese punto de cruce es "
        "el payback real, con impuestos y descuento incluidos."
    )

    # ── Banderas rojas del contrato PPA ──────────────────────────────────────
    st.markdown('<div class="section-header">🚩 Banderas rojas del contrato</div>',
                unsafe_allow_html=True)

    _flags = []

    if ppa_inflacion_tarifa > ppa_inflacion_cfe:
        _flags.append(("alta", "Escalador por encima de la inflación tarifaria",
            f"El PPA sube {ppa_inflacion_tarifa:.1f} %/año y CFE se proyecta a "
            f"{ppa_inflacion_cfe:.1f} %/año. El descuento se erosiona y termina "
            f"invirtiéndose. Un escalador sano va **igual o por debajo** de la "
            f"inflación tarifaria esperada; lo más limpio es indexarlo al INPC o "
            f"directamente a la tarifa CFE en lugar de fijar un porcentaje."))
    elif ppa_inflacion_tarifa == 0:
        _flags.append(("baja", "Escalador en cero",
            "Un PPA sin escalador es excelente para el comprador, pero verifica "
            "que el precio inicial no venga inflado para compensarlo."))

    if not cli_transfiere:
        _flags.append(("alta", "Sin transferencia del activo al término",
            f"Al año {ppa_plazo_minimo} el sistema sigue siendo del desarrollador "
            f"y el comprador vuelve a tarifa CFE completa con un techo ocupado. "
            f"Esto le cuesta "
            f"${abs(_ops['ppa']['vp'] - analisis_comprador(gen_anio1=ppa_gen_anual, tarifa_cfe=ppa_tarifa_cliente, inflacion_cfe=ppa_inflacion_cfe, precio_ppa=ppa_precio_manual, escalador_ppa=ppa_inflacion_tarifa, plazo_ppa=int(ppa_plazo_minimo), capex_mxn=_cap_mxn_cli, horizonte=int(cli_horizonte), degradacion_pct=ppa_degradacion, lid_pct=lid_pct, om_pct=ppa_om_pct, seguros_pct=ppa_seguros_pct, inflacion_om=ppa_inflacion_om, tasa_descuento=cli_tasa, isr_pct=cli_isr, aplicar_isr=cli_isr_on, deduccion_art34=cli_art34, ppa_transfiere_activo=True, autoconsumo_frac=cli_autoconsumo)['opciones']['ppa']['vp']):,.0f} MXN "
            f"en valor presente frente a un contrato con transferencia. Exige que "
            f"el contrato diga qué pasa el último día: transferencia a título "
            f"gratuito, opción de compra a valor residual definido con fórmula, o "
            f"retiro del equipo a cargo del desarrollador y restitución de cubierta."))

    if ppa_plazo_minimo >= 20:
        _flags.append(("media", f"Plazo largo — {ppa_plazo_minimo} años",
            "Arriba de 20 años el contrato sobrevive a la vida de casi cualquier "
            "decisión industrial: cambio de proceso, mudanza, venta de la planta. "
            "Exige cláusula de terminación anticipada con fórmula de pago "
            "explícita, y de cesión del contrato si se vende el inmueble."))

    if abs(descuento_vs_cfe) < 10 and descuento_vs_cfe < 0:
        _flags.append(("media", f"Descuento inicial delgado — {abs(descuento_vs_cfe):.1f} %",
            "Por debajo de 10 % de descuento el margen no absorbe un error de "
            "estimación de generación ni un año malo de recurso. Verifica que la "
            "tarifa de referencia sea tu tarifa real ponderada, no la de lista."))

    if cli_autoconsumo >= 0.999:
        _flags.append(("media", "Autoconsumo supuesto al 100 %",
            "El modelo asume que toda la generación se consume en sitio. Si la "
            "planta para los domingos, cierra en vacaciones, o su carga es "
            "nocturna, una parte se va a la red y se acredita por debajo de la "
            "tarifa. Pide el perfil de carga horario y contrástalo con el perfil "
            "de generación antes de firmar."))

    _flags.append(("info", "Garantía de desempeño — verificar que exista",
        "El contrato debe garantizar generación mínima anual (típico 95 % del "
        "P50 comprometido) con penalización o crédito si no se alcanza, medida "
        "con equipo clase A conforme IEC 61724-1 y ajustada por irradiancia real "
        "del periodo. Sin ajuste por irradiancia la garantía no significa nada: "
        "el desarrollador siempre podrá alegar un año de mal recurso."))

    _flags.append(("info", "Responsabilidad de O&M, seguros y reemplazos",
        "Debe decir explícitamente quién paga limpieza, monitoreo, reposición de "
        "inversores (año 12–15 típico), seguro de daño físico y de responsabilidad "
        "civil, y quién asume el riesgo de un cambio regulatorio o tarifario. "
        "En un PPA bien estructurado todo eso es del desarrollador — si el "
        "borrador guarda silencio, terminará siendo del comprador."))

    _flags.append(("info", "Riesgo de cubierta y desmantelamiento",
        "El arreglo ocupa el techo entre 15 y 25 años. Define quién responde por "
        "filtraciones, quién paga el retiro y la reinstalación si hay que "
        "reimpermeabilizar, y en qué estado se devuelve la cubierta al final."))

    _ico = {"alta": ("🔴", "#f87171"), "media": ("🟡", "#fbbf24"),
            "baja": ("🔵", "#60a5fa"), "info": ("⚪", "#94a3b8")}
    _n_alta = sum(1 for f in _flags if f[0] == "alta")

    if _n_alta:
        st.markdown(
            f'<div style="color:#f87171;font-size:13px;font-weight:600;'
            f'margin-bottom:8px;">{_n_alta} punto{"s" if _n_alta > 1 else ""} '
            f'de atención alta en la configuración actual.</div>',
            unsafe_allow_html=True)

    for _sev, _tit, _txt in _flags:
        _e, _c = _ico[_sev]
        with st.expander(f"{_e}  {_tit}", expanded=(_sev == "alta")):
            st.markdown(f'<div style="font-size:13px;color:#cbd5e1;">{_txt}</div>',
                        unsafe_allow_html=True)

    st.caption(
        "Esta lista es un punto de partida de revisión comercial, no una opinión "
        "legal. Un PPA es un contrato de largo plazo con implicaciones fiscales y "
        "de propiedad: revísalo con abogado antes de firmar."
    )

    # ── Ahorro anual vs CFE (vista original) ─────────────────────────────────
    st.markdown('<div class="section-header">Ahorro anual vs CFE · durante el contrato</div>',
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
                   "yaxis": dict(title="MXN/año",gridcolor="#343841",tickformat=","),
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
    <div class="sc-label">Ahorro nominal acumulado</div>
    <div class="sc-val" style="color:#4ade80;">${ahorro_total:,.0f}</div>
    <div class="sc-sub">MXN sin descontar · {ppa_plazo_minimo} años</div>
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

    st.caption(
        "⚠️ El **ahorro nominal acumulado** es la cifra que más aparece en las "
        "propuestas comerciales y la menos útil: suma pesos de años distintos "
        "como si valieran lo mismo. Para decidir, usa el comparativo de "
        "modalidades de arriba, que está en valor presente."
    )


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
            disabled=usando_irr_default,
            use_container_width=True,
            type="primary",
        )
    with _ppa_exp2:
        if st.button("📝 Generar Caso de Negocio (.docx)",
                     disabled=usando_irr_default,
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
                        ppa_precios_por_plazo=ppa_precios_por_plazo,
                    )
                    st.session_state["word_ppa_bytes"] = _word_bytes
                    st.success("✅ Documento generado")
                except Exception as _e:
                    st.error(f"❌ Error generando Word: {_e}")
        if "word_ppa_bytes" in st.session_state:
            st.download_button(
                "⬇️ Descargar Caso de Negocio (.docx)",
                data=st.session_state["word_ppa_bytes"],
                file_name=f"CasoNegocio_PPA_{proj_loc[:20].replace(' ','_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA COMPRADOR — cómo pedir, cómo comparar, cómo decidir
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        '<div style="background:linear-gradient(90deg,#1e2028,#17191f);'
        'border-left:3px solid #f59e0b;border-radius:8px;padding:16px 20px;'
        'margin-bottom:16px;">'
        '<div style="font-size:20px;font-weight:700;color:#f59e0b;">'
        'Herramientas del comprador</div>'
        '<div style="font-size:13px;color:#cbd5e1;margin-top:6px;line-height:1.6;">'
        'Comprar energía solar mal no suele ser un problema de precio: es un '
        'problema de comparación. Tres propuestas con potencias distintas, '
        'generaciones calculadas sobre supuestos distintos y alcances que no '
        'coinciden no se pueden poner una junto a otra, y la decisión termina '
        'cayendo en el precio total — el criterio que premia a quien recortó '
        'calidad o infló la producción.'
        '<br><br>Esta pestaña hace dos cosas: genera una solicitud que obliga a '
        'todos a responder sobre la misma base, y traduce las respuestas a un '
        'solo número comparable.</div></div>',
        unsafe_allow_html=True)

    sub_rfq, sub_cmp, sub_guia = st.tabs([
        "  📨 Solicitud de cotización",
        "  ⚖️ Comparar cotizaciones",
        "  📚 Guía rápida",
    ])

    # ═════════════════════════════════════════════════════════════════════════
    # A · SOLICITUD DE COTIZACIÓN
    # ═════════════════════════════════════════════════════════════════════════
    with sub_rfq:
        st.markdown('<div class="section-header">Hipótesis que todo licitante '
                    'debe declarar</div>', unsafe_allow_html=True)
        st.caption(
            "Sin estos diez puntos, una cifra de generación no es verificable. "
            "Cada uno trae el porqué para que puedas defenderlo en la junta de "
            "aclaraciones."
        )

        for _t, _d in hipotesis_obligatorias():
            with st.expander(f"▸  {_t}"):
                st.markdown(f'<div style="font-size:13px;color:#cbd5e1;'
                            f'line-height:1.65;">{_d}</div>',
                            unsafe_allow_html=True)

        st.markdown('<div class="section-header">Formato único de respuesta</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Pide que la propuesta abra con esta tabla, en este orden. Convierte "
            "tres PDFs de sesenta páginas en tres columnas comparables."
        )
        st.dataframe(
            pd.DataFrame([{"Concepto": c, "Unidad": u, "Nota": n}
                          for c, u, n in formato_respuesta()]),
            use_container_width=True, hide_index=True, height=430)

        st.markdown('<div class="section-header">Criterios de evaluación</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Publícalos junto con la solicitud. Cuando un proveedor sabe que gana "
            "el costo nivelado y no el precio, deja de recortar calidad para bajar "
            "el total — y esa es la mitad del valor de este documento."
        )
        _ce = criterios_evaluacion()
        st.dataframe(
            pd.DataFrame([{"Criterio": c, "Peso": f"{p} %", "Qué se evalúa": d}
                          for c, p, d in _ce]),
            use_container_width=True, hide_index=True)

        _fig_ce = go.Figure(go.Bar(
            x=[p for _, p, _ in _ce], y=[c for c, _, _ in _ce],
            orientation="h",
            marker_color=[AMBER, TEAL, BLUE, VIOLET, "#6b7280"],
            hovertemplate="<b>%{y}</b><br>Peso: %{x} %<extra></extra>"))
        _l_ce = copy.deepcopy(PLOT_LAYOUT)
        _l_ce.update({"height": 240,
                      "xaxis": dict(title="Peso (%)", gridcolor="#343841"),
                      "yaxis": dict(autorange="reversed", gridcolor="#343841"),
                      "margin": dict(l=10, r=20, t=20, b=40), "showlegend": False})
        _fig_ce.update_layout(**_l_ce)
        st.plotly_chart(_fig_ce, use_container_width=True)

        # ── Documento descargable ────────────────────────────────────────────
        st.markdown('<div class="section-header">Generar el documento</div>',
                    unsafe_allow_html=True)

        _rc1, _rc2 = st.columns(2)
        rfq_empresa = _rc1.text_input("Empresa convocante", "—", key="rfq_emp")
        rfq_contacto = _rc2.text_input("Contacto para aclaraciones", "—", key="rfq_cto")
        _rd1, _rd2 = st.columns(2)
        rfq_fecha_limite = _rd1.text_input("Fecha límite de entrega", "—", key="rfq_fl")
        rfq_visita = _rd2.text_input("Fecha de visita de sitio", "—", key="rfq_vs")

        if st.button("📨 Generar solicitud de cotización",
                     type="primary", use_container_width=True, key="btn_rfq"):
            _L = []
            _L.append("═" * 78)
            _L.append("SOLICITUD DE COTIZACIÓN")
            _L.append("SISTEMA FOTOVOLTAICO DE GENERACIÓN DISTRIBUIDA")
            _L.append("═" * 78)
            _L.append("")
            _L.append(f"  Convocante        : {rfq_empresa}")
            _L.append(f"  Ubicación         : {proj_loc}")
            _L.append(f"  Contacto          : {rfq_contacto}")
            _L.append(f"  Visita de sitio   : {rfq_visita}")
            _L.append(f"  Entrega de ofertas: {rfq_fecha_limite}")
            _L.append("")
            _L.append("─" * 78)
            _L.append("1. OBJETO")
            _L.append("─" * 78)
            _L.append("")
            for _l in _envolver(
                "Se solicita cotización llave en mano para el suministro, "
                "instalación, puesta en marcha e interconexión de un sistema "
                "fotovoltaico bajo el esquema de Generación Distribuida.", 74):
                _L.append(f"  {_l}")
            _L.append("")
            _L.append(f"  Capacidad de referencia : {kwp:,.1f} kWp DC")
            _L.append(f"  Generación de referencia: {annual_gen_base:,.0f} kWh/año")
            _L.append(f"  Rendimiento implícito   : {annual_gen_base/max(kwp,1e-6):,.0f} kWh/kWp/año")
            _L.append("")
            for _l in _envolver(
                "Estas cifras son de referencia y NO limitan la propuesta. El "
                "licitante debe presentar su propio dimensionamiento y sostenerlo "
                "con la simulación correspondiente. Se calcularon con: " +
                GEOM_NOTA_CORTA + f" PR {pr_pct:.0f} %.", 74):
                _L.append(f"  {_l}")
            _L.append("")
            _L.append("─" * 78)
            _L.append("2. HIPÓTESIS DE CÁLCULO DE DECLARACIÓN OBLIGATORIA")
            _L.append("─" * 78)
            _L.append("")
            for _l in _envolver(
                "La propuesta que no declare TODOS los puntos siguientes será "
                "desechada sin evaluación. No es una formalidad: sin ellos las "
                "generaciones ofertadas no son comparables entre sí.", 74):
                _L.append(f"  {_l}")
            _L.append("")
            for _i, (_t, _d) in enumerate(hipotesis_obligatorias(), 1):
                _L.append(f"  2.{_i}  {_t.upper()}")
                for _l in _envolver(_d, 70):
                    _L.append(f"       {_l}")
                _L.append("")
            _L.append("─" * 78)
            _L.append("3. FORMATO ÚNICO DE RESPUESTA")
            _L.append("─" * 78)
            _L.append("")
            for _l in _envolver(
                "La propuesta debe abrir con esta tabla completa, en este orden, "
                "antes de cualquier material descriptivo.", 74):
                _L.append(f"  {_l}")
            _L.append("")
            _L.append(f"  {'CONCEPTO':<42}{'UNIDAD':<16}VALOR")
            _L.append(f"  {'-'*42}{'-'*16}{'-'*18}")
            for _c, _u, _n in formato_respuesta():
                _L.append(f"  {_c:<42}{_u:<16}__________")
            _L.append("")
            _L.append("─" * 78)
            _L.append("4. CRITERIOS DE EVALUACIÓN")
            _L.append("─" * 78)
            _L.append("")
            for _l in _envolver(
                "La adjudicación NO se decide por precio total. Se decide por "
                "costo nivelado de la energía sobre supuestos comunes, con los "
                "pesos siguientes:", 74):
                _L.append(f"  {_l}")
            _L.append("")
            for _c, _p, _d in criterios_evaluacion():
                _L.append(f"  • {_c}  —  {_p} %")
                for _l in _envolver(_d, 70):
                    _L.append(f"      {_l}")
                _L.append("")
            for _l in _envolver(
                "La generación que se usará para calcular el costo nivelado es la "
                "que resulte de VERIFICAR la propuesta contra los supuestos "
                "comunes de esta solicitud, no la declarada por el licitante. Una "
                "generación no sostenida por la simulación será ajustada a la "
                "baja para efectos de evaluación.", 74):
                _L.append(f"  {_l}")
            _L.append("")
            _L.append("─" * 78)
            _L.append("5. GARANTÍAS MÍNIMAS EXIGIDAS")
            _L.append("─" * 78)
            _L.append("")
            for _g in [
                ("Producto del módulo", "12 años mínimo contra defectos de fabricación"),
                ("Potencia del módulo", "25 años mínimo, con curva de degradación explícita "
                                        "y potencia residual garantizada al año 25"),
                ("Inversor", "10 años mínimo; indicar costo de extensión a 20 años"),
                ("Mano de obra e instalación", "5 años mínimo, incluye estructura y "
                                               "estanqueidad de las penetraciones en cubierta"),
                ("Desempeño del sistema", "95 % del P50 comprometido durante los primeros "
                                          "5 años, medido conforme IEC 61724-1 con equipo "
                                          "clase A y AJUSTADO POR IRRADIANCIA REAL del "
                                          "periodo. Sin el ajuste por irradiancia la "
                                          "garantía es inejecutable: cualquier faltante se "
                                          "atribuirá a un mal año de recurso."),
                ("Cubierta", "El licitante responde por filtraciones atribuibles a la "
                             "instalación durante toda la vigencia de la garantía de obra "
                             "y entrega la cubierta en su estado original al desmantelar."),
            ]:
                _L.append(f"  • {_g[0]}")
                for _l in _envolver(_g[1], 70):
                    _L.append(f"      {_l}")
                _L.append("")
            _L.append("─" * 78)
            _L.append("6. ESPECIFICACIÓN TÉCNICA Y ENTREGABLES")
            _L.append("─" * 78)
            _L.append("")
            _L.append(tor_text)
            _L.append("")
            _L.append("═" * 78)
            _L.append("FIN DE LA SOLICITUD")
            _L.append("═" * 78)
            _L.append("")
            for _l in _envolver(
                "Documento generado con una herramienta abierta de evaluación "
                "preliminar. Las cifras de referencia son estimaciones de "
                "pre-dimensionamiento (±15 %) y no sustituyen ingeniería de "
                "detalle ni un Energy Yield Assessment de Ingeniero Independiente.", 74):
                _L.append(_l)

            st.session_state["rfq_text"] = "\n".join(_L)
            st.success("✅ Solicitud generada")

        if "rfq_text" in st.session_state:
            st.download_button(
                "⬇️ Descargar solicitud de cotización (.txt)",
                data=st.session_state["rfq_text"].encode("utf-8"),
                file_name=f"SolicitudCotizacion_{proj_loc[:20].replace(' ','_')}.txt",
                mime="text/plain", use_container_width=True)
            with st.expander("👁️ Vista previa"):
                st.code(st.session_state["rfq_text"][:6000], language=None)

    # ═════════════════════════════════════════════════════════════════════════
    # B · COMPARAR COTIZACIONES
    # ═════════════════════════════════════════════════════════════════════════
    with sub_cmp:
        st.markdown('<div class="section-header">Supuestos comunes de evaluación</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Estos valores se aplican por igual a todas las propuestas. Lo único "
            "que las distingue es su precio, su generación y su O&M — que es "
            "exactamente lo que se quiere comparar."
        )
        _e1, _e2, _e3, _e4 = st.columns(4)
        ev_horiz = _e1.number_input("Horizonte (años)", 10, 30, 25, 1, key="ev_h")
        ev_tasa  = _e2.number_input("Tasa de descuento (%)", 4.0, 25.0, 12.0, 0.5, key="ev_t")
        ev_deg   = _e3.number_input("Degradación (%/año)", 0.2, 1.5, 0.50, 0.05, key="ev_d",
                                    help="Se impone la misma a todos. Si un licitante "
                                         "declara menos, no se le premia por ello.")
        ev_isr   = _e4.number_input("ISR (%)", 0.0, 40.0, 30.0, 1.0, key="ev_i")
        _ev_art34 = st.checkbox("Aplicar deducción Art. 34 LISR al 100 %",
                                value=True, key="ev_a34")

        _rend_ref = (annual_gen_base / kwp) if kwp > 0 else 0.0
        st.caption(
            f"Referencia calculada para este sitio: **{_rend_ref:,.0f} kWh/kWp/año** "
            f"({GEOM_NOTA_CORTA} PR {pr_pct:.0f} %). Una propuesta que prometa más "
            f"de 12 % por encima queda marcada."
        )

        st.markdown('<div class="section-header">Cotizaciones recibidas</div>',
                    unsafe_allow_html=True)
        n_cot = st.slider("¿Cuántas cotizaciones vas a comparar?", 2, 4, 3, 1, key="n_cot")

        _cots = []
        _cot_cols = st.columns(n_cot)
        for _i in range(n_cot):
            with _cot_cols[_i]:
                st.markdown(f'<div style="font-size:13px;font-weight:700;'
                            f'color:#f59e0b;margin-bottom:6px;">Cotización {_i+1}</div>',
                            unsafe_allow_html=True)
                _nm = st.text_input("Proveedor", f"Proveedor {chr(65+_i)}",
                                    key=f"cot_nm_{_i}")
                _pr = st.number_input("Precio total (MXN sin IVA)", 0.0, 500_000_000.0,
                                      float(round(kwp * costo_kwp * usd_to_mxn, 0)),
                                      1000.0, key=f"cot_pr_{_i}")
                _kw = st.number_input("Potencia (kWp DC)", 0.1, 100_000.0,
                                      float(round(kwp, 1)), 0.1, key=f"cot_kw_{_i}")
                _gn = st.number_input("Generación año 1 declarada (kWh)", 0.0,
                                      500_000_000.0, float(round(annual_gen_base, 0)),
                                      100.0, key=f"cot_gn_{_i}")
                _om = st.number_input("O&M anual (MXN)", 0.0, 50_000_000.0,
                                      float(round(kwp * costo_kwp * usd_to_mxn * 0.017, 0)),
                                      500.0, key=f"cot_om_{_i}")
                with st.expander("Datos declarados"):
                    _prd = st.number_input("PR declarado", 0.0, 1.0, 0.0, 0.01,
                                           key=f"cot_prd_{_i}",
                                           help="0 = no lo declaró")
                    _dgd = st.number_input("Degradación declarada (%/año)", 0.0, 2.0,
                                           0.0, 0.05, key=f"cot_dg_{_i}",
                                           help="0 = no la declaró")
                    _dca = st.number_input("DC/AC declarado", 0.0, 2.0, 0.0, 0.01,
                                           key=f"cot_dc_{_i}",
                                           help="0 = no lo declaró")
                    _gpo = st.number_input("Garantía de potencia (años)", 0, 40, 0, 1,
                                           key=f"cot_gp_{_i}", help="0 = no la declaró")
                _cots.append(dict(nombre=_nm, precio=_pr, kwp=_kw, gen=_gn, om=_om,
                                  pr=_prd, deg=_dgd, dcac=_dca, gp=_gpo))

        # ── Evaluación ───────────────────────────────────────────────────────
        _res_cot = []
        for _c in _cots:
            _n = normalizar_cotizacion(
                _c["nombre"], _c["precio"], _c["kwp"], _c["gen"], usd_to_mxn,
                pr_declarado=_c["pr"], degradacion=_c["deg"], dc_ac=_c["dcac"],
                om_anual_mxn=_c["om"], gar_potencia=_c["gp"],
                gen_referencia_kwh_kwp=_rend_ref,
                factor_transposicion=(_POA_R and sum(_POA_R)/12) or 1.0)

            # Generación DECLARADA vs generación VERIFICADA. La verificada acota
            # la promesa al rendimiento de referencia del sitio: si el proveedor
            # promete más sin sostenerlo, no se le premia en la evaluación.
            _gen_ver = min(_c["gen"], _rend_ref * _c["kwp"] * 1.12) if _rend_ref > 0 else _c["gen"]

            _n["lcoe_decl"] = lcoe_cotizacion(
                _c["precio"], _c["gen"], _c["om"], horizonte=int(ev_horiz),
                tasa=ev_tasa, degradacion=ev_deg, isr_pct=ev_isr, art34=_ev_art34)
            _n["lcoe_ver"] = lcoe_cotizacion(
                _c["precio"], _gen_ver, _c["om"], horizonte=int(ev_horiz),
                tasa=ev_tasa, degradacion=ev_deg, isr_pct=ev_isr, art34=_ev_art34)
            _n["gen_ver"] = _gen_ver
            _res_cot.append(_n)

        _ganador = min(_res_cot, key=lambda x: x["lcoe_ver"])
        _mas_barato = min(_res_cot, key=lambda x: x["precio_mxn"])

        st.markdown('<div class="section-header">Comparación normalizada</div>',
                    unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{
            "Proveedor": _r["nombre"],
            "Precio total": f"${_r['precio_mxn']:,.0f}",
            "USD/Wp": f"{_r['usd_wp']:.3f}",
            "kWp": f"{_r['kwp']:,.1f}",
            "kWh/kWp declarado": f"{_r['rendimiento']:,.0f}",
            "Gen. verificada": f"{_r['gen_ver']:,.0f}",
            "LCOE declarado": f"${_r['lcoe_decl']:.3f}",
            "LCOE verificado": f"${_r['lcoe_ver']:.3f}",
            "🚩": ("—" if _r["n_alta"] == 0 else f"{_r['n_alta']} alta"
                   + ("s" if _r["n_alta"] > 1 else "")),
        } for _r in _res_cot]), use_container_width=True, hide_index=True)

        _c1, _c2 = st.columns(2)
        with _c1:
            st.markdown(
                f'<div class="snap-card"><div class="sc-label">Mejor costo nivelado '
                f'verificado</div><div class="sc-val" style="color:#4ade80;">'
                f'{_ganador["nombre"]}</div><div class="sc-sub">'
                f'${_ganador["lcoe_ver"]:.3f}/kWh · {_ganador["n_alta"]} banderas altas'
                f'</div></div>', unsafe_allow_html=True)
        with _c2:
            st.markdown(
                f'<div class="snap-card"><div class="sc-label">Precio total más bajo'
                f'</div><div class="sc-val" style="color:#f59e0b;">'
                f'{_mas_barato["nombre"]}</div><div class="sc-sub">'
                f'${_mas_barato["precio_mxn"]:,.0f} · {_mas_barato["n_alta"]} banderas altas'
                f'</div></div>', unsafe_allow_html=True)

        if _ganador["nombre"] != _mas_barato["nombre"]:
            st.warning(
                f"**La más barata no es la mejor.** {_mas_barato['nombre']} tiene el "
                f"precio total más bajo pero {_ganador['nombre']} entrega energía más "
                f"barata a lo largo del horizonte. La diferencia está en generación, "
                f"O&M o ambos — que es justo lo que un comparativo por precio total "
                f"no ve."
            )
        if _ganador["n_alta"] > 0:
            st.error(
                f"**{_ganador['nombre']} gana en costo nivelado pero tiene "
                f"{_ganador['n_alta']} bandera{'s' if _ganador['n_alta']>1 else ''} "
                f"de atención alta.** Un LCOE bajo construido sobre una generación "
                f"que no se sostiene es un LCOE ficticio. Resuelve las banderas "
                f"antes de adjudicar."
            )

        # Gráfica LCOE declarado vs verificado
        _fig_lc = go.Figure()
        _fig_lc.add_trace(go.Bar(
            x=[_r["nombre"] for _r in _res_cot],
            y=[_r["lcoe_decl"] for _r in _res_cot],
            name="LCOE con generación declarada", marker_color="#4b5563",
            hovertemplate="<b>%{x}</b><br>$%{y:.3f}/kWh<extra></extra>"))
        _fig_lc.add_trace(go.Bar(
            x=[_r["nombre"] for _r in _res_cot],
            y=[_r["lcoe_ver"] for _r in _res_cot],
            name="LCOE con generación verificada", marker_color=AMBER,
            hovertemplate="<b>%{x}</b><br>$%{y:.3f}/kWh<extra></extra>"))
        _l_lc = copy.deepcopy(PLOT_LAYOUT)
        _l_lc.update({"height": 300, "barmode": "group",
                      "yaxis": dict(title="MXN/kWh", gridcolor="#343841", tickformat=".2f"),
                      "xaxis": dict(gridcolor="#343841"),
                      "legend": dict(orientation="h", y=1.15, x=0.5, xanchor="center",
                                     bgcolor="rgba(0,0,0,0)"),
                      "margin": dict(l=20, r=20, t=52, b=40)})
        _fig_lc.update_layout(**_l_lc)
        st.plotly_chart(_fig_lc, use_container_width=True)
        st.caption(
            "La barra gris usa la generación que declara el proveedor; la ámbar la "
            "acota al rendimiento de referencia del sitio más 12 %. Una brecha "
            "grande entre ambas significa que el atractivo de esa propuesta "
            "descansa en una promesa de producción, no en su precio."
        )

        st.markdown('<div class="section-header">Banderas por propuesta</div>',
                    unsafe_allow_html=True)
        _ico2 = {"alta": "🔴", "media": "🟡", "baja": "🔵"}
        for _r in _res_cot:
            _lbl = (f"{_r['nombre']} — sin observaciones" if not _r["banderas"]
                    else f"{_r['nombre']} — {len(_r['banderas'])} observacion"
                         f"{'es' if len(_r['banderas'])>1 else ''}"
                         f" ({_r['n_alta']} alta{'s' if _r['n_alta']!=1 else ''})")
            with st.expander(_lbl, expanded=_r["n_alta"] > 0):
                if not _r["banderas"]:
                    st.markdown('<div style="font-size:13px;color:#4ade80;">'
                                'Los parámetros declarados caen dentro de rangos '
                                'defendibles.</div>', unsafe_allow_html=True)
                for _s, _t in _r["banderas"]:
                    st.markdown(f'<div style="font-size:13px;color:#cbd5e1;'
                                f'margin-bottom:8px;line-height:1.6;">'
                                f'{_ico2[_s]} {_t}</div>', unsafe_allow_html=True)

        st.caption(
            "Los rangos de verificación usados: rendimiento "
            f"{RANGO_RENDIMIENTO_MX[0]:,.0f}–{RANGO_RENDIMIENTO_MX[1]:,.0f} kWh/kWp/año · "
            f"PR sobre POA {RANGO_PR_POA[0]:.2f}–{RANGO_PR_POA[1]:.2f} · "
            f"degradación {RANGO_DEGRADACION[0]:.2f}–{RANGO_DEGRADACION[1]:.2f} %/año · "
            f"DC/AC {RANGO_DC_AC[0]:.2f}–{RANGO_DC_AC[1]:.2f} · "
            f"precio {RANGO_COSTO_USD_WP[0]:.2f}–{RANGO_COSTO_USD_WP[1]:.2f} USD/Wp. "
            "Son referencias de mercado mexicano para GD industrial, no reglas: "
            "una propuesta fuera de rango no está mal, está sin justificar."
        )

    # ═════════════════════════════════════════════════════════════════════════
    # C · GUÍA RÁPIDA
    # ═════════════════════════════════════════════════════════════════════════
    with sub_guia:
        st.markdown('<div class="section-header">Los seis errores que más caros '
                    'salen</div>', unsafe_allow_html=True)

        for _t, _d in [
            ("Comparar por precio total en vez de por costo de la energía",
             "Dos propuestas de 300 kWp y 260 kWp no son la misma compra. El "
             "número que compara todo es el costo nivelado: precio más O&M "
             "descontados, divididos entre la energía descontada del horizonte. "
             "Está en la hoja de comparación de esta pestaña."),

            ("Aceptar una generación sin preguntar sobre qué plano se calculó",
             "La misma planta rinde entre 0 % y 17 % más según se calcule sobre "
             "irradiancia horizontal o sobre el plano inclinado del generador. Un "
             "proveedor puede subir su cifra suponiendo una inclinación que no va "
             "a construir. Pregunta siempre: plano, inclinación, azimut."),

            ("Creerle a un rendimiento por encima de 1,800 kWh/kWp",
             "En México las plantas reales entregan entre 1,500 y 1,750 kWh/kWp "
             "al año. Arriba de eso hace falta recurso excepcional, inclinación "
             "óptima y temperatura baja simultáneamente. Cada 100 kWh/kWp "
             "inventados bajan el costo nivelado aparente cerca de 6 % y desplazan "
             "a las propuestas honestas."),

            ("Dejar el O&M fuera de la comparación",
             "El O&M de un sistema en cubierta industrial cuesta entre 1.2 % y "
             "2.2 % del CAPEX al año, incluyendo limpieza, monitoreo, seguros y "
             "la reposición del inversor alrededor del año 12–15. Una propuesta "
             "que no lo cotiza se ve más barata y no lo es."),

            ("Firmar un PPA sin la cláusula de fin de plazo",
             "Es la cláusula más cara del contrato y la que más veces falta. Si al "
             "terminar el PPA el sistema no pasa al comprador, este vuelve a pagar "
             "tarifa completa con el techo ocupado. La diferencia en valor "
             "presente entre un contrato con transferencia y uno sin ella suele "
             "superar todo el ahorro del contrato."),

            ("Aceptar una garantía de desempeño sin ajuste por irradiancia",
             "Una garantía que promete 95 % del P50 pero no se ajusta por la "
             "irradiancia real del periodo es inejecutable: cualquier faltante se "
             "atribuirá a un mal año de recurso y el comprador no tendrá cómo "
             "rebatirlo. La medición debe seguir IEC 61724-1 con equipo clase A."),
        ]:
            with st.expander(f"▸  {_t}", expanded=False):
                st.markdown(f'<div style="font-size:13px;color:#cbd5e1;'
                            f'line-height:1.65;">{_d}</div>',
                            unsafe_allow_html=True)

        st.markdown('<div class="section-header">Las cinco preguntas que separan '
                    'una propuesta seria de un folleto</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:13px;color:#cbd5e1;line-height:1.9;">'
            '1. ¿Me entregas el archivo nativo de la simulación, no solo el PDF?<br>'
            '2. ¿Qué PR usaste y cómo se descompone por tipo de pérdida?<br>'
            '3. ¿Cuánta energía pierdo por recorte del inversor con ese DC/AC?<br>'
            '4. ¿Tu degradación declarada coincide con la garantía del módulo que '
            'me estás cotizando?<br>'
            '5. ¿Quién paga el reemplazo del inversor en el año 13, y con qué '
            'garantía?</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">Orden recomendado de trabajo</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:13px;color:#cbd5e1;line-height:1.9;">'
            '<b>1.</b> Dimensiona en la pestaña Turnkey con tu recibo real y el '
            'recurso de tu sitio. Ese número es tu referencia, no tu diseño.<br>'
            '<b>2.</b> Genera la solicitud de cotización y mándala igual a todos. '
            'Publica los criterios de evaluación con ella.<br>'
            '<b>3.</b> Captura las respuestas en la hoja de comparación y resuelve '
            'las banderas antes de mirar precios.<br>'
            '<b>4.</b> Si te ofrecen un PPA, corre la pestaña PPA y mira el '
            'comparativo de modalidades: puede que comprar te convenga más, y '
            'ahora tendrás el número que lo prueba.<br>'
            '<b>5.</b> Antes de firmar cualquier cosa, exige simulación en PVsyst '
            'o Helioscope con la geometría real. Todo lo anterior es '
            'pre-dimensionamiento de ±15 %.</div>', unsafe_allow_html=True)

        st.info(
            "**Qué es y qué no es esta herramienta.** Es una calculadora abierta "
            "de pre-dimensionamiento y evaluación financiera, hecha para que un "
            "comprador industrial llegue a la mesa sabiendo qué pedir y cómo "
            "comparar. No sustituye ingeniería de detalle, ni un Energy Yield "
            "Assessment de Ingeniero Independiente, ni la revisión legal de un "
            "contrato. Su propósito es cerrar la brecha de información entre quien "
            "vende energía solar y quien la compra."
        )
