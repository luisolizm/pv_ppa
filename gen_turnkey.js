const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, ImageRun, PageBreak,
  LevelFormat, UnderlineType
} = require('docx');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync('/tmp/word_data.json', 'utf8'));
const D = data;

// ── Helpers ──────────────────────────────────────────────────────────────────
const W = 9360; // content width DXA (US Letter 1" margins)
const DARK  = "1E2230";
const AMBER = "F59E0B";
const TEAL  = "14B8A6";
const GREY  = "64748B";
const WHITE = "F1F5F9";
const GREEN = "4ADE80";
const RED   = "F87171";

const border = { style: BorderStyle.SINGLE, size: 1, color: "D1D5DB" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function ph(text, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before ?? 80, after: opts.after ?? 80 },
    alignment: opts.align ?? AlignmentType.LEFT,
    children: [new TextRun({
      text,
      font: "Arial",
      size: opts.size ?? 20,
      bold: opts.bold ?? false,
      color: opts.color ?? "1F2937",
      italics: opts.italic ?? false,
    })]
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: AMBER, space: 4 } },
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: "111827" })]
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: "Arial", size: 22, bold: true, color: "1F2937" })]
  });
}

function spacer(lines = 1) {
  return Array.from({ length: lines }, () => new Paragraph({ children: [new TextRun("")] }));
}

function placeholder(label) {
  return new TextRun({ text: `[${label}]`, font: "Arial", size: 20, color: "9CA3AF", italics: true });
}

function kpiTable(items) {
  // items: [{label, value, sub}]
  const n = items.length;
  const cw = Math.floor(W / n);
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: items.map(() => cw),
    rows: [new TableRow({
      children: items.map(it => new TableCell({
        borders,
        width: { size: cw, type: WidthType.DXA },
        shading: { fill: "F8FAFC", type: ShadingType.CLEAR },
        margins: cellMargins,
        verticalAlign: VerticalAlign.CENTER,
        children: [
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 20 },
            children: [new TextRun({ text: it.value, font: "Arial", size: 28, bold: true, color: AMBER })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 20 },
            children: [new TextRun({ text: it.label, font: "Arial", size: 16, color: GREY })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
            children: [new TextRun({ text: it.sub ?? "", font: "Arial", size: 14, color: "9CA3AF" })] }),
        ]
      }))
    })]
  });
}

