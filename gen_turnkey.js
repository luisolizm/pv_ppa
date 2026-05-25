const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, ImageRun, PageBreak,
  LevelFormat, UnderlineType
} = require('docx');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync(process.env.WORD_DATA || '/tmp/word_data.json', 'utf8'));
const D = data;

// ── Constantes de layout ──────────────────────────────────────────────────────
const W      = 9360;  // ancho contenido US Letter 1" márgenes (DXA)
const AMBER  = "F59E0B";
const TEAL   = "14B8A6";
const GREY   = "64748B";
const DARK   = "111827";
const MID    = "374151";
const LIGHT  = "6B7280";
const WHITE  = "F1F5F9";
const GREEN  = "166534";
const GREEN2 = "4ADE80";
const RED2   = "F87171";
const BGCARD = "F8FAFC";
const BGGREY = "F3F4F6";

// ── Borders ──────────────────────────────────────────────────────────────────
const border   = { style: BorderStyle.SINGLE, size: 1, color: "D1D5DB" };
const borders  = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders= { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const cellMar  = { top: 100, bottom: 100, left: 140, right: 140 };
const cellMarS = { top: 60,  bottom: 60,  left: 120, right: 120 };

// ── Helpers de párrafo ────────────────────────────────────────────────────────
function ph(text, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before ?? 60, after: opts.after ?? 60 },
    alignment: opts.align ?? AlignmentType.LEFT,
    children: [new TextRun({
      text, font: "Arial", size: opts.size ?? 20,
      bold: opts.bold ?? false, color: opts.color ?? MID,
      italics: opts.italic ?? false,
    })]
  });
}

function phRuns(runs, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before ?? 60, after: opts.after ?? 60 },
    alignment: opts.align ?? AlignmentType.LEFT,
    children: runs,
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 280, after: 140 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: AMBER, space: 4 } },
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: DARK })]
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 180, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 22, bold: true, color: MID })]
  });
}

function spacer(lines = 1) {
  return Array.from({ length: lines }, () =>
    new Paragraph({ spacing: { before: 0, after: 0 }, children: [new TextRun({ text: "" })] })
  );
}

function placeholder(label) {
  return new TextRun({ text: `[${label}]`, font: "Arial", size: 20, color: "9CA3AF", italics: true });
}

// bullet nativo Word (sin unicode •)
function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: "Arial", size: opts.size ?? 19, color: opts.color ?? MID })]
  });
}

// ── Tablas de datos ───────────────────────────────────────────────────────────
function dataTable(headers, rows, colWidths, opts = {}) {
  const hdrFill = opts.hdrFill ?? "1F2937";
  const hdrRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders, width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: hdrFill, type: ShadingType.CLEAR },
      margins: cellMar,
      children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, font: "Arial", size: 18, bold: true, color: WHITE })] })]
    }))
  });
  const dataRows = rows.map((row, ri) => new TableRow({
    children: row.map((cell, ci) => new TableCell({
      borders, width: { size: colWidths[ci], type: WidthType.DXA },
      shading: { fill: ri % 2 === 0 ? BGCARD : BGGREY, type: ShadingType.CLEAR },
      margins: cellMar,
      children: [new Paragraph({
        alignment: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        children: [new TextRun({ text: String(cell ?? "—"), font: "Arial", size: 18, color: DARK })]
      })]
    }))
  }));
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: colWidths, rows: [hdrRow, ...dataRows] });
}

// ── KPI cards ────────────────────────────────────────────────────────────────
function kpiTable(items) {
  const n  = items.length;
  const cw = Math.floor(W / n);
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: items.map(() => cw),
    rows: [new TableRow({ children: items.map(it => new TableCell({
      borders, width: { size: cw, type: WidthType.DXA },
      shading: { fill: BGCARD, type: ShadingType.CLEAR },
      margins: cellMar, verticalAlign: VerticalAlign.CENTER,
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 16 },
          children: [new TextRun({ text: it.value, font: "Arial", size: 28, bold: true, color: AMBER })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 12 },
          children: [new TextRun({ text: it.label, font: "Arial", size: 16, color: GREY })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
          children: [new TextRun({ text: it.sub ?? "", font: "Arial", size: 13, color: "9CA3AF" })] }),
      ]
    })) })]
  });
}

