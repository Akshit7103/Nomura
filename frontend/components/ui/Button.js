import clsx from 'clsx';

const base =
  'inline-flex items-center gap-2 font-medium rounded transition-colors duration-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed select-none';

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2   text-sm',
  lg: 'px-5 py-2.5 text-sm',
};

const variants = {
  primary:
    'bg-brand-500 text-white border border-brand-600 hover:bg-brand-600 active:bg-brand-700 shadow-sm',
  secondary:
    'bg-white text-neutral-700 border border-neutral-300 hover:bg-neutral-50 active:bg-neutral-100 shadow-sm',
  ghost:
    'bg-transparent text-neutral-600 border border-transparent hover:bg-neutral-100 hover:text-neutral-800',
  danger:
    'bg-red-600 text-white border border-red-700 hover:bg-red-700 active:bg-red-800 shadow-sm',
};

export default function Button({ variant = 'primary', size = 'md', loading = false, icon, children, className, ...props }) {
  return (
    <button
      className={clsx(base, sizes[size], variants[variant], className)}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
          <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        </svg>
      ) : icon ? (
        <span className="w-4 h-4 flex-shrink-0 flex items-center justify-center">{icon}</span>
      ) : null}
      {children}
    </button>
  );
}
