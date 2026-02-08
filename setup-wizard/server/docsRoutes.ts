import { Router } from 'express';
import { generatePlanMaestro } from './docgen.js';

export const docsRoutes = Router();

docsRoutes.get('/plan-maestro', async (_req, res) => {
  try {
    const buffer = await generatePlanMaestro();
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
    res.setHeader('Content-Disposition', 'attachment; filename=Plan_Maestro_Dual_RTX5090.docx');
    res.send(buffer);
  } catch (err) {
    res.status(500).json({ error: 'Error generando documento', details: String(err) });
  }
});
