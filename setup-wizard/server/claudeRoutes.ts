import { Router } from 'express';
import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const claudeRoutes = Router();

function getClient(): Anthropic | null {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return null;
  return new Anthropic({ apiKey: key });
}

function loadHardwareContext(): string {
  try {
    const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'hardware.json'), 'utf-8'));
    return data.map((i: { category: string; model: string; specs: string; status: string }) =>
      `- ${i.category}: ${i.model} (${i.specs}) [${i.status}]`
    ).join('\n');
  } catch {
    return 'Hardware no configurado';
  }
}

const SYSTEM_PROMPT = `Eres un ingeniero experto en infraestructura de IA local, especializado en configuraciones con GPUs NVIDIA (RTX 5090, arquitectura Blackwell, sm_120) sobre WSL2 en Windows 11.

Tu rol es ayudar a diagnosticar errores y responder preguntas tecnicas sobre la configuracion de este sistema. Eres pedagogico pero tecnico: explicas el "por que" sin perder rigor.

HARDWARE DEL USUARIO:
{HARDWARE}

REGLAS:
- Responde en espanol
- Se conciso y directo
- Da soluciones paso a paso con comandos copiables
- Si no estas seguro, dilo
- Siempre explica la causa raiz, no solo el fix
- Prioriza soluciones que no requieran reinstalar todo`;

claudeRoutes.get('/status', (_req, res) => {
  res.json({ configured: !!process.env.ANTHROPIC_API_KEY });
});

claudeRoutes.post('/diagnose', async (req, res) => {
  const client = getClient();
  if (!client) {
    return res.status(503).json({ error: 'API key no configurada. Agrega ANTHROPIC_API_KEY al archivo .env' });
  }

  const { error, step, context } = req.body;
  if (!error) {
    return res.status(400).json({ error: 'Falta el campo "error"' });
  }

  const hardware = loadHardwareContext();
  const systemPrompt = SYSTEM_PROMPT.replace('{HARDWARE}', hardware);

  let userMessage = `DIAGNOSTICO DE ERROR\n\nError reportado:\n${error}`;
  if (step) userMessage += `\n\nPaso actual del setup: ${step}`;
  if (context) userMessage += `\n\nContexto adicional: ${context}`;

  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 2048,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    });

    const text = message.content
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map(b => b.text)
      .join('\n');

    res.json({ diagnosis: text, model: message.model, usage: message.usage });
  } catch (err) {
    res.status(500).json({ error: 'Error llamando a Claude', details: String(err) });
  }
});

claudeRoutes.post('/ask', async (req, res) => {
  const client = getClient();
  if (!client) {
    return res.status(503).json({ error: 'API key no configurada' });
  }

  const { question } = req.body;
  if (!question) {
    return res.status(400).json({ error: 'Falta el campo "question"' });
  }

  const hardware = loadHardwareContext();
  const systemPrompt = SYSTEM_PROMPT.replace('{HARDWARE}', hardware);

  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 2048,
      system: systemPrompt,
      messages: [{ role: 'user', content: question }],
    });

    const text = message.content
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map(b => b.text)
      .join('\n');

    res.json({ answer: text, model: message.model, usage: message.usage });
  } catch (err) {
    res.status(500).json({ error: 'Error llamando a Claude', details: String(err) });
  }
});
