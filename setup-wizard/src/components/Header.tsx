import { phases } from '../data/phases';
import { useExport } from '../hooks/useExport';
import type { AppView, ProgressState } from '../types';

interface HeaderProps {
  percentage: number;
  currentPhase: number;
  currentView: AppView;
  previousView: AppView | null;
  onChangeView: (view: AppView) => void;
  onGoBack: () => void;
  completed: ProgressState['completed'];
  timestamps: ProgressState['timestamps'];
}

const tabs: { id: AppView; label: string }[] = [
  { id: 'setup', label: 'Configuracion' },
  { id: 'hardware', label: 'Hardware' },
  { id: 'sistema', label: 'Sistema' },
];

export function Header({ percentage, currentPhase, currentView, previousView, onChangeView, onGoBack, completed, timestamps }: HeaderProps) {
  const { exportMarkdown } = useExport({ completed, timestamps, percentage });

  return (
    <header className="header">
      <div className="header-top">
        <div>
          <h1 className="header-title">Centro de Control — Dual RTX 5090</h1>
          <p className="header-subtitle">Infraestructura de IA local</p>
        </div>
        <div className="header-right">
          {previousView && currentView !== 'setup' && (
            <button className="back-btn" onClick={onGoBack} title="Volver">
              ← Volver
            </button>
          )}
          <button className="export-btn" onClick={exportMarkdown} title="Exportar progreso a Markdown">
            Exportar .md
          </button>
          <div>
            <div className="header-pct">{percentage}%</div>
            <div className="header-pct-label">completado</div>
          </div>
        </div>
      </div>

      <div className="progress-bar-bg">
        <div className="progress-bar-fill" style={{ width: `${percentage}%` }} />
      </div>

      <div className="header-bottom">
        <div className="phase-row">
          {phases.map((phase, i) => (
            <span
              key={i}
              className={`phase-tag ${currentPhase === i ? 'phase-active' : ''}`}
              style={{
                background: currentPhase === i ? phase.color : 'rgba(255,255,255,0.08)',
                color: currentPhase === i ? '#fff' : 'rgba(255,255,255,0.45)',
              }}
            >
              {phase.name}
            </span>
          ))}
        </div>

        <div className="tab-nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${currentView === tab.id ? 'tab-active' : ''}`}
              onClick={() => onChangeView(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}
