import { useState, useCallback, useEffect } from 'react';

interface ClaudeState {
  configured: boolean;
  loading: boolean;
  response: string | null;
}

export function useClaude() {
  const [state, setState] = useState<ClaudeState>({
    configured: false,
    loading: false,
    response: null,
  });

  useEffect(() => {
    fetch('/api/claude/status')
      .then(r => r.json())
      .then(d => setState(prev => ({ ...prev, configured: d.configured })))
      .catch(() => {});
  }, []);

  const diagnose = useCallback(async (error: string, step?: string) => {
    setState(prev => ({ ...prev, loading: true, response: null }));
    try {
      const res = await fetch('/api/claude/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error, step }),
      });
      const data = await res.json();
      setState(prev => ({
        ...prev,
        loading: false,
        response: data.diagnosis || data.error,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        response: `Error de conexion: ${err instanceof Error ? err.message : String(err)}`,
      }));
    }
  }, []);

  const ask = useCallback(async (question: string) => {
    setState(prev => ({ ...prev, loading: true, response: null }));
    try {
      const res = await fetch('/api/claude/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setState(prev => ({
        ...prev,
        loading: false,
        response: data.answer || data.error,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        response: `Error de conexion: ${err instanceof Error ? err.message : String(err)}`,
      }));
    }
  }, []);

  const clear = useCallback(() => {
    setState(prev => ({ ...prev, response: null }));
  }, []);

  return { ...state, diagnose, ask, clear };
}
