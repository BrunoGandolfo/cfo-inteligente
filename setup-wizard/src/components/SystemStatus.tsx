import { useEffect } from 'react';
import { useSystemStatus } from '../hooks/useSystemStatus';

const statusIcon: Record<string, string> = {
  ok: '✓',
  warning: '!',
  error: '✗',
  not_installed: '—',
};

const statusLabel: Record<string, string> = {
  ok: 'Operativo',
  warning: 'Atencion',
  error: 'Error',
  not_installed: 'No instalado',
};

export function SystemStatus() {
  const { results, loading, error, lastChecked, detect } = useSystemStatus();

  useEffect(() => { detect(); }, [detect]);

  const okCount = results.filter(r => r.status === 'ok').length;
  const warnCount = results.filter(r => r.status === 'warning').length;
  const errCount = results.filter(r => r.status === 'error' || r.status === 'not_installed').length;

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h2 className="view-title">Estado del Sistema</h2>
          <p className="view-subtitle">
            Deteccion automatica del entorno WSL2
            {lastChecked && (
              <span className="view-meta">
                {' '}— Ultima verificacion: {new Date(lastChecked).toLocaleTimeString('es-UY')}
              </span>
            )}
          </p>
        </div>
        <button className="btn-secondary" onClick={detect} disabled={loading}>
          {loading ? 'Detectando...' : 'Actualizar'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {results.length > 0 && (
        <div className="status-summary">
          <div className="summary-item summary-ok">
            <span className="summary-count">{okCount}</span>
            <span className="summary-label">Operativos</span>
          </div>
          <div className="summary-item summary-warn">
            <span className="summary-count">{warnCount}</span>
            <span className="summary-label">Atencion</span>
          </div>
          <div className="summary-item summary-err">
            <span className="summary-count">{errCount}</span>
            <span className="summary-label">Pendientes</span>
          </div>
        </div>
      )}

      <div className="status-grid">
        {loading && results.length === 0 && (
          <div className="status-loading">Detectando componentes del sistema...</div>
        )}
        {results.map((r) => (
          <div key={r.id} className={`status-card status-${r.status}`}>
            <div className="status-card-header">
              <span className={`status-badge badge-${r.status}`}>
                {statusIcon[r.status]}
              </span>
              <div>
                <div className="status-name">{r.name}</div>
                <div className="status-label">{statusLabel[r.status]}</div>
              </div>
            </div>
            <div className="status-message">{r.message}</div>
            {r.details && (
              <pre className="status-details">{r.details}</pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
