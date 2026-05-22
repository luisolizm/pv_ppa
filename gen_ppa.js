const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, ImageRun, PageBreak,
  LevelFormat
} = require('docx');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync('/tmp/word_data.json', 'utf8'));
const D = data;

const W = 9360;
const AMBER = "F59E0B"; const TEAL = "14B8A6"; const GREY = "64748B";
const WHITE = "F1F5F9"; const GREEN = "4ADE80"; const RED = "F87171";

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
      text, font: "Arial", size: opts.size ?? 20,
      bold: opts.bold ?? false, color: opts.color ?? "1F2937",
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
function spacer(n = 1) { return Array.from({ length: n }, () => new Paragraph({ children: [new TextRun("")] })); }
function placeholder(label) {
  return new TextRun({ text: `[${label}]`, font: "Arial", size: 20, color: "9CA3AF", italics: true });
}
function kpiTable(items) {
  const n = items.length;
  const cw = Math.floor(W / n);
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: items.map(() => cw),
    rows: [new TableRow({ children: items.map(it => new TableCell({
      borders, width: { size: cw, type: WidthType.DXA },
      shading: { fill: "F8FAFC", type: ShadingType.CLEAR },
      margins: cellMargins, verticalAlign: VerticalAlign.CENTER,
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 20 },
          children: [new TextRun({ text: it.value, font: "Arial", size: 26, bold: true, color: AMBER })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 20 },
          children: [new TextRun({ text: it.label, font: "Arial", size: 16, color: GREY })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
          children: [new TextRun({ text: it.sub ?? "", font: "Arial", size: 14, color: "9CA3AF" })] }),
      ]
    })) })]
  });
}
function dataTable(headers, rows, colWidths) {
  const hdrRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders, width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: "1F2937", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, font: "Arial", size: 18, bold: true, color: WHITE })] })]
    }))
  });
  const dataRows = rows.map((row, ri) => new TableRow({
    children: row.map((cell, ci) => new TableCell({
      borders, width: { size: colWidths[ci], type: WidthType.DXA },
      shading: { fill: ri % 2 === 0 ? "F9FAFB" : "F1F5F9", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [new Paragraph({ alignment: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        children: [new TextRun({ text: String(cell), font: "Arial", size: 18, color: "1F2937" })] })]
    }))
  }));
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: colWidths, rows: [hdrRow, ...dataRows] });
}

// ── Logo ──────────────────────────────────────────────────────────────────────
let logoRun = null;
if (D.logo_b64) {
  logoRun = new ImageRun({ data: Buffer.from(D.logo_b64, 'base64'),
    transformation: { width: 160, height: 50 }, type: 'png' });
}

// ── Tabla de plazos ────────────────────────────────────────────────────────────
const plazos = D.plazos;  // [{pl, pm, ph, ph_label, precio_manual, vpn, tir, pb, pb_disc, vr, ing_total}]
const plazoCols = [2200, ...plazos.map(() => Math.floor((W - 2200) / plazos.length))];
const plazosHeaders = ["Métrica", ...plazos.map(p => `${p.pl} años`)];
const plazosRows = [
  ["Precio mínimo viable (VPN=0)", ...plazos.map(p => p.pm ? `$${p.pm.toFixed(4)}/kWh` : "No viable")],
  [`Tarifa objetivo (${D.hurdle_label})`, ...plazos.map(p => p.ph ? `$${p.ph.toFixed(4)}/kWh` : "N/A")],
  ["Tarifa ofrecida", ...plazos.map(p => `$${p.precio_manual.toFixed(4)}/kWh`)],
  ["VPN (MXN)", ...plazos.map(p => `$${(p.vpn/1e6).toFixed(2)}M`)],
  ["TIR equity", ...plazos.map(p => p.tir ? `${p.tir.toFixed(1)}%` : "N/A")],
  ["Payback simple", ...plazos.map(p => p.pb ? `${p.pb} años` : `>${p.pl}a`)],
  ["Payback descontado", ...plazos.map(p => p.pb_disc ? `${p.pb_disc} años` : `>${p.pl}a`)],
  ["Valor de rescate (MXN)", ...plazos.map(p => `$${(p.vr/1e6).toFixed(2)}M`)],
  ["Ingreso total (MXN)", ...plazos.map(p => `$${(p.ing_total/1e6).toFixed(2)}M`)],
];