function dataTable(headers, rows, colWidths) {
  const hdrRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: "1F2937", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, font: "Arial", size: 18, bold: true, color: WHITE })] })]
    }))
  });
  const dataRows = rows.map((row, ri) => new TableRow({
    children: row.map((cell, ci) => new TableCell({
      borders,
      width: { size: colWidths[ci], type: WidthType.DXA },
      shading: { fill: ri % 2 === 0 ? "F9FAFB" : "F1F5F9", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [new Paragraph({ alignment: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        children: [new TextRun({ text: String(cell), font: "Arial", size: 18, color: "1F2937" })] })]
    }))
  }));
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [hdrRow, ...dataRows]
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

// ── Escenarios Turnkey ────────────────────────────────────────────────────────
const esc = D.escenarios;
const escHeaders = ["Escenario", "Supuestos clave", "TIR", "VPN (MXN)", "Payback simple", "LCOE (MXN/kWh)"];
const escWidths  = [1200, 2800, 900, 1500, 1460, 1500];
const escRows = [
  ["✅ Best Case", esc.best.nota,   esc.best.tir,  esc.best.vpn,  esc.best.pb,  esc.best.lcoe],
  ["📊 Base Case", esc.base.nota,   esc.base.tir,  esc.base.vpn,  esc.base.pb,  esc.base.lcoe],
  ["⚠️ Worst Case", esc.worst.nota, esc.worst.tir, esc.worst.vpn, esc.worst.pb, esc.worst.lcoe],
];

// ── CAPEX table ───────────────────────────────────────────────────────────────
const capexHeaders = ["Rubro", "% referencia", "Monto (MXN)"];
const capexWidths  = [3600, 2000, 3760];
const capexRows = [
  ["Paneles fotovoltaicos + Inversores", "~55%", ""],
  ["Instalación + Estructura + Montaje", "~25%", ""],
  ["Trámites + Interconexión CFE + UVIE", "~10%", ""],
  ["Margen + Ingeniería + Contingencia", "~10%", ""],
  ["TOTAL CAPEX", `$${D.inversion_usd.toLocaleString('es-MX')} USD / $${D.inversion_mxn.toLocaleString('es-MX')} MXN`, "Por confirmar con cotización"],
];

// ── Build document ────────────────────────────────────────────────────────────
const children = [
  // ── PORTADA ─────────────────────────────────────────────────────────────────
  ...(logoRun ? [new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 0, after: 280 },
    children: [logoRun] })] : []),
  new Paragraph({ spacing: { before: 480, after: 120 },
    children: [new TextRun({ text: "CASO DE NEGOCIO – VERSIÓN INTERNA", font: "Arial", size: 36, bold: true, color: "111827" })] }),
  new Paragraph({ spacing: { before: 0, after: 80 },
    children: [new TextRun({ text: "Proyecto de Autoconsumo Solar Fotovoltaico", font: "Arial", size: 26, color: GREY })] }),
  new Paragraph({ spacing: { before: 80, after: 40 },
    children: [placeholder("Nombre del Cliente / Proyecto")] }),
  ...spacer(1),
  new Paragraph({ spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: `Fecha: ${D.fecha}`, font: "Arial", size: 20, color: GREY }),
               new TextRun({ text: "   |   ", font: "Arial", size: 20, color: "D1D5DB" }),
               new TextRun({ text: "Versión: Confidencial – Uso Interno", font: "Arial", size: 20, color: GREY, italics: true })] }),
  new Paragraph({ spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: "Preparado por: ", font: "Arial", size: 20, color: GREY }),
               placeholder("Tu Empresa")] }),
  new Paragraph({ spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: `Ubicación: ${D.ubicacion}`, font: "Arial", size: 20, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 1. RESUMEN EJECUTIVO ────────────────────────────────────────────────────
  heading1("1. Resumen Ejecutivo"),
  kpiTable([
    { label: "Capacidad propuesta", value: `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : D.kwp.toFixed(1)+' kWp'}`, sub: `${D.n_panels.toLocaleString()} paneles` },
    { label: "CAPEX total ref.", value: `$${(D.inversion_mxn/1e6).toFixed(2)}M`, sub: "MXN" },
    { label: "Ahorro año 1", value: `$${(D.ahorro1/1e6).toFixed(2)}M`, sub: "MXN" },
    { label: "Payback simple", value: D.pb_simple ?? `>${D.vida_util}a`, sub: "años" },
  ]),
  ...spacer(1),
  kpiTable([
    { label: "TIR equity", value: D.tir_str, sub: `vs ${D.wacc}% WACC` },
    { label: "VPN", value: `$${(D.vpn/1e6).toFixed(2)}M`, sub: "MXN" },
    { label: "LCOE", value: `$${D.lcoe.toFixed(2)}`, sub: "MXN/kWh" },
    { label: "Payback descontado", value: D.pb_disc ?? `>${D.vida_util}a`, sub: "años" },
  ]),
  ...spacer(1),
  ph(`Recomendación: ${D.vpn > 0 ? "✅ GO – Proyecto atractivo con VPN positivo y TIR sobre el WACC." : "⚠️ REVISAR – VPN negativo. Analizar reducción de CAPEX o mejora de condiciones."}`,
     { bold: true, size: 20 }),
  ph("Objetivo: Desarrollar e instalar un sistema de autoconsumo solar interconectado bajo esquema Net Billing / Generación Distribuida para reducir el costo energético del cliente durante los próximos 25 años.",
     { color: GREY }),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 2. DESCRIPCIÓN DEL PROYECTO ─────────────────────────────────────────────
  heading1("2. Descripción del Proyecto"),
  dataTable(
    ["Parámetro", "Valor"],
    [
      ["Modalidad", "Autoconsumo Interconectado (Net Billing) – Generación Distribuida"],
      ["Ubicación", D.ubicacion],
      ["Coordenadas", `${D.lat.toFixed(4)}°N, ${D.lon.toFixed(4)}°W`],
      ["Consumo anual estimado", `${(D.consumo_anual/1000).toFixed(1)} MWh/año`],
      ["Cobertura esperada", `${D.cobertura_pct.toFixed(1)}%`],
      ["Capacidad instalada", `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : D.kwp.toFixed(1)+' kWp'} / ${D.n_panels.toLocaleString()} paneles`],
      ["Área requerida (estimada)", `${D.area_usada.toFixed(0)} m² netos`],
      ["Vida útil del proyecto", `${D.vida_util} años`],
      ["Etapa actual", "[Diseño / Estudio de viabilidad / Permisos en trámite]"],
    ],
    [3600, 5760]
  ),
  ...spacer(2),

  // ── 3. ANÁLISIS TÉCNICO ─────────────────────────────────────────────────────
  heading1("3. Análisis Técnico"),
  heading2("3.1 Recurso Solar"),
  dataTable(
    ["Parámetro", "Valor", "Fuente"],
    [
      ["Irradiancia promedio anual (HSP)", `${D.hsp.toFixed(2)} kWh/m²/día`, "NASA POWER 2005-2024"],
      ["Generación estimada P50", `${(D.gen_p50/1000).toFixed(1)} MWh/año`, "Irradiancia media climatológica"],
      ["Generación estimada P90", D.gen_p90 ? `${(D.gen_p90/1000).toFixed(1)} MWh/año` : "No disponible – cargar NASA", "Serie histórica 20 años"],
      ["Performance Ratio (PR)", `${D.pr_pct.toFixed(1)}%`, "Configurado por usuario"],
      ["Degradación anual paneles", `${D.degradacion}%/año`, "Datasheet fabricante"],
      ["Base del modelo financiero", D.gen_p90 ? "P90 (conservador)" : "P50 (media)", ""],
    ],
    [3200, 3560, 2600]
  ),
  ...spacer(1),
  heading2("3.2 Panel de referencia"),
  dataTable(
    ["Parámetro", "Valor"],
    [
      ["Potencia pico (Pmax)", `${D.panel_wp} Wp`],
      ["Eficiencia", `${D.panel_eff.toFixed(1)}%`],
      ["Dimensiones", `${D.panel_largo}×${D.panel_ancho} mm`],
      ["Peso por panel", `${D.panel_peso} kg`],
      ["Carga estructural total (×1.35)", `${(D.n_panels * D.panel_peso * 1.35).toFixed(0)} kg`],
    ],
    [4680, 4680]
  ),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 4. SUPUESTOS FINANCIEROS ────────────────────────────────────────────────
  heading1("4. Supuestos Financieros"),
  heading2("4.1 CAPEX (llenar con cotización real del proveedor)"),
  dataTable(capexHeaders, capexRows, capexWidths),
  ...spacer(1),
  heading2("4.2 Parámetros del modelo"),
  dataTable(
    ["Supuesto", "Valor"],
    [
      ["OPEX anual (O&M)", `${D.om_pct}% del CAPEX MXN`],
      ["Tarifa CFE actual", `$${D.tarifa_efectiva.toFixed(3)}/kWh MXN`],
      ["Inflación tarifaria CFE proyectada", `${D.inflacion_cfe}%/año`],
      ["Tipo de cambio", `$${D.usd_to_mxn.toFixed(2)} MXN/USD`],
      ["Tasa de descuento (WACC)", `${D.wacc}%`],
      ["Horizonte de análisis", `${D.vida_util} años`],
      ["Costo/kWp referencia (llave en mano)", `$${D.costo_kwp.toFixed(0)} USD/kWp`],
    ],
    [4680, 4680]
  ),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 5. RESULTADOS FINANCIEROS ───────────────────────────────────────────────
  heading1("5. Resultados Financieros"),
  heading2("5.1 Métricas Base Case"),
  dataTable(
    ["Métrica", "Valor", "Comentario"],
    [
      ["TIR equity", esc.base.tir, `vs WACC ${D.wacc}%`],
      ["VPN", esc.base.vpn, "a tasa de descuento configurada"],
      ["Payback simple", esc.base.pb, "nominal sin descontar"],
      ["Payback descontado", esc.base.pb_disc, `a WACC ${D.wacc}%`],
      ["LCOE", esc.base.lcoe, "costo nivelado de energía"],
      ["Ahorro año 1", `$${(D.ahorro1/1e6).toFixed(2)}M MXN`, "sobre autoconsumo estimado"],
      ["CO₂ evitado año 1", `${D.co2_t.toFixed(1)} ton/año`, `Factor SEN 2024: ${D.co2_factor} kg CO₂e/kWh`],
    ],
    [2800, 2560, 4000]
  ),
  ...spacer(1),
  heading2("5.2 Análisis de escenarios"),
  ph("Variables de sensibilidad: CAPEX (±10–15%), Inflación CFE (±2–3 pts), Generación P50/P90, WACC (±2 pts).",
     { color: GREY, size: 18 }),
  ...spacer(1),
  dataTable(escHeaders, escRows, escWidths),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 6. CONSIDERACIONES ──────────────────────────────────────────────────────
  heading1("6. Consideraciones y Próximos Pasos"),
  ph("• Los valores son estimados de pre-sizing (±15%). La ingeniería detallada y simulación definitiva (PVSyst/Helioscope) son responsabilidad del proveedor EPC.", { color: GREY }),
  ph("• Se requiere visita técnica al sitio para validar área disponible, orientación, inclinación, sombras y condición de la red eléctrica interna.", { color: GREY }),
  ph("• Trámite de interconexión CFE (Pequeña Escala o Generación Distribuida) puede tomar 2–6 meses dependiendo de la zona y capacidad.", { color: GREY }),
  ph("• El CAPEX deberá confirmarse con cotizaciones formales de al menos 2 proveedores EPC certificados.", { color: GREY }),
  ph("• Se recomienda solicitar dictamen UVIE (NOM-001-SEDE) y garantía EPC mínimo 2 años post-comisionamiento.", { color: GREY }),
  ...spacer(2),
  ph("Preparado con Sizing Tool — Pre-sizing fotovoltaico · Uso interno · Confidencial",
     { color: "D1D5DB", size: 16, italic: true, align: AlignmentType.CENTER }),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: "111827" },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: "1F2937" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: AMBER, space: 4 } },
            spacing: { before: 0, after: 100 },
            children: [
              ...(logoRun ? [logoRun, new TextRun({ text: "   ", font: "Arial", size: 20 })] : []),
              new TextRun({ text: "Caso de Negocio Solar · ", font: "Arial", size: 18, color: GREY }),
              new TextRun({ text: D.ubicacion, font: "Arial", size: 18, color: GREY, italics: true }),
              new TextRun({ text: "   Pág. ", font: "Arial", size: 16, color: "9CA3AF" }),
            ]
          })
        ]
      })
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/tmp/word_output.docx', buf);
  console.log('OK');
});
