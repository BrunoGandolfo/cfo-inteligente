import { useCallback } from 'react';
import { steps } from '../data/steps';
import { phases } from '../data/phases';
import { stepContent } from '../data/content';
import type { ProgressState } from '../types';

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('es-UY', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function useExport(progress: {
  completed: ProgressState['completed'];
  timestamps: ProgressState['timestamps'];
  percentage: number;
}) {
  const exportMarkdown = useCallback(() => {
    const lines: string[] = [
      '# Setup Dual RTX 5090 — Reporte de Progreso',
      '',
      `**Progreso:** ${progress.percentage}%`,
      `**Exportado:** ${new Date().toLocaleString('es-UY')}`,
      '',
      '---',
      '',
    ];

    let currentPhase = -1;

    steps.forEach((step, index) => {
      if (step.phase !== currentPhase) {
        currentPhase = step.phase;
        lines.push(`## ${phases[currentPhase].name}`, '');
      }

      const done = progress.completed[index];
      const ts = progress.timestamps[index];
      const check = done ? '[x]' : '[ ]';
      const tsStr = ts ? ` _(${formatDate(ts)})_` : '';

      lines.push(`- ${check} **${step.icon} ${step.title}**${tsStr}`);

      const content = stepContent[step.id];
      if (content?.commands.length) {
        lines.push('');
        content.commands.forEach((cmd) => {
          if (!cmd.command.startsWith('#')) {
            lines.push(`  \`\`\`bash`);
            lines.push(`  ${cmd.command}`);
            lines.push(`  \`\`\``);
          }
        });
      }
      lines.push('');
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `setup-rtx5090-progreso-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [progress.completed, progress.timestamps, progress.percentage]);

  return { exportMarkdown };
}