// ── Escenarios sobre plazo objetivo ───────────────────────────────────────────
const esc = D.escenarios;
const escHeaders = ["Escenario", "Supuestos clave", "TIR equity", "VPN (MXN)", "Payback simple"];
const escWidths  = [1300, 3200, 1100, 1760, 2000];
const escRows = [
  ["✅ Best Case",  esc.best.nota,  esc.best.tir,  esc.best.vpn,  esc.best.pb],
  ["📊 Base Case",  esc.base.nota,  esc.base.tir,  esc.base.vpn,  esc.base.pb],
  ["⚠️ Worst Case", esc.worst.nota, esc.worst.tir, esc.worst.vpn, esc.worst.pb],
];

// ── CAPEX ─────────────────────────────────────────────────────────────────────
const capexHeaders = ["Rubro", "% referencia", "Monto (MXN)"];
const capexWidths  = [3600, 2000, 3760];
const capexRows = [
  ["Paneles fotovoltaicos + Inversores", "~55%", ""],
  ["Instalación + Estructura + Montaje", "~25%", ""],
  ["Trámites + Interconexión CFE + UVIE", "~10%", ""],
  ["Margen + Ingeniería + Contingencia", "~10%", ""],
  ["TOTAL CAPEX referencia", `$${D.inversion_usd.toLocaleString('es-MX')} USD / $${D.inversion_mxn.toLocaleString('es-MX')} MXN`, "Por confirmar con cotización"],
];

const ro = D.plazo_obj;   // resultado del plazo objetivo

