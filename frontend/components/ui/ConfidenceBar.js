import clsx from 'clsx';

/* Derive the raw relevance score from stored confidence + label.
   The classifier stores confidence differently per label:
     RELEVANT   → confidence = min(rawScore, 0.95)   → relevance = confidence
     AMBIGUOUS  → confidence = rawScore              → relevance = confidence
     IRRELEVANT → confidence = 1 - rawScore          → relevance = 1 - confidence
*/
export function relevanceScore(confidence, label) {
  const c = confidence ?? 0;
  return label === 'IRRELEVANT' ? 1 - c : c;
}

export default function ConfidenceBar({ value, label }) {
  const score = (label !== undefined) ? relevanceScore(value, label) : (value ?? 0);
  const pct   = Math.round(score * 100);
  const color =
    pct >= 70 ? 'bg-emerald-500' :
    pct >= 30 ? 'bg-amber-400'   :
                'bg-red-400';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-neutral-150 rounded-full overflow-hidden min-w-[48px]">
        <div
          className={clsx('h-full rounded-full transition-all duration-500', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium text-neutral-600 w-9 text-right tabular-nums">
        {pct}%
      </span>
    </div>
  );
}
