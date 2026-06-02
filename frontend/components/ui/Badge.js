import clsx from 'clsx';

const variants = {
  relevant:   'bg-[#ecfdf3] text-[#027a48] border-[#abefc6]',
  ambiguous:  'bg-[#fffaeb] text-[#b54708] border-[#fedf89]',
  irrelevant: 'bg-[#fff1f0] text-[#b42318] border-[#fecdca]',
  ingested:   'bg-[#eff4ff] text-[#3538cd] border-[#c7d7fd]',
  success:    'bg-[#ecfdf3] text-[#027a48] border-[#abefc6]',
  error:      'bg-[#fff1f0] text-[#b42318] border-[#fecdca]',
  pending:    'bg-neutral-100 text-neutral-500 border-neutral-200',
  synced:     'bg-[#eff4ff] text-[#2356d4] border-[#a4bcfd]',
};

const dots = {
  relevant:   'bg-[#12b76a]',
  ambiguous:  'bg-[#f79009]',
  irrelevant: 'bg-[#f04438]',
  ingested:   'bg-[#6172f3]',
  success:    'bg-[#12b76a]',
  error:      'bg-[#f04438]',
  pending:    'bg-neutral-400',
  synced:     'bg-[#2356d4]',
};

export default function Badge({ variant = 'pending', dot = false, children, className }) {
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border',
      variants[variant] ?? variants.pending,
      className,
    )}>
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full', dots[variant] ?? 'bg-neutral-400')} />}
      {children}
    </span>
  );
}
