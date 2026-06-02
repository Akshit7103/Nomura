'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import StatCard from '@/components/ui/StatCard';
import Badge from '@/components/ui/Badge';
import ConfidenceBar from '@/components/ui/ConfidenceBar';
import EmptyState from '@/components/ui/EmptyState';
import { ProcessLoader, SkeletonRows, useStagedLoader } from '@/components/ui/Loader';
import {
  FolderOpenIcon2, Cog6ToothIcon, PaperClipIcon, ChartBarIcon,
  MagnifyingGlassIcon, DocumentIcon, CheckCircleIcon, ArrowPathIcon,
} from '@/components/ui/Icons';

const EXTRACT_STEPS = [
  'Loading case index',
  'Reading manifest files',
  'Parsing trade fields',
  'Resolving counterparties',
  'Building trade register',
];

/* ─── currency symbol / code map ──────────────────────────── */
const SYMBOL_MAP = {
  '$':   'USD',   // bare $ = USD (unless prefixed)
  'A$':  'AUD',   // Australian dollar
  'C$':  'CAD',   // Canadian dollar
  'NZ$': 'NZD',   // New Zealand dollar
  'HK$': 'HKD',
  'S$':  'SGD',
  '£':   'GBP',
  '€':   'EUR',
  '¥':   'JPY',
  'kr':  'SEK',   // approximate; could be DKK/NOK too
};

/* ─── parse trade fields from subject + body ────────────────
   Priority: body fields > subject regex                      */
function parseTradeFields(subject = '', body = '') {
  const text = subject;

  // ── Currency pair from subject ──────────────────────────
  const ccySlash  = text.match(/\b([A-Z]{3})\/([A-Z]{3})\b/);
  let currencyPair = ccySlash ? ccySlash[0] : null;

  // ── Amount and inferred currency from BODY ──────────────
  let amount = null;
  let buyOrSell = null;
  let counterparty = null;
  let valueDate = null;

  if (body) {
    // "Amount: AUD 37,673,146.00" or "Amount: $5016443" or "Amount: A$16952461"
    const amtLine = body.match(/Amount\s*:\s*([^\n\r*]+)/i);
    if (amtLine) {
      const raw = amtLine[1].trim().replace(/\*/g, '').trim();
      amount = raw;

      if (!currencyPair) {
        // Try "CCY 1,234,567" (3-letter code followed by digits)
        const codeAmt = raw.match(/^([A-Z]{3})\s+([\d,]+)/);
        if (codeAmt) {
          currencyPair = codeAmt[1];
        } else {
          // Try symbol prefixes: A$, C$, NZ$, HK$, S$, $, £, €, ¥
          const symMatch = raw.match(/^(NZ\$|HK\$|A\$|C\$|S\$|\$|£|€|¥|kr)/);
          if (symMatch) {
            currencyPair = SYMBOL_MAP[symMatch[1]] ?? null;
          }
        }
      }
    }

    // "Buy/Sell: Buy"
    const bsLine = body.match(/Buy\/Sell\s*:\s*([^\n\r*]+)/i);
    if (bsLine) buyOrSell = bsLine[1].trim().replace(/\*/g, '').trim();

    // "Counterparty: BNP Paribas"
    const cpLine = body.match(/Counterparty\s*:\s*([^\n\r*]+)/i);
    if (cpLine) counterparty = cpLine[1].trim().replace(/\*/g, '').trim();

    // "Value Date: 20-Nov-2026" or "Value Date: 26/05/2026"
    const vdLine = body.match(/Value\s*Date\s*:\s*([^\n\r*]+)/i);
    if (vdLine) {
      const vd = vdLine[1].trim().replace(/\*/g, '').trim();
      if (vd && vd.length > 2) valueDate = vd;
    }
  }

  // ── Settlement date from subject (fallback) ─────────────
  let settlementDate = valueDate;
  if (!settlementDate) {
    const d_und = subject.match(/\b(\d{2})[_](\d{2})[_](\d{2,4})\b/);
    const d_iso = subject.match(/\b(\d{4}-\d{2}-\d{2})\b/);
    const d_sl4 = subject.match(/\b(\d{2})\/(\d{2})\/(\d{4})\b/);
    const d_sl2 = subject.match(/\b(\d{2})\/(\d{2})\/(\d{2})\b/);
    if (d_und) {
      const yr = d_und[3].length === 2 ? `20${d_und[3]}` : d_und[3];
      settlementDate = `${d_und[1]}/${d_und[2]}/${yr}`;
    } else if (d_iso) {
      settlementDate = d_iso[1];
    } else if (d_sl4) {
      settlementDate = `${d_sl4[1]}/${d_sl4[2]}/${d_sl4[3]}`;
    } else if (d_sl2) {
      const [, dd, mm, yy] = d_sl2;
      const mmN = parseInt(mm), ddN = parseInt(dd);
      if (ddN >= 1 && ddN <= 31 && mmN >= 1 && mmN <= 12)
        settlementDate = `${dd}/${mm}/20${yy}`;
    }
  }

  // ── Counterparty from sender (fallback) ─────────────────
  // (kept in caller since we don't have sender here)

  return { currencyPair, settlementDate, amount, buyOrSell, counterparty };
}

