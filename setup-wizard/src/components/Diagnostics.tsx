import { useState, useCallback } from 'react';
import { knownErrors } from '../data/knownErrors';
import { useClaude } from '../hooks/useClaude';
import type { KnownError } from '../types';

interface DiagnosticsProps {
  currentStepName?: string;
}

export function Diagnostics({ currentStepName }: DiagnosticsProps) {
  const [input, setInput] = useState('');
  const [localResults, setLocalResults] = useState<KnownError[] | null>(null);
  const { configured, loading, response, diagnose, clear } = useClaude();

  const handleDiagnose = useCallback(() => {
    if (!input.trim()) return;
    clear();

    const lower = input.toLowerCase();
    const matches = knownErrors.filter(err =>
      err.patterns.some(p => lower.includes(p.toLowerCase()))
    );
    setLocalResults(matches.length > 0 ? matches : []);

    if (matches.length === 0 && configured) {
      diagnose(input, currentStepName);
    }
  }, [input, configured, diagnose, clear, currentStepName]);

  const handleAskClaude = useCallback(() => {
    if (!input.trim() || !configured) return;
    diagnose(input, currentStepName);
  }, [input, configured, diagnose, currentStepName]);

  return (
    <div className="diagnostics">
      <h3 className="diagnostics-title">Diagnostico de Errores</h3>
      <p className="diagnostics-desc">
        Pega el error que te aparece. Primero busca en la base local; si no encuentra, consulta a Claude.
      </p>
      <textarea
        className="diagnostics-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && e.ctrlKey) handleDiagnose(); }}
        placeholder="Pega tu error aca... (Ctrl+Enter para diagnosticar)"
      />
      <div className="diagnostics-actions">
        <button className="btn-primary" onClick={handleDiagnose} disabled={!input.trim()}>
          Diagnosticar
        </button>
        {configured && (
          <button className="btn-secondary" onClick={handleAskClaude} disabled={!input.trim() || loading}>
            {loading ? 'Consultando a Claude...' : 'Preguntar a Claude'}
          </button>
        )}
        {!configured && (
          <span className="diagnostics-hint">Agrega ANTHROPIC_API_KEY al .env para diagnostico con IA</span>
        )}
      </div>

      {localResults !== null && localResults.length > 0 && (
        <div className="diagnostics-results">
          <div className="diagnostics-results-label">Errores conocidos encontrados:</div>
          {localResults.map((err, i) => (
            <div key={i} className="diag-result">
              <h4>{err.title}</h4>
              <p><strong>Causa:</strong> {err.cause}</p>
              <div className="diag-solutions">
                <strong>Soluciones:</strong>
                {err.solutions.map((sol, j) => (
                  <p key={j}>{j + 1}. {sol}</p>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {localResults !== null && localResults.length === 0 && !response && !loading && (
        <div className="diagnostics-results">
          <div className="diag-result diag-empty">
            {configured
              ? 'No se encontro patron conocido. Consultando a Claude...'
              : 'No se encontro patron conocido. Configura la API de Claude para diagnostico avanzado.'}
          </div>
        </div>
      )}

      {loading && (
        <div className="diagnostics-results">
          <div className="claude-loading">Claude esta analizando el error...</div>
        </div>
      )}

      {response && (
        <div className="diagnostics-results">
          <div className="claude-response">
            <div className="claude-response-header">Diagnostico de Claude</div>
            <div className="claude-response-body">
              {response.split('\n').map((line, i) => (
                <p key={i}>{line || '\u00A0'}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
