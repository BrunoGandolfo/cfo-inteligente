import { useState, useCallback } from 'react';
import type { DetectionResult } from '../types';

interface SystemStatusState {
  results: DetectionResult[];
  loading: boolean;
  error: string | null;
  lastChecked: string | null;
}

export function useSystemStatus() {
  const [state, setState] = useState<SystemStatusState>({
    results: [],
    loading: false,
    error: null,
    lastChecked: null,
  });

  const detect = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const res = await fetch('/api/system/detect');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setState({
        results: data.results,
        loading: false,
        error: null,
        lastChecked: data.timestamp,
      });
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: `Error: ${err instanceof Error ? err.message : String(err)}`,
      }));
    }
  }, []);

  return { ...state, detect };
}
