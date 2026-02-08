import { Router } from 'express';
import { detectAll } from './detector.js';

export const systemRoutes = Router();

systemRoutes.get('/detect', async (_req, res) => {
  try {
    const results = await detectAll();
    res.json({ timestamp: new Date().toISOString(), results });
  } catch (err) {
    res.status(500).json({ error: 'Error detectando sistema', details: String(err) });
  }
});
