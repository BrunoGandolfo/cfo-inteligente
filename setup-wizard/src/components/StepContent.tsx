import { steps } from '../data/steps';
import { phases } from '../data/phases';
import { stepContent } from '../data/content';
import { CommandBlock } from './CommandBlock';
import { InfoBox } from './InfoBox';
import { Diagnostics } from './Diagnostics';

interface StepContentProps {
  currentStep: number;
  completed: Record<number, boolean>;
  diagnosticsOpen: boolean;
  onMarkComplete: () => void;
  onGoToStep: (i: number) => void;
}

export function StepContent({
  currentStep,
  completed,
  diagnosticsOpen,
  onMarkComplete,
  onGoToStep,
}: StepContentProps) {
  const step = steps[currentStep];
  const content = stepContent[step.id];
  const phase = phases[step.phase];
  const isDone = completed[currentStep];
  const isLast = currentStep === steps.length - 1;

  const nextLabel = isDone
    ? 'Completado — Siguiente'
    : isLast
      ? 'Marcar como completado'
      : 'Completar y siguiente';

  const btnColor = isDone ? '#059669' : phase.color;

  return (
    <main className="content">
      <div className="card">
        <div className="step-header">
          <span className="step-icon">{step.icon}</span>
          <div>
            <div className="step-phase" style={{ color: phase.color }}>
              {phase.name}
            </div>
            <h2 className="step-title">{step.title}</h2>
          </div>
          {isDone && <span className="step-done-badge">Completado</span>}
        </div>

        <InfoBox variant="why" title="Por que hacemos esto">
          {content.why}
        </InfoBox>

        {content.alternative && (
          <InfoBox variant="alternative" title="Por que esta opcion y no otra">
            {content.alternative}
          </InfoBox>
        )}

        {content.explanation && (
          <InfoBox variant="explanation" title="">
            <pre className="explanation-pre">{content.explanation}</pre>
          </InfoBox>
        )}
      </div>

      {content.commands.length > 0 && (
        <div className="card">
          <h3 className="commands-title">Comandos — copiar y pegar en WSL</h3>
          {content.commands.map((cmd, i) => (
            <CommandBlock key={i} command={cmd} index={i} />
          ))}
        </div>
      )}

      {content.successCriteria && (
        <div className="success-card">
          <h4>Criterio de exito</h4>
          <p>{content.successCriteria}</p>
        </div>
      )}

      {diagnosticsOpen && <Diagnostics currentStepName={step.title} />}

      <div className="nav-row">
        <button
          className="btn-secondary"
          disabled={currentStep === 0}
          onClick={() => onGoToStep(currentStep - 1)}
        >
          Anterior
        </button>
        <button
          className="btn-primary"
          style={{ background: btnColor }}
          onClick={onMarkComplete}
        >
          {nextLabel}
        </button>
      </div>
    </main>
  );
}