/* Normalise a "classified email" record (from Step 2) into the
   same shape StepExtract expects from a DB case row. */
function normalise(entry) {
  return {
    trade_id:                 entry.trade_id,
    subject:                  entry.subject,
    sender:                   entry.sender,
    received_at:              entry.received_at,
    asset_class:              entry.asset_class,
    attachment_count:         entry.attachment_count ?? 0,
    message_id:               entry.message_id,
    status:                   entry.skip_reason === 'duplicate' ? 'duplicate' : (entry.status ?? 'ingested'),
    skip_reason:              entry.skip_reason ?? null,
    classification_label:     entry.classification_label ?? entry.label,
    classification_confidence:entry.classification_confidence ?? entry.confidence,
  };
}

/* ─── Trade detail drawer ──────────────────────────────────── */
function TradeDrawer({ entry, onClose }) {
  const open = !!entry;
  const [detail, setDetail]   = useState(null);
  const [loadingD, setLoadingD] = useState(false);

  useEffect(() => {
    if (!entry) { setDetail(null); return; }
    if (entry.skip_reason === 'duplicate') return; // no stored case
    setLoadingD(true);
    api.getCase(entry.trade_id)
      .then(d => setDetail(d))
      .catch(() => {})
      .finally(() => setLoadingD(false));
  }, [entry?.trade_id]);

  useEffect(() => {
    const fn = (e) => e.key === 'Escape' && onClose?.();
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [onClose]);

  const c    = detail?.case ?? entry;
  const mf   = detail?.manifest;
  const body = detail?.body_excerpt ?? '';
  const tf   = entry ? parseTradeFields(entry.subject ?? '', body) : {};
  const senderName = entry?.sender?.match(/^([^<(]+?)(?:\s*<|\s*\(|$)/)?.[1]?.trim() ?? entry?.sender ?? '—';
  const counterparty = tf.counterparty || senderName;

  return (
    <>
      <div className={`drawer-backdrop fixed inset-0 z-40 bg-neutral-900/25 backdrop-blur-[2px] ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} onClick={onClose} />
      <div className={`drawer-slide fixed top-0 right-0 z-50 h-full w-full max-w-lg bg-white border-l border-neutral-200 shadow-2xl flex flex-col ${open ? 'translate-x-0' : 'translate-x-full'}`}>
        {!entry ? null : <>
          {/* Header */}
          <div className="px-5 py-4 border-b border-neutral-200 flex-shrink-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <Badge variant="relevant" dot>RELEVANT</Badge>
                  {entry.skip_reason === 'duplicate' && (
                    <Badge variant="ambiguous">Duplicate</Badge>
                  )}
                  <span className="font-mono text-xs font-semibold text-brand-500 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                    {entry.trade_id ?? '—'}
                  </span>
                  {tf.currencyPair && (
                    <span className="text-xs font-semibold text-neutral-700 bg-neutral-100 px-2 py-0.5 rounded border border-neutral-200 font-mono">
                      {tf.currencyPair}
                    </span>
                  )}
                </div>
                <p className="text-sm font-semibold text-neutral-900 leading-snug line-clamp-2">{entry.subject ?? '—'}</p>
              </div>
              <button onClick={onClose} className="w-7 h-7 rounded flex items-center justify-center hover:bg-neutral-100 text-neutral-500 flex-shrink-0 transition-colors">
                <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" /></svg>
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5 scrollbar-thin">
            {loadingD && (
              <div className="flex items-center gap-2 text-xs text-neutral-400 py-4">
                <svg className="w-4 h-4 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.2" />
                  <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                </svg>
                Loading manifest…
              </div>
            )}

            {entry.skip_reason === 'duplicate' && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs">
                This trade ID was already present in the case store. This email was classified as RELEVANT but not stored to avoid duplicate trade records.
              </div>
            )}

            {/* Extracted trade data */}
            <div>
              <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wide mb-3">Extracted Trade Data</p>
              <div className="grid grid-cols-2 gap-2.5">
                <TradeField label="Trade ID"        value={entry.trade_id}          mono highlight />
                <TradeField label="Asset Class"     value={entry.asset_class} />
                <TradeField label="Currency Pair"   value={tf.currencyPair}         highlight={!!tf.currencyPair} />
                <TradeField label="Settlement Date" value={tf.settlementDate}       highlight={!!tf.settlementDate} />
                <TradeField label="Counterparty"    value={counterparty} />
                <TradeField label="Amount"          value={tf.amount}               highlight={!!tf.amount} />
                <TradeField label="Direction"       value={tf.buyOrSell} />
                <TradeField label="Attachments"     value={entry.attachment_count ?? 0} />
              </div>
            </div>

            {/* Classification */}
            <div>
              <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wide mb-2">Classification</p>
              <div className="flex items-start gap-3 p-3 bg-[#ecfdf3] border border-[#abefc6] rounded-lg">
                <span className="w-7 h-7 rounded-lg bg-[#dcfae6] flex items-center justify-center flex-shrink-0 text-[#027a48] mt-0.5">
                  <CheckCircleIcon className="w-4 h-4" />
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <Badge variant="relevant" dot>RELEVANT</Badge>
                    <span className="text-xs font-semibold text-[#027a48]">
                      {Math.round(((c?.classification_confidence ?? entry.classification_confidence ?? 0)) * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-xs text-[#027a48] leading-relaxed break-words">
                    {mf?.classification?.reason ?? '—'}
                  </p>
                </div>
              </div>
            </div>

            {/* Email metadata */}
            <div>
              <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wide mb-2">Email Metadata</p>
              <div className="space-y-1.5 text-xs">
                {[
                  ['Sender',      entry.sender],
                  ['Received',    entry.received_at],
                  ['Message ID',  entry.message_id,    true],
                  ['Case Folder', c?.case_folder,       true],
                  ['Status',      entry.status ?? 'ingested'],
                ].map(([label, value, mono]) => (
                  <div key={label} className="flex gap-2">
                    <span className="text-neutral-400 w-24 flex-shrink-0 text-[11px] pt-px">{label}</span>
                    <span className={`text-neutral-700 break-all leading-snug ${mono ? 'font-mono text-[10px]' : ''}`}>{value ?? '—'}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Attachments */}
            {mf?.attachments?.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wide mb-2">Attachments ({mf.attachments.length})</p>
                <div className="space-y-1.5">
                  {mf.attachments.map((att, i) => (
                    <div key={i} className="flex items-center gap-3 px-3 py-2 bg-neutral-50 border border-neutral-150 rounded-lg text-xs">
                      <span className="w-7 h-7 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-400 flex-shrink-0">
                        <DocumentIcon className="w-4 h-4" />
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-neutral-800 truncate">{att.filename}</p>
                        <p className="text-neutral-400 text-[10px]">{att.mime_type} · {att.size_bytes != null ? `${(att.size_bytes / 1024).toFixed(1)} KB` : 'unknown'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw body excerpt */}
            {body && (
              <div>
                <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wide mb-2">Email Body Excerpt</p>
                <pre className="text-[10px] text-neutral-600 bg-neutral-50 border border-neutral-150 rounded-lg px-3 py-2.5 whitespace-pre-wrap leading-relaxed font-mono overflow-x-auto scrollbar-thin">
                  {body}
                </pre>
              </div>
            )}
          </div>

          <div className="px-5 py-3 border-t border-neutral-150 flex-shrink-0">
            <p className="text-[10px] text-neutral-300 font-mono break-all">{entry.message_id ?? '—'}</p>
          </div>
        </>}
      </div>
    </>
  );
}

function TradeField({ label, value, mono, highlight }) {
  const hasValue = value !== null && value !== undefined && value !== '';
  return (
    <div className={`px-3 py-2.5 rounded-lg border text-xs ${highlight && hasValue ? 'bg-brand-50 border-brand-200' : 'bg-neutral-50 border-neutral-150'}`}>
      <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide mb-0.5">{label}</p>
      <p className={`font-medium truncate ${highlight && hasValue ? 'text-brand-700' : 'text-neutral-700'} ${mono ? 'font-mono text-[11px]' : ''}`}>
        {hasValue ? value : <span className="text-neutral-300 font-normal italic">—</span>}
      </p>
    </div>
  );
}

/* ─── main ─────────────────────────────────────────────────── */

export default function StepExtract({ enabled, preloadedCases }) {
  const [loading, setLoading] = useState(false);
  const [entries, setEntries] = useState(null);  // normalised display rows
  const [error,   setError]   = useState(null);
  const [drawer,  setDrawer]  = useState(null);
  const [search,  setSearch]  = useState('');

  const loader = useStagedLoader(EXTRACT_STEPS, 440);

  /* preloadedCases comes from Step 2 (classified email objects, all 14 relevant).
     We use those as the base. We also call listCases in the background so the
     auto-load path works when the tab is visited without Step 2 data. */
  useEffect(() => {
    if (!enabled) return;
    if (preloadedCases?.length > 0) {
      // Normalise classified email shape → display shape
      setEntries(preloadedCases.map(normalise));
    } else if (!entries && !loading) {
      loadFromDB();
    }
  }, [enabled, preloadedCases]);

  async function loadFromDB() {
    setLoading(true);
    setError(null);
    loader.start();
    try {
      const [data] = await Promise.all([
        api.listCases(),
        new Promise(r => setTimeout(r, EXTRACT_STEPS.length * 440 + 300)),
      ]);
      const rows = (data.cases ?? [])
        .filter(c => c.classification_label === 'RELEVANT')
        .map(normalise);
      setEntries(rows);
    } catch (e) {
      setError(e.message);
    } finally {
      loader.reset();
      setLoading(false);
    }
  }

  const activeCases = entries ?? [];
  const filtered = activeCases.filter(c =>
    !search ||
    c.trade_id?.toLowerCase().includes(search.toLowerCase()) ||
    c.subject?.toLowerCase().includes(search.toLowerCase()) ||
    c.asset_class?.toLowerCase().includes(search.toLowerCase()) ||
    c.sender?.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <TradeDrawer entry={drawer} onClose={() => setDrawer(null)} />

      <div className="space-y-4">
        {activeCases.length > 0 && !loading && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Relevant Cases"   value={activeCases.length}                                           icon={<FolderOpenIcon2 />} color="green"   />
            <StatCard label="Stored in DB"     value={activeCases.filter(c => c.status !== 'duplicate').length}     icon={<Cog6ToothIcon />}   color="blue"    />
            <StatCard label="With Attachments" value={activeCases.filter(c => c.attachment_count > 0).length}       icon={<PaperClipIcon />}   color="neutral" />
            <StatCard label="Avg Confidence"
              value={activeCases.length ? `${Math.round(activeCases.reduce((s,c) => s + (c.classification_confidence ?? 0), 0) / activeCases.length * 100)}%` : '—'}
              icon={<ChartBarIcon />} color="neutral"
            />
          </div>
        )}

        <div className="bg-white border border-neutral-200 rounded-lg shadow-card">
          <div className="p-5 pb-0">
            <CardHeader
              title="Extracted Trade Register"
              description="Parsed trade fields from all relevant emails · click any row to load full details from the case manifest."
              actions={
                entries && !loading && (
                  <Button variant="ghost" size="sm" loading={loading} onClick={loadFromDB}
                    icon={<ArrowPathIcon className="w-3.5 h-3.5" />}>Refresh</Button>
                )
              }
            />
          </div>

          {!enabled && !entries && (
            <div className="px-5 pb-5">
              <div className="flex items-center gap-2.5 p-3 bg-neutral-50 border border-neutral-150 rounded-lg text-neutral-500 text-xs">
                <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-neutral-400 flex-shrink-0">
                  <path fillRule="evenodd" d="M10 1a4.5 4.5 0 0 0-4.5 4.5V9H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-.5V5.5A4.5 4.5 0 0 0 10 1Zm3 8V5.5a3 3 0 1 0-6 0V9h6Z" clipRule="evenodd" />
                </svg>
                Run the shortlist first to generate trade cases.
              </div>
            </div>
          )}

          {error && <div className="px-5 pb-5"><div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">{error}</div></div>}

          {loading && <div className="pb-4"><ProcessLoader steps={EXTRACT_STEPS} currentStep={loader.step} title="Loading trade register…" /></div>}

          {entries && !loading && (
            <>
              <div className="px-5 pb-3">
                <div className="relative max-w-sm">
                  <svg viewBox="0 0 20 20" fill="currentColor" className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400">
                    <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11ZM2 9a7 7 0 1 1 12.452 4.391l3.328 3.329a.75.75 0 1 1-1.06 1.06l-3.329-3.328A7 7 0 0 1 2 9Z" clipRule="evenodd" />
                  </svg>
                  <input type="text" placeholder="Search trade ID, asset, sender…" value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 text-xs border border-neutral-200 rounded-md bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white" />
                </div>
              </div>

              {filtered.length === 0 ? (
                <div className="px-5 pb-5">
                  <EmptyState icon={<MagnifyingGlassIcon className="w-6 h-6" />} title="No cases found" description="No relevant cases match your search." />
                </div>
              ) : (
                <div className="overflow-x-auto border-t border-neutral-150">
                  <table className="w-full text-xs data-table">
                    <thead>
                      <tr className="bg-neutral-50 border-b border-neutral-150">
                        {['Trade ID', 'Sett. Date', 'Counterparty', 'Asset Class', 'Confidence', 'Status', ''].map(h => (
                          <th key={h} className="px-3 py-2.5 text-left text-[11px] font-semibold text-neutral-400 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-100">
                      {filtered.map((c) => {
                        /* Parse trade fields from subject only (body loads lazily in drawer) */
                        const tf  = parseTradeFields(c.subject ?? '', '');
                        const isDup = c.status === 'duplicate';
                        return (
                          <tr key={c.message_id ?? c.trade_id}
                            onClick={() => setDrawer(c)}
                            className={`cursor-pointer transition-colors ${drawer?.trade_id === c.trade_id ? 'bg-brand-50' : isDup ? 'bg-amber-50/40 hover:bg-amber-50' : 'hover:bg-[#f5f8ff]'}`}
                          >
                            <td className="px-3 py-2.5 font-mono text-brand-500 font-semibold whitespace-nowrap">
                              {c.trade_id ?? '—'}
                            </td>
                            <td className="px-3 py-2.5 font-mono text-[11px] text-neutral-600 whitespace-nowrap">
                              {tf.settlementDate ?? <span className="text-neutral-300">—</span>}
                            </td>
                            <td className="px-3 py-2.5 text-neutral-600 max-w-[130px] truncate whitespace-nowrap">
                              {c.sender?.replace(/<.*?>/, '').trim() || '—'}
                            </td>
                            <td className="px-3 py-2.5 text-neutral-600 whitespace-nowrap">{c.asset_class ?? '—'}</td>
                            <td className="px-3 py-2.5 w-28">
                              <ConfidenceBar value={c.classification_confidence} label="RELEVANT" />
                            </td>
                            <td className="px-3 py-2.5 whitespace-nowrap">
                              {isDup ? (
                                <Badge variant="ambiguous">Duplicate</Badge>
                              ) : (
                                <Badge variant="ingested" dot>{c.status ?? 'ingested'}</Badge>
                              )}
                            </td>
                            <td className="px-3 py-2.5">
                              <span className="flex items-center gap-1 text-brand-500 font-medium whitespace-nowrap">
                                <span className="text-[10px]">Details</span>
                                <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                                  <path fillRule="evenodd" d="M3 10a.75.75 0 0 1 .75-.75h10.638L10.23 5.29a.75.75 0 1 1 1.04-1.08l5.5 5.25a.75.75 0 0 1 0 1.08l-5.5 5.25a.75.75 0 1 1-1.04-1.08l4.158-3.96H3.75A.75.75 0 0 1 3 10Z" clipRule="evenodd" />
                                </svg>
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <div className="px-4 py-2.5 border-t border-neutral-100">
                    <p className="text-xs text-neutral-400">
                      {filtered.length} of {activeCases.length} relevant email{activeCases.length !== 1 ? 's' : ''} · {activeCases.filter(c => c.status === 'duplicate').length} duplicate trade ID{activeCases.filter(c => c.status === 'duplicate').length !== 1 ? 's' : ''} not stored · Click any row to view full trade details
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
