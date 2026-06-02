import clsx from 'clsx';

export default function StatCard({ label, value, icon, color = 'blue', sub }) {
  const colors = {
    blue:    { bg: 'bg-blue-50',   icon: 'text-blue-600',   val: 'text-blue-700'   },
    green:   { bg: 'bg-emerald-50', icon: 'text-emerald-600', val: 'text-emerald-700' },
    amber:   { bg: 'bg-amber-50',  icon: 'text-amber-600',  val: 'text-amber-700'  },
    red:     { bg: 'bg-red-50',    icon: 'text-red-600',    val: 'text-red-700'    },
    neutral: { bg: 'bg-neutral-100', icon: 'text-neutral-500', val: 'text-neutral-700' },
  };
  const c = colors[color] ?? colors.blue;

  return (
    <div className="group bg-white border border-neutral-150 rounded-lg p-4 shadow-card flex items-center gap-4 transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-card-md hover:border-neutral-200 cursor-default">
      <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-transform duration-200 group-hover:scale-110', c.bg)}>
        <span className={clsx('w-5 h-5 flex items-center justify-center', c.icon)}>
          {icon}
        </span>
      </div>
      <div className="min-w-0">
        <p className="text-xs text-neutral-500 font-medium uppercase tracking-wide truncate">{label}</p>
        <p className={clsx('text-2xl font-bold leading-tight', c.val)}>
          {value ?? <span className="text-neutral-300">—</span>}
        </p>
        {sub && <p className="text-xs text-neutral-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}
