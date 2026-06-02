export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center mb-4 text-neutral-400">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-neutral-700 mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-neutral-500 max-w-sm leading-relaxed mb-4">{description}</p>
      )}
      {action}
    </div>
  );
}
