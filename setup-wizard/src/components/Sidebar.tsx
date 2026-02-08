import { steps } from '../data/steps';
import { phases } from '../data/phases';

interface SidebarProps {
  currentStep: number;
  completed: Record<number, boolean>;
  timestamps: Record<number, string>;
  diagnosticsOpen: boolean;
  onGoToStep: (i: number) => void;
  onToggleDiagnostics: () => void;
  onReset: () => void;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('es-UY', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function Sidebar({
  currentStep,
  completed,
  timestamps,
  diagnosticsOpen,
  onGoToStep,
  onToggleDiagnostics,
  onReset,
}: SidebarProps) {
  return (
    <nav className="sidebar">
      <div className="sidebar-inner">
        {steps.map((step, i) => {
          const active = i === currentStep;
          const done = completed[i];
          const phase = phases[step.phase];
          const ts = timestamps[i];

          return (
            <button
              key={step.id}
              className={`sidebar-btn ${active ? 'active' : ''} ${done ? 'done' : ''}`}
              style={{
                color: active ? phase.color : done ? '#059669' : '#6b7280',
                background: active ? `${phase.color}15` : 'transparent',
                borderLeftColor: active ? phase.color : 'transparent',
                fontWeight: active ? 600 : 400,
              }}
              onClick={() => onGoToStep(i)}
            >
              <span className="sidebar-icon">{done ? '✅' : step.icon}</span>
              <span className="sidebar-label">
                {step.title}
                {done && ts && (
                  <span className="sidebar-ts">{formatTimestamp(ts)}</span>
                )}
              </span>
            </button>
          );
        })}

        <div className="sidebar-sep" />

        <button
          className={`sidebar-btn ${diagnosticsOpen ? 'active' : ''}`}
          style={{
            color: diagnosticsOpen ? '#d97706' : '#6b7280',
            background: diagnosticsOpen ? 'rgba(254,243,199,0.13)' : 'transparent',
            borderLeftColor: diagnosticsOpen ? '#f59e0b' : 'transparent',
            fontWeight: diagnosticsOpen ? 600 : 400,
          }}
          onClick={onToggleDiagnostics}
        >
          <span className="sidebar-icon">🔧</span>
          <span className="sidebar-label">Tengo un error</span>
        </button>

        <div className="sidebar-sep" />

        <button className="sidebar-btn" onClick={onReset}>
          <span className="sidebar-icon">🔄</span>
          <span className="sidebar-label sidebar-reset">Resetear progreso</span>
        </button>
      </div>
    </nav>
  );
}
