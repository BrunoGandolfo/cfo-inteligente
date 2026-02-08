import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, LevelFormat, PageNumber, PageBreak,
} from 'docx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const C = {
  dark: '1E293B', accent: '2563EB', green: '059669', orange: 'D97706',
  red: 'DC2626', gray: '64748B', white: 'FFFFFF', black: '000000',
  headerBg: '1E293B', tableBorder: 'CBD5E1',
};

const border = { style: BorderStyle.SINGLE, size: 1, color: C.tableBorder };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

interface HWItem { category: string; model: string; specs: string; status: string; price?: number }

function loadHardware(): HWItem[] {
  try {
    return JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'hardware.json'), 'utf-8'));
  } catch { return []; }
}

function h1(text: string) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, font: 'Arial', size: 32, color: C.dark })] });
}
function h2(text: string) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, font: 'Arial', size: 26, color: C.accent })] });
}
function h3(text: string) {
  return new Paragraph({ spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, font: 'Arial', size: 22, color: C.dark })] });
}
function p(text: string, color?: string) {
  return new Paragraph({ spacing: { after: 120 },
    children: [new TextRun({ text, font: 'Arial', size: 21, color: color || C.black })] });
}
function bullet(text: string, ref = 'bullets') {
  return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80 },
    children: [new TextRun({ text, font: 'Arial', size: 21 })] });
}
function numItem(text: string, ref = 'numbers') {
  return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80 },
    children: [new TextRun({ text, font: 'Arial', size: 21 })] });
}
function spacer() { return new Paragraph({ spacing: { after: 200 }, children: [] }); }
function pb() { return new Paragraph({ children: [new PageBreak()] }); }

function makeRow(cells: string[], isHeader = false) {
  const widths = cells.length === 2 ? [3500, 5860] : cells.length === 3 ? [2200, 4160, 3000] : [2340, 2340, 2340, 2340];
  return new TableRow({
    children: cells.map((text, i) => new TableCell({
      borders, width: { size: widths[i], type: WidthType.DXA }, margins: cellMargins,
      shading: isHeader ? { fill: C.headerBg, type: ShadingType.CLEAR } : undefined,
      children: [new Paragraph({ children: [new TextRun({ text, font: 'Arial', size: 20, bold: isHeader, color: isHeader ? C.white : C.black })] })],
    })),
  });
}

function makeTable(headers: string[], rows: string[][]) {
  const widths = headers.length === 2 ? [3500, 5860] : headers.length === 3 ? [2200, 4160, 3000] : [2340, 2340, 2340, 2340];
  return new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: widths,
    rows: [makeRow(headers, true), ...rows.map(r => makeRow(r))],
  });
}

