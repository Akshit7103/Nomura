import clsx from 'clsx';

export function Card({ className, children, noPad = false, hoverable = false }) {
  return (
    <div
      className={clsx(
        'bg-white border border-neutral-150 rounded-lg shadow-card',
        hoverable && 'transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-card-md hover:border-neutral-200 cursor-default',
        !noPad && 'p-5',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, description, actions, className }) {
  return (
    <div className={clsx('flex items-start justify-between gap-4 mb-5', className)}>
      <div>
        <h2 className="text-sm font-semibold text-neutral-900 leading-snug">{title}</h2>
        {description && (
          <p className="mt-0.5 text-xs text-neutral-400 leading-relaxed">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>}
    </div>
  );
}
