import { useState, useCallback } from 'react';
import { steps } from './data/steps';
import { useProgress } from './hooks/useProgress';
import { useKeyboardNav } from './hooks/useKeyboardNav';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { StepContent } from './components/StepContent';
import { SystemStatus } from './components/SystemStatus';
import { HardwareInventory } from './components/HardwareInventory';
import type { AppView } from './types';
import './styles/index.css';

export default function App() {
  const {
    currentStep,
    completed,
    timestamps,
    percentage,
    goToStep,
    markComplete,
    reset,
  } = useProgress();

  const [view, setView] = useState<AppView>('setup');
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);

  useKeyboardNav(currentStep, goToStep);

  const handleGoToStep = useCallback(
    (i: number) => { goToStep(i); window.scrollTo(0, 0); },
    [goToStep]
  );

  const handleMarkComplete = useCallback(() => {
    markComplete(); window.scrollTo(0, 0);
  }, [markComplete]);

  const handleReset = useCallback(() => {
    if (window.confirm('Resetear todo el progreso?')) reset();
  }, [reset]);

  const toggleDiagnostics = useCallback(() => {
    setDiagnosticsOpen(prev => !prev);
  }, []);

  const currentPhase = steps[currentStep].phase;

  return (
    <div className="wrap">
      <Header
        percentage={percentage}
        currentPhase={currentPhase}
        currentView={view}
        onChangeView={setView}
        completed={completed}
        timestamps={timestamps}
      />

      <div className="layout">
        {view === 'setup' && (
          <>
            <Sidebar
              currentStep={currentStep}
              completed={completed}
              timestamps={timestamps}
              diagnosticsOpen={diagnosticsOpen}
              onGoToStep={handleGoToStep}
              onToggleDiagnostics={toggleDiagnostics}
              onReset={handleReset}
            />
            <StepContent
              currentStep={currentStep}
              completed={completed}
              diagnosticsOpen={diagnosticsOpen}
              onMarkComplete={handleMarkComplete}
              onGoToStep={handleGoToStep}
            />
          </>
        )}

        {view === 'hardware' && <HardwareInventory />}
        {view === 'sistema' && <SystemStatus />}
      </div>
    </div>
  );
}
