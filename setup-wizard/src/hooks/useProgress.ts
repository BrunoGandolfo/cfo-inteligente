import { useState, useCallback, useEffect } from 'react';
import type { ProgressState } from '../types';
import { steps } from '../data/steps';

const STORAGE_KEY = 'rtx5090-wizard-v4';

function loadState(): ProgressState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        completed: parsed.completed || {},
        timestamps: parsed.timestamps || {},
        currentStep: parsed.currentStep || 0,
      };
    }
  } catch {
    // ignore
  }
  return { completed: {}, timestamps: {}, currentStep: 0 };
}

function saveState(state: ProgressState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignore
  }
}

export function useProgress() {
  const [state, setState] = useState<ProgressState>(loadState);

  useEffect(() => {
    saveState(state);
  }, [state]);

  const currentStep = state.currentStep;

  const goToStep = useCallback((index: number) => {
    if (index >= 0 && index < steps.length) {
      setState((prev) => ({ ...prev, currentStep: index }));
    }
  }, []);

  const markComplete = useCallback(() => {
    setState((prev) => {
      const next = { ...prev };
      next.completed = { ...prev.completed, [prev.currentStep]: true };
      if (!prev.timestamps[prev.currentStep]) {
        next.timestamps = {
          ...prev.timestamps,
          [prev.currentStep]: new Date().toISOString(),
        };
      }
      if (prev.currentStep < steps.length - 1) {
        next.currentStep = prev.currentStep + 1;
      }
      return next;
    });
  }, []);

  const toggleComplete = useCallback((index: number) => {
    setState((prev) => {
      const wasCompleted = prev.completed[index];
      const newCompleted = { ...prev.completed };
      const newTimestamps = { ...prev.timestamps };
      if (wasCompleted) {
        delete newCompleted[index];
        delete newTimestamps[index];
      } else {
        newCompleted[index] = true;
        newTimestamps[index] = new Date().toISOString();
      }
      return { ...prev, completed: newCompleted, timestamps: newTimestamps };
    });
  }, []);

  const reset = useCallback(() => {
    const fresh: ProgressState = { completed: {}, timestamps: {}, currentStep: 0 };
    setState(fresh);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const completedCount = Object.keys(state.completed).filter(
    (k) => state.completed[Number(k)]
  ).length;

  const percentage = Math.round((completedCount / steps.length) * 100);

  return {
    currentStep,
    completed: state.completed,
    timestamps: state.timestamps,
    percentage,
    completedCount,
    goToStep,
    markComplete,
    toggleComplete,
    reset,
  };
}