// ── Tabla dos columnas para portada ──────────────────────────────────────────
function coverInfoTable(leftItems, rightImageB64, rightImageW, rightImageH) {
  const leftW  = Math.floor(W * 0.54);
  const rightW = W - leftW;

  // columna izquierda: filas de dato
  const leftChildren = leftItems.map(([label, value, color]) =>
    new Paragraph({
      spacing: { before: 44, after: 44 },
      children: [
        new TextRun({ text: `${label}: `, font: "Arial", size: 18, color: GREY }),
        new TextRun({ text: value, font: "Arial", size: 18, bold: true, color: color ?? DARK }),
      ]
    })
  );

  // columna derecha: imagen o placeholder
  const rightChildren = rightImageB64
    ? [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 20, after: 20 },
        children: [new ImageRun({
          data: Buffer.from(rightImageB64, 'base64'),
          transformation: { width: rightImageW, height: rightImageH },
          type: 'png',
        })]
      })]
    : [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: `📍 ${D.lat.toFixed(4)}°N, ${D.lon.toFixed(4)}°W`,
          font: "Arial", size: 18, color: GREY })]
      })];

  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [leftW, rightW],
    rows: [new TableRow({ children: [
      new TableCell({
        borders: noBorders, width: { size: leftW, type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 0, right: 120 },
        verticalAlign: VerticalAlign.TOP,
        children: leftChildren,
      }),
      new TableCell({
        borders: { top: noBorder, bottom: noBorder, right: noBorder,
          left: { style: BorderStyle.SINGLE, size: 2, color: "E5E7EB" } },
        width: { size: rightW, type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 120, right: 0 },
        verticalAlign: VerticalAlign.CENTER,
        children: rightChildren,
      }),
    ]})]
  });
}

// ── Imagen de gráfica ─────────────────────────────────────────────────────────
function chartImg(b64, widthPx, heightPx) {
  if (!b64) return null;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    children: [new ImageRun({
      data: Buffer.from(b64, 'base64'),
      transformation: { width: widthPx, height: heightPx },
      type: 'png',
    })]
  });
}

// ── Logo ──────────────────────────────────────────────────────────────────────
let logoRun = null;
if (D.logo_b64) {
  logoRun = new ImageRun({
    data: Buffer.from(D.logo_b64, 'base64'),
    transformation: { width: 160, height: 50 },
    type: 'png',
  });
}

// ── Escenarios ────────────────────────────────────────────────────────────────
const esc = D.escenarios;
const escHeaders = ["Escenario", "Supuestos clave", "TIR", "VPN (MXN)", "Payback", "LCOE"];
const escWidths  = [1100, 2960, 900, 1440, 1160, 1800];
const escRows = [
  ["✅ Optimista", esc.best.nota,  esc.best.tir,  esc.best.vpn,  esc.best.pb,  esc.best.lcoe],
  ["📊 Base",      esc.base.nota,  esc.base.tir,  esc.base.vpn,  esc.base.pb,  esc.base.lcoe],
  ["⚠️ Conservador", esc.worst.nota, esc.worst.tir, esc.worst.vpn, esc.worst.pb, esc.worst.lcoe],
];

// ── CAPEX ─────────────────────────────────────────────────────────────────────
const capexRows = [
  ["Paneles fotovoltaicos + Inversores",    "~55%", ""],
  ["Instalación + Estructura + Montaje",    "~25%", ""],
  ["Trámites + Interconexión CFE + UVIE",  "~10%", ""],
  ["Margen + Ingeniería + Contingencia",    "~10%", ""],
  ["TOTAL CAPEX",
   `$${Number(D.inversion_usd).toLocaleString('es-MX')} USD / $${Number(D.inversion_mxn).toLocaleString('es-MX')} MXN`,
   "Confirmar con cotización"],
];

// ── Alerta datos faltantes ────────────────────────────────────────────────────
const alertas = [];
if (!D.consumo_anual || D.consumo_anual <= 0)
  alertas.push("⚠️  Consumo anual no ingresado — la cobertura muestra 0%. Ingresar recibos CFE para un análisis completo.");