export async function generatePlanMaestro(): Promise<Buffer> {
  const hw = loadHardware();
  const installed = hw.filter(h => h.status === 'installed');
  const pending = hw.filter(h => h.status !== 'installed');
  const totalCost = pending.reduce((sum, h) => sum + (h.price || 0), 0);

  const doc = new Document({
    styles: { default: { document: { run: { font: 'Arial', size: 21 } } } },
    numbering: {
      config: [
        { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ],
    },
    sections: [{
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
      },
      headers: {
        default: new Header({ children: [
          new Paragraph({ alignment: AlignmentType.RIGHT, children: [
            new TextRun({ text: 'Plan Maestro \u2014 Dual RTX 5090 \u2014 CFO Inteligente', font: 'Arial', size: 16, color: C.gray, italics: true }),
          ] }),
        ] }),
      },
      footers: {
        default: new Footer({ children: [
          new Paragraph({ alignment: AlignmentType.CENTER, children: [
            new TextRun({ text: 'Pagina ', font: 'Arial', size: 16, color: C.gray }),
            new TextRun({ children: [PageNumber.CURRENT], font: 'Arial', size: 16, color: C.gray }),
            new TextRun({ text: ' \u2014 Conexion Consultora \u2014 Febrero 2026', font: 'Arial', size: 16, color: C.gray }),
          ] }),
        ] }),
      },
      children: [
        // COVER
        spacer(), spacer(), spacer(),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
          children: [new TextRun({ text: 'PLAN MAESTRO', font: 'Arial', size: 48, bold: true, color: C.dark })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
          children: [new TextRun({ text: 'Infraestructura de IA Local con Dual RTX 5090', font: 'Arial', size: 28, color: C.accent })] }),
        spacer(),
        makeTable(['Dato', 'Valor'], [
          ['Proyecto', 'CFO Inteligente \u2014 Conexion Consultora'],
          ['Autor', 'Bruno Gandolfo (CFO & Partner)'],
          ['Arquitecto IA', 'Claude (Anthropic)'],
          ['Fecha', new Date().toLocaleDateString('es-UY', { year: 'numeric', month: 'long' })],
          ['Clasificacion', 'Documento estrategico interno'],
          ['Version', '1.0'],
        ]),
        pb(),

        // 1. RESUMEN EJECUTIVO
        h1('1. Resumen Ejecutivo'),
        p('Este documento describe el plan completo para dotar a CFO Inteligente de capacidad de inteligencia artificial local, eliminando la dependencia de APIs en la nube y multiplicando la potencia de procesamiento disponible.'),
        spacer(),
        h3('El problema actual'),
        bullet('Cada consulta al CFO AI cuesta dinero (API de Anthropic: ~$5-20/mes).'),
        bullet('La latencia depende de internet y de los servidores de Anthropic.'),
        bullet('Los datos financieros de la firma viajan a servidores externos.'),
        bullet('No hay control sobre limites de uso, cambios de precio o disponibilidad.'),
        spacer(),
        h3('La solucion'),
        bullet('Instalar dos GPUs NVIDIA RTX 5090 (32 GB VRAM cada una = 64 GB total).'),
        bullet('Correr modelos de IA localmente con rendimiento comparable a GPT-4.'),
        bullet('Cero costo por consulta. Cero latencia de red. Cero datos saliendo de la oficina.'),
        spacer(),
        makeTable(['Metrica', 'Hoy (Nube)', 'Manana (Local)'], [
          ['Costo por consulta', '~$0.01-0.05', '$0.00'],
          ['Latencia tipica', '2-5 segundos', '<1 segundo'],
          ['Privacidad de datos', 'Salen a EEUU', 'No salen de la oficina'],
          ['Limite de uso', 'Segun plan/creditos', 'Ilimitado'],
        ]),
        pb(),

        // 2. HARDWARE
        h1('2. Hardware'),
        h2('2.1 Componentes instalados'),
        makeTable(['Componente', 'Modelo', 'Specs'], installed.map(h => [h.category, h.model, h.specs])),
        spacer(),
        h2('2.2 Componentes pendientes / en camino'),
        makeTable(['Componente', 'Modelo', 'Specs'], pending.map(h => [h.category, h.model, h.specs])),
        spacer(),
        p(`Inversion total estimada: ~USD $${totalCost.toLocaleString()}`, C.accent),
        pb(),

        // 3. PLAN DE EJECUCION
        h1('3. Plan de Ejecucion'),
        makeTable(['Fase', 'Que se hace', 'Cuando'], [
          ['Fase 1: Pre-requisitos', 'Verificar WSL2, driver, CUDA', 'AHORA (30 min)'],
          ['Fase 2: Software IA', 'Ollama, modelos, vLLM, Open WebUI', 'AHORA (2-4 horas)'],
          ['Fase 3: Hardware + Integracion', 'Instalar hardware + conectar con CFO', 'Cuando llegue el hardware'],
        ]),
        spacer(),
        h2('Fase 1: Pre-requisitos'),
        numItem('Verificar WSL2 (wsl --version, kernel 5.10+)'),
        numItem('Verificar driver NVIDIA (nvidia-smi, driver 580+)'),
        numItem('Instalar CUDA Toolkit 12.8 (obligatorio para RTX 5090 / sm_120)'),
        spacer(),
        h2('Fase 2: Software IA'),
        numItem('Instalar Ollama (curl -fsSL https://ollama.com/install.sh | sh)'),
        numItem('Descargar Qwen 2.5 72B (~42 GB) — modelo principal'),
        numItem('Descargar DeepSeek-R1 70B (~42 GB) — razonamiento'),
        numItem('Descargar Qwen Coder 32B (~34 GB) — codigo/SQL'),
        numItem('Instalar PyTorch nightly + vLLM'),
        numItem('Instalar Open WebUI via Docker'),
        numItem('Configurar monitoreo (nvtop, htop)'),
        spacer(),
        h2('Fase 3: Hardware + Integracion'),
        numItem('Instalar motherboard MSI MEG Z890 ACE'),
        numItem('GPU 1 en PCIEX16 (x16), GPU 2 en PCIEX8 (x8)'),
        numItem('Configurar dual PSU con adaptador Add2PSU'),
        numItem('Verificar dual GPU (nvidia-smi, PyTorch, Ollama)'),
        numItem('Test termico 30 minutos (ambas GPUs < 83C)'),
        numItem('Integrar con CFO Inteligente (API local Ollama)'),
        pb(),

        // 4. RENDIMIENTO ESPERADO
        h1('4. Rendimiento Esperado'),
        makeTable(['Modelo', '1x RTX 5090', '2x RTX 5090'], [
          ['Qwen 2.5 72B (Q4)', '~12-15 t/s', '~25-30 t/s'],
          ['DeepSeek-R1 70B', '~10-12 t/s', '~20-25 t/s'],
          ['Qwen Coder 32B (Q8)', '~35-45 t/s', '~60-80 t/s'],
          ['Consulta SQL tipica CFO', '~3-5 seg', '~1-3 seg'],
        ]),
        pb(),

        // 5. RIESGOS
        h1('5. Riesgos y Mitigacion'),
        makeTable(['Riesgo', 'Severidad', 'Mitigacion'], [
          ['Sobrecalentamiento', 'ALTA', 'Test termico 30 min. Corsair 9000D + 9 ventiladores.'],
          ['Corte de luz', 'MEDIA', 'UPS recomendado para apagado limpio.'],
          ['Modelo no alcanza calidad Claude', 'BAJA', 'Fallback a Claude API para consultas criticas.'],
          ['Fuente insuficiente', 'MEDIA', 'Seasonic PX-1600 + segunda fuente via Add2PSU.'],
        ]),
        pb(),

        // CIERRE
        h1('Cierre'),
        p('Este plan transforma a Conexion Consultora de consumidora de IA en la nube a operadora de IA propia. El 80% del trabajo se hace ANTES de que llegue el hardware nuevo.'),
        spacer(),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun({ text: 'Bruno Gandolfo', bold: true, font: 'Arial', size: 21 }),
          new TextRun({ text: ' \u2014 CFO & Partner, Conexion Consultora', font: 'Arial', size: 21, color: C.gray }),
        ] }),
        p(new Date().toLocaleDateString('es-UY', { year: 'numeric', month: 'long' }), C.gray),
      ],
    }],
  });

  return await Packer.toBuffer(doc) as unknown as Buffer;
}