const children = [
  // ── PORTADA ──────────────────────────────────────────────────────────────────
  ...(logoRun ? [new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 0, after: 280 },
    children: [logoRun] })] : []),
  new Paragraph({ spacing: { before: 480, after: 120 },
    children: [new TextRun({ text: "CASO DE NEGOCIO – VERSIÓN INTERNA", font: "Arial", size: 36, bold: true, color: "111827" })] }),
  new Paragraph({ spacing: { before: 0, after: 80 },
    children: [new TextRun({ text: "Power Purchase Agreement (PPA) – Solar Fotovoltaico", font: "Arial", size: 26, color: GREY })] }),
  new Paragraph({ spacing: { before: 80, after: 40 }, children: [placeholder("Nombre del Cliente / Proyecto")] }),
  ...spacer(1),
  new Paragraph({ spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: `Fecha: ${D.fecha}`, font: "Arial", size: 20, color: GREY }),
               new TextRun({ text: "   |   ", font: "Arial", size: 20, color: "D1D5DB" }),
               new TextRun({ text: "Confidencial – Uso Interno", font: "Arial", size: 20, color: GREY, italics: true })] }),
  new Paragraph({ spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: "Preparado por: ", font: "Arial", size: 20, color: GREY }),
               placeholder("Tu Empresa")] }),
  new Paragraph({ spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: `Ubicación: ${D.ubicacion}`, font: "Arial", size: 20, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 1. RESUMEN EJECUTIVO ─────────────────────────────────────────────────────
  heading1("1. Resumen Ejecutivo"),
  kpiTable([
    { label: "Capacidad", value: `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : D.kwp.toFixed(1)+' kWp'}`, sub: "sistema instalado" },
    { label: "CAPEX total ref.", value: `$${(D.inversion_mxn/1e6).toFixed(2)}M`, sub: "MXN" },
    { label: "Plazo análisis", value: `${ro.pl} años`, sub: "plazo objetivo" },
    { label: "VPN equity", value: `$${(ro.vpn/1e6).toFixed(2)}M`, sub: "MXN" },
  ]),
  ...spacer(1),
  kpiTable([
    { label: "TIR equity", value: ro.tir ? `${ro.tir.toFixed(1)}%` : "N/A", sub: `vs ${D.wacc}% WACC` },
    { label: "Tarifa ofrecida", value: `$${D.precio_manual.toFixed(4)}`, sub: "MXN/kWh año 1" },
    { label: `Tarifa obj. (${D.hurdle_label})`, value: ro.ph ? `$${ro.ph.toFixed(4)}` : "N/A", sub: "MXN/kWh año 1" },
    { label: "Precio mínimo (VPN=0)", value: ro.pm ? `$${ro.pm.toFixed(4)}` : "No viable", sub: "MXN/kWh año 1" },
  ]),
  ...spacer(1),
  ph(`Recomendación: ${ro.vpn > 0 && ro.tir && ro.pm && D.precio_manual >= ro.ph
      ? "✅ GO – VPN positivo, TIR sobre hurdle rate y precio ofrecido sobre tarifa objetivo."
      : ro.vpn > 0 && ro.pm && D.precio_manual >= ro.pm
      ? "🟡 VIABLE – VPN positivo y precio sobre mínimo, pero bajo el hurdle rate. Evaluar margen de negociación."
      : "⚠️ REVISAR – Precio por debajo del mínimo viable. Ajustar precio, plazo o estructura de costos."}`,
     { bold: true }),
  ph(`Hurdle rate: WACC ${D.wacc}% + spread ${D.spread}% = ${D.wacc + D.spread}%. La tarifa objetivo es el precio donde la TIR equity iguala exactamente el hurdle rate.`,
     { color: GREY }),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 2. DESCRIPCIÓN DEL PROYECTO ──────────────────────────────────────────────
  heading1("2. Descripción del Proyecto"),
  dataTable(
    ["Parámetro", "Valor"],
    [
      ["Modalidad", "Power Purchase Agreement (PPA) – Desarrollador dueño del sistema"],
      ["Ubicación", D.ubicacion],
      ["Generación base (año 1)", `${(D.gen_anual/1000).toFixed(1)} MWh/año (${D.gen_base_label})`],
      ["Capacidad instalada", `${D.kwp >= 1000 ? (D.kwp/1000).toFixed(2)+' MWp' : D.kwp.toFixed(1)+' kWp'}`],
      ["Escalador PPA anual", `${D.esc_ppa}%/año`],
      ["Degradación paneles", `${D.degradacion}%/año`],
      ["Vida útil del sistema", `${D.vida_util} años`],
      ["Etapa actual", "[Diseño / Estudio de viabilidad / Permisos en trámite]"],
    ],
    [3600, 5760]
  ),
  ...spacer(2),

  // ── 3. ANÁLISIS TÉCNICO ───────────────────────────────────────────────────────
  heading1("3. Análisis Técnico"),
  dataTable(
    ["Parámetro", "Valor", "Fuente"],
    [
      ["Irradiancia promedio anual (HSP)", `${D.hsp.toFixed(2)} kWh/m²/día`, "NASA POWER 2005-2024"],
      ["Generación año 1 (base modelo)", `${(D.gen_anual/1000).toFixed(1)} MWh/año`, D.gen_base_label],
      ["CO₂ evitado año 1", `${D.co2_t.toFixed(1)} ton/año`, `Factor ${D.co2_factor} kg CO₂e/kWh · SEN 2024`],
      ["Performance Ratio (PR)", `${D.pr_pct.toFixed(1)}%`, "Configurado por usuario"],
      ["Degradación anual", `${D.degradacion}%/año`, ""],
      ["Valor de rescate (plazo obj.)", `$${(ro.vr/1e6).toFixed(2)}M MXN`, D.valor_residual_nota],
    ],
    [3200, 3160, 3000]
  ),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 4. SUPUESTOS FINANCIEROS ─────────────────────────────────────────────────
  heading1("4. Supuestos Financieros"),
  heading2("4.1 CAPEX (llenar con cotización real del proveedor)"),
  dataTable(capexHeaders, capexRows, capexWidths),
  ...spacer(1),
  heading2("4.2 Parámetros del modelo"),
  dataTable(
    ["Supuesto", "Valor"],
    [
      ["WACC (tasa de descuento equity)", `${D.wacc}%`],
      ["Hurdle rate (WACC + spread)", `${D.wacc + D.spread}%`],
      ["Spread objetivo", `${D.spread}%`],
      ["Escalador PPA anual", `${D.esc_ppa}%/año`],
      ["Inflación CFE (perspectiva cliente)", `${D.inflacion_cfe}%/año`],
      ["O&M anual", `${D.om_pct}% del CAPEX MXN`],
      ["Seguros", `${D.seg_pct}% del CAPEX MXN`],
      ["Financiamiento", D.con_fin ? `Sí — ${100 - D.equity_pct}% deuda / ${D.equity_pct}% equity` : "No — 100% equity"],
      ["Tipo de cambio", `$${D.usd_to_mxn.toFixed(2)} MXN/USD`],
      ["Valor de rescate", D.usar_vr ? "Incluido (Gordon generalizado, suma finita exacta)" : "Excluido (escenario conservador)"],
    ],
    [4680, 4680]
  ),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 5. COMPARATIVO DE PLAZOS ─────────────────────────────────────────────────
  heading1("5. Comparativo de Plazos"),
  ph(`Hurdle rate: ${D.hurdle_label} · Valor de rescate: ${D.usar_vr ? "incluido" : "excluido"} · Generación base: ${D.gen_base_label}`,
     { color: GREY, size: 18 }),
  ...spacer(1),
  dataTable(plazosHeaders, plazosRows, plazoCols),
  ...spacer(2),

  // ── 6. RESULTADOS FINANCIEROS ────────────────────────────────────────────────
  heading1(`6. Resultados Financieros — Plazo objetivo: ${ro.pl} años`),
  heading2("6.1 Perspectiva del desarrollador"),
  dataTable(
    ["Métrica", "Valor", "Comentario"],
    [
      ["TIR equity", ro.tir ? `${ro.tir.toFixed(1)}%` : "N/A", `Hurdle: ${D.wacc + D.spread}% · WACC: ${D.wacc}%`],
      ["VPN", `$${(ro.vpn/1e6).toFixed(2)}M MXN`, "sobre equity aportado"],
      ["Payback simple", ro.pb ? `${ro.pb} años` : `>${ro.pl}a`, "nominal sin descontar"],
      ["Payback descontado", ro.pb_disc ? `${ro.pb_disc} años` : `>${ro.pl}a`, `a WACC ${D.wacc}%`],
      ["Ingreso total", `$${(ro.ing_total/1e6).toFixed(2)}M MXN`, `en ${ro.pl} años`],
      ["Valor de rescate", `$${(ro.vr/1e6).toFixed(2)}M MXN`, D.valor_residual_nota],
    ],
    [2800, 2560, 4000]
  ),
  ...spacer(1),
  heading2("6.2 Perspectiva del cliente"),
  dataTable(
    ["Métrica", "Valor"],
    [
      ["Tarifa CFE actual", `$${D.tarifa_cliente.toFixed(4)}/kWh`],
      ["Tarifa PPA ofrecida (año 1)", `$${D.precio_manual.toFixed(4)}/kWh`],
      ["Descuento vs CFE hoy", `${D.descuento_vs_cfe > 0 ? '+' : ''}${D.descuento_vs_cfe.toFixed(1)}%`],
      ["Ahorro total cliente estimado", `$${(D.ahorro_total/1e6).toFixed(2)}M MXN en ${ro.pl} años`],
      ["Inflación CFE proyectada", `${D.inflacion_cfe}%/año`],
    ],
    [4680, 4680]
  ),
  ...spacer(1),
  heading2("6.3 Análisis de escenarios — plazo objetivo"),
  ph(`Variables: CAPEX (±15%), Precio PPA (±15%), WACC (±2 pts), Escalador PPA (±1 pt). Plazo: ${ro.pl} años.`,
     { color: GREY, size: 18 }),
  ...spacer(1),
  dataTable(escHeaders, escRows, escWidths),
  new Paragraph({ children: [new PageBreak()] }),

  // ── 7. CONSIDERACIONES ───────────────────────────────────────────────────────
  heading1("7. Consideraciones y Próximos Pasos"),
  ph("• Los valores son estimados de pre-sizing (±15%). Simulación definitiva (PVSyst/Helioscope) es responsabilidad del proveedor EPC.", { color: GREY }),
  ph("• El contrato PPA debe incluir cláusulas de garantía de producción mínima (P90), penalidades por incumplimiento y condiciones de terminación anticipada.", { color: GREY }),
  ph("• Se recomienda auditoría energética del cliente para validar el perfil de consumo y la coincidencia horaria con la generación solar.", { color: GREY }),
  ph("• Trámite de interconexión CFE puede tomar 2–6 meses dependiendo de la zona y la capacidad del proyecto.", { color: GREY }),
  ph("• El CAPEX deberá confirmarse con cotizaciones formales de al menos 2 proveedores EPC certificados antes de firmar el contrato PPA.", { color: GREY }),
  ...spacer(2),
  ph("Preparado con Sizing Tool — Análisis PPA Fotovoltaico · Uso interno · Confidencial",
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
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } } },
    headers: {
      default: new Header({ children: [
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: AMBER, space: 4 } },
          spacing: { before: 0, after: 100 },
          children: [
            ...(logoRun ? [logoRun, new TextRun({ text: "   ", font: "Arial", size: 20 })] : []),
            new TextRun({ text: "Caso de Negocio PPA Solar · ", font: "Arial", size: 18, color: GREY }),
            new TextRun({ text: D.ubicacion, font: "Arial", size: 18, color: GREY, italics: true }),
          ]
        })
      ]})
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/tmp/word_output.docx', buf);
  console.log('OK');
});
