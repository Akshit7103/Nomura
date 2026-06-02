'use client';
import { useEffect, useRef } from 'react';
import clsx from 'clsx';

export default function LogDrawer({ open, onClose, title, logs = [] }) {
  const listRef = useRef(null);

  useEffect(() => {
    if (open && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [open, logs.length]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-neutral-900/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative z-10 w-full max-w-2xl bg-white rounded-xl shadow-card-lg border border-neutral-200 flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-200">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-neutral-900">{title}</span>
            <span className="text-xs bg-neutral-100 text-neutral-500 px-2 py-0.5 rounded font-medium">
              {logs.length} entries
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded flex items-center justify-center hover:bg-neutral-100 text-neutral-500 hover:text-neutral-700 transition-colors"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {/* Log lines */}
        <div
          ref={listRef}
          className="flex-1 overflow-y-auto bg-neutral-900 rounded-b-xl scrollbar-thin"
        >
          {logs.length === 0 ? (
            <p className="text-xs text-neutral-500 p-4 font-mono">No log entries.</p>
          ) : (
            <div className="py-2">
              {logs.map((line, i) => (
                <LogLine key={i} line={line} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LogLine({ line }) {
  const isObj = typeof line === 'object';
  const level = isObj ? line.level : 'info';

  const levelColor = {
    info:    'text-blue-400',
    success: 'text-emerald-400',
    warn:    'text-amber-400',
    error:   'text-red-400',
  }[level] ?? 'text-neutral-400';

  const levelBadge = {
    info:    'INFO',
    success: ' OK ',
    warn:    'WARN',
    error:   ' ERR',
  }[level] ?? 'INFO';

  const msg  = isObj ? line.message : String(line);
  const time = isObj ? line.time    : null;

  return (
    <div className="flex items-start gap-3 px-4 py-0.5 hover:bg-neutral-800 transition-colors">
      {time && (
        <span className="text-neutral-600 font-mono text-xs whitespace-nowrap mt-px">{time}</span>
      )}
      <span className={clsx('font-mono text-xs font-bold whitespace-nowrap mt-px', levelColor)}>
        [{levelBadge}]
      </span>
      <span className="font-mono text-xs text-neutral-300 break-all leading-5">{msg}</span>
    </div>
  );
}
