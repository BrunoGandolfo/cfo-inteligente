import { useEffect, useState } from 'react';
import { useSystemStatus } from '../hooks/useSystemStatus';
import { CardExplainer } from './CardExplainer';
import { CATEGORY_LABELS, CATEGORY_ORDER } from '../types';
import type { DetectionCategory, DetectionResult } from '../types';

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

const categoryIcon: Record<DetectionCategory, string> = {
  hardware: '🖥',
  ai_runtime: '⚡',
  ai_frameworks: '🧠',
  ai_servers: '🌐',
  dev_tools: '🔧',
};

export function SystemStatus() {
  const { results, loading, error, lastChecked, detect } = useSystemStatus();
  const [expandedCard, setExpandedCard] = useState<string | null>(null);

  useEffect(() => { detect(); }, [detect]);

  const okCount = results.filter(r => r.status === 'ok').length;
  const warnCount = results.filter(r => r.status === 'warning').length;
  const errCount = results.filter(r => r.status === 'error' || r.status === 'not_installed').length;

  // Group results by category
  const grouped = CATEGORY_ORDER.map(cat => ({
    category: cat,
    label: CATEGORY_LABELS[cat],
    icon: categoryIcon[cat],
    items: results.filter(r => r.category === cat),
  })).filter(g => g.items.length > 0);

  const handleToggleExplainer = (componentId: string) => {
    setExpandedCard(prev => prev === componentId ? null : componentId);
  };

  const expandedComponent = expandedCard
    ? results.find(r => r.id === expandedCard)
    : null;

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h2 className="view-title">Radiografia del Sistema</h2>
          <p className="view-subtitle">
            Deteccion automatica de hardware y software para IA
            {lastChecked && (
              <span className="view-meta">
                {' '}— Ultima verificacion: {new Date(lastChecked).toLocaleTimeString('es-UY')}
              </span>
            )}
          </p>
        </div>
        <button className="btn-secondary" onClick={detect} disabled={loading}>
          {loading ? 'Escaneando...' : 'Escanear'}
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
            <span className="summary-label">No disponibles</span>
          </div>
          <div className="summary-item summary-total">
            <span className="summary-count">{results.length}</span>
            <span className="summary-label">Componentes</span>
          </div>
        </div>
      )}

      {loading && results.length === 0 && (
        <div className="scan-loading">
          <div className="scan-spinner" />
          <p>Escaneando hardware y software...</p>
          <p className="scan-hint">Detectando 23 componentes en paralelo</p>
        </div>
      )}

      {grouped.map((group) => {
        const groupOk = group.items.filter(r => r.status === 'ok').length;
        const groupTotal = group.items.length;
        return (
          <div key={group.category} className="category-section">
            <div className="category-header">
              <span className="category-icon">{group.icon}</span>
              <span className="category-label">{group.label}</span>
              <span className="category-count">{groupOk}/{groupTotal}</span>
            </div>
            <div className="status-grid">
              {group.items.map((r) => (
                <StatusCard
                  key={r.id}
                  result={r}
                  isExpanded={expandedCard === r.id}
                  onToggleExplainer={() => handleToggleExplainer(r.id)}
                />
              ))}
            </div>
          </div>
        );
      })}

      {/* Explainer panel — shown below all cards when a card is selected */}
      {expandedComponent && (
        <CardExplainer
          component={expandedComponent}
          onClose={() => setExpandedCard(null)}
        />
      )}
    </div>
  );
}

function StatusCard({ result: r, isExpanded, onToggleExplainer }: {
  result: DetectionResult;
  isExpanded: boolean;
  onToggleExplainer: () => void;
}) {
  return (
    <div className={`status-card status-${r.status} ${isExpanded ? 'status-card-active' : ''}`}>
      <div className="status-card-header">
        <span className={`status-badge badge-${r.status}`}>
          {statusIcon[r.status]}
        </span>
        <div style={{ flex: 1 }}>
          <div className="status-name">{r.name}</div>
          <div className="status-label">{statusLabel[r.status]}</div>
        </div>
        <button
          className={`learn-btn ${isExpanded ? 'learn-btn-active' : ''}`}
          onClick={onToggleExplainer}
          title={isExpanded ? 'Cerrar explicacion' : 'Aprender sobre este componente'}
        >
          {isExpanded ? '✕' : '📖'}
        </button>
      </div>
      <div className="status-message">{r.message}</div>
      {r.details && (
        <pre className="status-details">{r.details}</pre>
      )}
    </div>
  );
}
