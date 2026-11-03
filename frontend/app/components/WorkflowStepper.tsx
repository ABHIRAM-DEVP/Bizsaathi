import Link from "next/link";

export type WorkflowStepStatus = "complete" | "current" | "upcoming";

export interface WorkflowStep {
  label: string;
  description: string;
  status: WorkflowStepStatus;
}

type WorkflowAction =
  | { label: string; description: string; href: string }
  | { label: string; description: string; onClick: () => void; disabled?: boolean };

export function WorkflowStepper({
  label,
  context,
  steps,
  nextAction,
}: {
  label: string;
  context: string;
  steps: WorkflowStep[];
  nextAction: WorkflowAction;
}) {
  return (
    <aside className="workflow-stepper surface-card" aria-label={label}>
      <p className="eyebrow">YOUR WORKFLOW</p>
      <p className="workflow-context">{context}</p>
      <ol className="workflow-step-list" data-step-count={steps.length}>
        {steps.map((step, index) => (
          <li
            key={step.label}
            className={step.status}
            aria-current={step.status === "current" ? "step" : undefined}
          >
            <span className="workflow-step-marker" aria-hidden="true">
              {step.status === "complete" ? "✓" : index + 1}
            </span>
            <span>
              <strong>{step.label}</strong>
              <small>{step.description}</small>
            </span>
          </li>
        ))}
      </ol>
      <div className="workflow-next-action">
        <p className="eyebrow">NEXT STEP</p>
        <p>{nextAction.description}</p>
        {"href" in nextAction ? (
          <Link className="button button-primary" href={nextAction.href}>
            {nextAction.label}
          </Link>
        ) : (
          <button
            className="button button-primary"
            type="button"
            onClick={nextAction.onClick}
            disabled={nextAction.disabled}
          >
            {nextAction.label}
          </button>
        )}
      </div>
    </aside>
  );
}
