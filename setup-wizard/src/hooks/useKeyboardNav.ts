import { useEffect } from 'react';
import { steps } from '../data/steps';

export function useKeyboardNav(
  currentStep: number,
  goToStep: (i: number) => void
) {
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      // Don't capture when typing in a textarea
      if (e.target instanceof HTMLTextAreaElement) return;

      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        goToStep(Math.max(0, currentStep - 1));
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        goToStep(Math.min(steps.length - 1, currentStep + 1));
      }
    }

    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [currentStep, goToStep]);
}