if (!D.gen_p90)
  alertas.push("ℹ️  P90 no disponible. Se usó P50 como base. Para mayor rigor, cargar datos NASA POWER en el sidebar.");

// ── Recomendación GO/NO GO ────────────────────────────────────────────────────
const isGo = D.vpn > 0;
const recoText = isGo
  ? "✅  GO — Proyecto atractivo: VPN positivo y TIR superior al WACC. Se recomienda proceder con ingeniería de detalle."
  : "⚠️  REVISAR — VPN negativo. Analizar reducción de CAPEX, mejora de tarifa o condiciones de financiamiento.";
const recoColor = isGo ? "14532D" : "7F1D1D";
const recoBg    = isGo ? "DCFCE7" : "FEE2E2";

// ── Construir documento ───────────────────────────────────────────────────────
const children = [

  // ══════════════════════════════════════════════════════════════════
  // PORTADA
  // ══════════════════════════════════════════════════════════════════
  ...(logoRun ? [new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 0, after: 200 },
    children: [logoRun],
  })] : []),

  // Título
  new Paragraph({
    spacing: { before: 60, after: 80 },
    children: [new TextRun({ text: "CASO DE NEGOCIO", font: "Arial", size: 42, bold: true, color: DARK })],
  }),
  new Paragraph({
    spacing: { before: 0, after: 60 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: AMBER, space: 6 } },
    children: [new TextRun({ text: "Proyecto de Autoconsumo Solar Fotovoltaico", font: "Arial", size: 24, color: GREY })],
  }),
  ...spacer(1),

  // Meta del documento
  phRuns([
    new TextRun({ text: "Cliente / Proyecto: ", font: "Arial", size: 19, color: GREY }),
    placeholder("Nombre del Cliente / Proyecto"),
  ], { before: 60, after: 40 }),
  phRuns([
    new TextRun({ text: `Fecha: ${D.fecha}`, font: "Arial", size: 19, color: GREY }),
    new TextRun({ text: "   ·   ", font: "Arial", size: 19, color: "D1D5DB" }),
    new TextRun({ text: "Confidencial – Uso Interno", font: "Arial", size: 19, color: GREY, italics: true }),
    new TextRun({ text: "   ·   Elaborado por: ", font: "Arial", size: 19, color: GREY }),
    placeholder("Tu Empresa"),
  ], { before: 0, after: 100 }),

  // Tabla: resumen rápido izquierda | mapa derecha
  coverInfoTable(
    [
      ["Ubicación",   D.ubicacion,                                         DARK],
      ["Coordenadas", `${Number(D.lat).toFixed(4)}°N, ${Number(D.lon).toFixed(4)}°W`, GREY],
      ["Capacidad",   `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : Number(D.kwp).toFixed(1)+' kWp'} · ${D.n_panels} paneles`, DARK],
      ["CAPEX ref.",  `$${(Number(D.inversion_mxn)/1e6).toFixed(2)}M MXN · $${Number(D.inversion_usd).toLocaleString('es-MX')} USD`, DARK],
      ["Generación P50", `${(Number(D.gen_p50)/1000).toFixed(1)} MWh/año`, DARK],
      ["TIR / Payback", `${D.tir_str}  ·  ${D.pb_simple ?? '>'+D.vida_util}a simple`, AMBER],
      ["Vida útil",   `${D.vida_util} años`,                              GREY],
      ["Fuente irr.", "NASA POWER 2005–2024",                             GREY],
    ],
    D.map_b64 ?? null,
    220, 148
  ),
  ...spacer(1),

  // Recomendación GO/NO GO en portada
  new Paragraph({
    spacing: { before: 80, after: 0 },
    shading: { fill: recoBg, type: ShadingType.CLEAR },
    border: {
      left: { style: BorderStyle.SINGLE, size: 18, color: isGo ? "16A34A" : "DC2626", space: 8 },
    },
    children: [new TextRun({ text: "  " + recoText, font: "Arial", size: 19, bold: true, color: recoColor })],
  }),

  // Alertas de datos faltantes (si hay)
  ...alertas.map(msg => new Paragraph({
    spacing: { before: 60, after: 0 },
    shading: { fill: "FFFBEB", type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: "F59E0B", space: 8 } },
    children: [new TextRun({ text: "  " + msg, font: "Arial", size: 17, color: "92400E", italics: true })],
  })),

  new Paragraph({ children: [new PageBreak()] }),

  // ══════════════════════════════════════════════════════════════════
  // 1. RESUMEN EJECUTIVO
  // ══════════════════════════════════════════════════════════════════
  heading1("1. Resumen Ejecutivo"),
  kpiTable([
    { label: "Capacidad propuesta",  value: `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : Number(D.kwp).toFixed(1)+' kWp'}`, sub: `${D.n_panels} paneles` },
    { label: "CAPEX total ref.",     value: `$${(Number(D.inversion_mxn)/1e6).toFixed(2)}M`,  sub: "MXN" },
    { label: "Ahorro año 1",         value: `$${(Number(D.ahorro1)/1e6).toFixed(2)}M`,         sub: "MXN" },
    { label: "Payback simple",       value: D.pb_simple ? `${D.pb_simple}a` : `>${D.vida_util}a`, sub: "nominal" },
  ]),
  ...spacer(1),
  kpiTable([
    { label: "TIR equity",           value: D.tir_str,                                          sub: `vs ${D.wacc}% WACC` },
    { label: "VPN",                  value: `$${(Number(D.vpn)/1e6).toFixed(2)}M`,              sub: "MXN" },
    { label: "LCOE",                 value: `$${Number(D.lcoe).toFixed(2)}`,                    sub: "MXN/kWh" },
    { label: "Payback descontado",   value: D.pb_disc ? `${D.pb_disc}a` : `>${D.vida_util}a`,  sub: `WACC ${D.wacc}%` },
  ]),
  ...spacer(1),

  // Objetivo del proyecto
  ph("Objetivo del proyecto:", { bold: true, size: 19, color: DARK, before: 80, after: 30 }),
  ph("Desarrollar e instalar un sistema fotovoltaico de autoconsumo interconectado bajo esquema Net Billing / Generación Distribuida para reducir el costo energético del cliente a lo largo de los próximos 25 años, con retorno de inversión comprobable y riesgo acotado por el análisis de escenarios.",
     { color: LIGHT, size: 18, before: 0, after: 80 }),

  // ── Gráfica de generación mensual ─────────────────────────────────
  ...(D.chart_b64 ? [
    heading2("Generación mensual estimada"),
    ph("Barras: energía generada por mes (MWh). Línea: irradiancia global horizontal NASA POWER (kWh/m²/día).",
       { color: LIGHT, size: 17, italic: true, before: 0, after: 60 }),
    chartImg(D.chart_b64, 580, 205),
  ] : []),

  // ── Gráfica generación vs consumo (solo si hay datos de recibo) ────
  ...(D.coverage_b64 ? [
    heading2("Generación vs Consumo Mensual"),
    ph("Ámbar: energía solar cubierta. Gris: consumo complementado por CFE. Línea punteada: generación total del sistema.",
       { color: LIGHT, size: 17, italic: true, before: 0, after: 60 }),
    chartImg(D.coverage_b64, 580, 215),
  ] : []),

  new Paragraph({ children: [new PageBreak()] }),

  // ══════════════════════════════════════════════════════════════════
  // 2. DESCRIPCIÓN DEL PROYECTO
  // ══════════════════════════════════════════════════════════════════
  heading1("2. Descripción del Proyecto"),
  dataTable(
    ["Parámetro", "Valor"],
    [
      ["Modalidad",                  "Autoconsumo Interconectado (Net Billing) – Generación Distribuida"],
      ["Ubicación",                  D.ubicacion],
      ["Coordenadas GPS",            `${Number(D.lat).toFixed(4)}°N, ${Number(D.lon).toFixed(4)}°W`],
      ["Consumo anual estimado",     D.consumo_anual > 0 ? `${(D.consumo_anual/1000).toFixed(1)} MWh/año` : "Pendiente — ingresar recibos CFE"],
      ["Cobertura esperada",         D.consumo_anual > 0 ? `${Number(D.cobertura_pct).toFixed(1)}%` : "N/D"],
      ["Capacidad instalada",        `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : Number(D.kwp).toFixed(1)+' kWp'} / ${D.n_panels} paneles`],
      ["Área neta estimada",         `${Number(D.area_usada).toFixed(0)} m²`],
      ["Vida útil del proyecto",     `${D.vida_util} años`],
      ["Etapa actual",               "[Diseño / Estudio de viabilidad / Permisos en trámite]"],
    ],
    [3600, 5760]
  ),
  ...spacer(1),

  // ══════════════════════════════════════════════════════════════════
  // 3. ANÁLISIS TÉCNICO (mismo página que sección 2)
  // ══════════════════════════════════════════════════════════════════
  heading1("3. Análisis Técnico"),
  heading2("3.1 Recurso Solar"),
  dataTable(
    ["Parámetro", "Valor", "Fuente"],
    [
      ["Irradiancia promedio anual (HSP)",  `${Number(D.hsp).toFixed(2)} kWh/m²/día`,  "NASA POWER 2005–2024"],
      ["Generación estimada P50",           `${(Number(D.gen_p50)/1000).toFixed(1)} MWh/año`, "Irradiancia media climatológica"],
      ["Generación estimada P90",           D.gen_p90 ? `${(D.gen_p90/1000).toFixed(1)} MWh/año` : "Cargar datos NASA en sidebar", "Serie histórica 20 años"],
      ["Performance Ratio (PR)",            `${Number(D.pr_pct).toFixed(1)}%`,          "Configurado por usuario"],
      ["Degradación anual de paneles",      `${D.degradacion}%/año`,                   "Datasheet fabricante"],
      ["Base del modelo financiero",        D.gen_p90 ? "P90 (conservador)" : "P50 (media)", ""],
    ],
    [3200, 3360, 2800]
  ),
  ...spacer(1),

  heading2("3.2 Panel de referencia"),
  dataTable(
    ["Parámetro", "Valor"],
    [
      ["Potencia pico (Pmax)",              `${D.panel_wp} Wp`],
      ["Eficiencia",                        `${Number(D.panel_eff).toFixed(1)}%`],
      ["Dimensiones",                       `${D.panel_largo} × ${D.panel_ancho} mm`],
      ["Peso por panel",                    `${D.panel_peso} kg`],
      ["Carga estructural total (×1.35)",   `${(D.n_panels * D.panel_peso * 1.35).toFixed(0)} kg`],
    ],
    [4680, 4680]
  ),

  new Paragraph({ children: [new PageBreak()] }),

  // ══════════════════════════════════════════════════════════════════
  // 4. SUPUESTOS FINANCIEROS
  // ══════════════════════════════════════════════════════════════════
  heading1("4. Supuestos Financieros"),
  heading2("4.1 CAPEX — confirmar con cotización real del proveedor"),
  dataTable(
    ["Rubro", "% referencia", "Monto estimado"],
    capexRows,
    [3600, 1800, 3960]
  ),
  ...spacer(1),

  heading2("4.2 Parámetros del modelo financiero"),
  dataTable(
    ["Supuesto", "Valor"],
    [
      ["OPEX anual (O&M)",                      `${D.om_pct}% del CAPEX MXN`],
      ["Tarifa CFE actual (efectiva)",           `$${Number(D.tarifa_efectiva).toFixed(3)}/kWh MXN`],
      ["Inflación tarifaria CFE proyectada",     `${D.inflacion_cfe}%/año`],
      ["Tipo de cambio referencia",              `$${Number(D.usd_to_mxn).toFixed(2)} MXN/USD`],
      ["Tasa de descuento (WACC)",              `${D.wacc}%`],
      ["Horizonte de análisis",                 `${D.vida_util} años`],
      ["Costo/kWp referencia (llave en mano)",  `$${Number(D.costo_kwp).toFixed(0)} USD/kWp`],
    ],
    [4680, 4680]
  ),

  new Paragraph({ children: [new PageBreak()] }),

  // ══════════════════════════════════════════════════════════════════
  // 5. RESULTADOS FINANCIEROS
  // ══════════════════════════════════════════════════════════════════
  heading1("5. Resultados Financieros"),
  heading2("5.1 Métricas — Caso Base"),
  dataTable(
    ["Métrica", "Valor", "Interpretación"],
    [
      ["TIR equity",         esc.base.tir,                           `vs WACC ${D.wacc}% — ${D.vpn > 0 ? "por encima del hurdle" : "por debajo del hurdle"}`],
      ["VPN",                esc.base.vpn,                           "Valor creado a la tasa de descuento configurada"],
      ["Payback simple",     esc.base.pb,                            "Nominal, sin descontar flujos"],
      ["Payback descontado", esc.base.pb_disc,                       `A WACC ${D.wacc}%`],
      ["LCOE",               esc.base.lcoe,                          "Costo nivelado de energía generada"],
      ["Ahorro año 1",       `$${(Number(D.ahorro1)/1e6).toFixed(2)}M MXN`, "Sobre autoconsumo estimado"],
      ["CO₂ evitado año 1",  `${Number(D.co2_t).toFixed(1)} ton/año`, `Factor SEN 2024: ${D.co2_factor} kg CO₂e/kWh`],
    ],
    [2600, 2200, 4560]
  ),
  ...spacer(1),

  heading2("5.2 Análisis de sensibilidad — tres escenarios"),
  ph("Variables: CAPEX (±10–15%), Inflación CFE (±2–3 pts), Generación P50/P90. En todos los escenarios el VPN permanece positivo.",
     { color: LIGHT, size: 17, italic: true, before: 0, after: 80 }),
  dataTable(escHeaders, escRows, escWidths),

  new Paragraph({ children: [new PageBreak()] }),

  // ══════════════════════════════════════════════════════════════════
  // 6. CONSIDERACIONES Y PRÓXIMOS PASOS
  // ══════════════════════════════════════════════════════════════════
  heading1("6. Consideraciones y Próximos Pasos"),

  heading2("6.1 Limitaciones del pre-sizing"),
  bullet("Los valores son estimados de pre-sizing (±15%). No sustituyen la ingeniería de detalle ni la simulación con software especializado (PVSyst, Helioscope)."),
  bullet(`El P90 se calcula como percentil 10 de la distribución de generaciones anuales usando ${D.gen_p90 ? '20' : 'N/D'} años de irradiancia real NASA POWER (2005–2024).`),
  bullet("El CAPEX deberá confirmarse con cotizaciones formales de al menos 2 proveedores EPC certificados."),

  ...spacer(1),
  heading2("6.2 Próximos pasos recomendados"),
  bullet("Visita técnica al sitio: validar área disponible, orientación, inclinación óptima, análisis de sombras y condición de la red eléctrica interna."),
  bullet("Ingeniería de detalle: solicitar simulación PVSyst / Helioscope con P50 y P90, análisis de sombras 3D y desglose de pérdidas."),
  bullet("Interconexión CFE: gestionar solicitud de interconexión (Pequeña Escala o GD). Tiempo estimado: 2–6 meses según zona y capacidad."),
  bullet("Dictamen UVIE (NOM-001-SEDE): requerido para contratar con CFE en la mayoría de los estados."),
  bullet("Garantía EPC: solicitar mínimo 2 años post-comisionamiento; financiamientos bancarios exigen 3 años."),
  bullet("Permiso CRE: requerido si la capacidad supera 0.5 MW."),

  ...spacer(2),
  ph("Preparado con Sizing Tool — Pre-sizing fotovoltaico · Confidencial · Uso interno",
     { color: "D1D5DB", size: 16, italic: true, align: AlignmentType.CENTER }),
];

// ── Documento final ───────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 480, hanging: 260 },
                       spacing: { before: 60, after: 60 } },
          run: { font: "Arial", size: 19, color: AMBER },
        }
      }]
    }]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: DARK },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: MID },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: AMBER, space: 4 } },
          spacing: { before: 0, after: 80 },
          children: [
            ...(logoRun ? [logoRun, new TextRun({ text: "   ", font: "Arial", size: 20 })] : []),
            new TextRun({ text: "Caso de Negocio Solar  ·  ", font: "Arial", size: 17, color: GREY }),
            new TextRun({ text: D.ubicacion, font: "Arial", size: 17, color: GREY, italics: true }),
            new TextRun({ text: "   Pág. ", font: "Arial", size: 15, color: "9CA3AF" }),
          ]
        })]
      })
    },
    children,
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.env.WORD_OUT || '/tmp/word_output.docx', buf);
  console.log('OK');
}).catch(err => {
  console.error('ERROR:', err.message);
  process.exit(1);
});
