import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { systemRoutes } from './routes.js';
import { hardwareRoutes } from './hardware.js';
import { claudeRoutes } from './claudeRoutes.js';
import { docsRoutes } from './docsRoutes.js';

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// API routes
app.use('/api/system', systemRoutes);
app.use('/api/hardware', hardwareRoutes);
app.use('/api/claude', claudeRoutes);
app.use('/api/docs', docsRoutes);

// In production, serve the built React app
const distPath = path.join(__dirname, '..', 'dist');
app.use(express.static(distPath));
app.get('/{*path}', (_req, res) => {
  res.sendFile(path.join(distPath, 'index.html'));
});

app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`[server] http://localhost:${PORT}`);
  console.log(`[server] Red local: http://0.0.0.0:${PORT}`);
  if (process.env.ANTHROPIC_API_KEY) {
    console.log('[server] Claude API configurada');
  } else {
    console.log('[server] Claude API no configurada (sin .env)');
  }
});
