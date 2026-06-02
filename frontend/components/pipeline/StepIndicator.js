import clsx from 'clsx';

export default function StepIndicator({ steps, current }) {
  return (
    <nav className="flex items-center gap-0 mb-6">
      {steps.map((step, i) => {
        const state =
          i < current ? 'done' :
          i === current ? 'active' :
          'locked';

        return (
          <div key={i} className="flex items-center gap-0 flex-1 min-w-0">
            <div className={clsx(
              'flex items-center gap-2.5 px-4 py-2.5 flex-1 min-w-0 rounded-lg transition-colors',
              state === 'done'   && 'bg-emerald-50 border border-emerald-200',
              state === 'active' && 'bg-white border border-brand-300 ring-1 ring-brand-400 shadow-card',
              state === 'locked' && 'bg-neutral-100 border border-neutral-200',
            )}>
              {/* Step number / check */}
              <div className={clsx(
                'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold',
                state === 'done'   && 'bg-emerald-500 text-white',
                state === 'active' && 'bg-brand-600 text-white',
                state === 'locked' && 'bg-neutral-300 text-neutral-500',
              )}>
                {state === 'done' ? (
                  <svg viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5">
                    <path fillRule="evenodd" d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z" clipRule="evenodd" />
                  </svg>
                ) : state === 'locked' ? (
                  <svg viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3">
                    <path fillRule="evenodd" d="M8 1a3.5 3.5 0 0 0-3.5 3.5V7A1.5 1.5 0 0 0 3 8.5v5A1.5 1.5 0 0 0 4.5 15h7a1.5 1.5 0 0 0 1.5-1.5v-5A1.5 1.5 0 0 0 11.5 7V4.5A3.5 3.5 0 0 0 8 1Zm2 6V4.5a2 2 0 1 0-4 0V7h4Z" clipRule="evenodd" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>

              {/* Label */}
              <div className="min-w-0">
                <p className={clsx(
                  'text-xs font-semibold leading-tight truncate',
                  state === 'done'   && 'text-emerald-700',
                  state === 'active' && 'text-brand-700',
                  state === 'locked' && 'text-neutral-400',
                )}>
                  {step.label}
                </p>
                <p className={clsx(
                  'text-[10px] leading-tight truncate',
                  state === 'done'   && 'text-emerald-500',
                  state === 'active' && 'text-brand-500',
                  state === 'locked' && 'text-neutral-400',
                )}>
                  {state === 'done' ? 'Complete' : state === 'locked' ? 'Locked' : 'In progress'}
                </p>
              </div>
            </div>

            {/* Connector */}
            {i < steps.length - 1 && (
              <div className={clsx(
                'h-px w-6 flex-shrink-0 mx-1',
                i < current ? 'bg-emerald-300' : 'bg-neutral-200',
              )} />
            )}
          </div>
        );
      })}
    </nav>
  );
}
