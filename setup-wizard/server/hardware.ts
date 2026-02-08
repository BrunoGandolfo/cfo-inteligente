import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_PATH = path.join(__dirname, 'data', 'hardware.json');

export const hardwareRoutes = Router();

interface HardwareItem {
  id: string;
  category: string;
  model: string;
  specs: string;
  status: 'installed' | 'pending' | 'ordered';
  price?: number;
  notes?: string;
}

function readData(): HardwareItem[] {
  try {
    return JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8'));
  } catch {
    return [];
  }
}

function writeData(items: HardwareItem[]) {
  fs.writeFileSync(DATA_PATH, JSON.stringify(items, null, 2));
}

hardwareRoutes.get('/', (_req, res) => {
  res.json(readData());
});

hardwareRoutes.post('/', (req, res) => {
  const items = readData();
  const newItem: HardwareItem = {
    id: `hw-${Date.now()}`,
    ...req.body,
  };
  items.push(newItem);
  writeData(items);
  res.status(201).json(newItem);
});

hardwareRoutes.put('/:id', (req, res) => {
  const items = readData();
  const idx = items.findIndex(i => i.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'No encontrado' });
  items[idx] = { ...items[idx], ...req.body, id: items[idx].id };
  writeData(items);
  res.json(items[idx]);
});

hardwareRoutes.delete('/:id', (req, res) => {
  let items = readData();
  const len = items.length;
  items = items.filter(i => i.id !== req.params.id);
  if (items.length === len) return res.status(404).json({ error: 'No encontrado' });
  writeData(items);
  res.json({ ok: true });
});
