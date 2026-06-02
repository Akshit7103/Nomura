"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function Header({ title, breadcrumbs = [] }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api
      .health()
      .then((d) => setHealth(d?.status ?? "healthy"))
      .catch(() => setHealth("unreachable"));
  }, []);

  const isHealthy = health === "healthy" || health === "ok";

  return (
    <header
      className="px-6 sticky top-0 z-30 flex items-center justify-between h-16 flex-shrink-0"
      style={{
        background: 'linear-gradient(90deg, #112244 0%, #1a3260 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5">
        {breadcrumbs.map((crumb, i) => (
          <span key={i} className="flex items-center gap-1.5">
            {i > 0 && (
              <svg viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3 flex-shrink-0" style={{ color: 'rgba(255,255,255,0.2)' }}>
                <path fillRule="evenodd" d="M6.22 4.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L9.19 8 6.22 5.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
              </svg>
            )}
            <span
              className="text-[13px]"
              style={{
                color: i === breadcrumbs.length - 1 ? '#ffffff' : 'rgba(255,255,255,0.65)',
                fontWeight: i === breadcrumbs.length - 1 ? 500 : 400,
              }}
            >
              {crumb}
            </span>
          </span>
        ))}
      </nav>

      {/* Right */}
      <div className="flex items-center gap-3">

        {/* API health */}
        <div className="flex items-center gap-1.5">
          <span style={{
            display: 'inline-block', width: 5, height: 5, borderRadius: '50%',
            background: health === null ? 'rgba(255,255,255,0.2)' : isHealthy ? '#12b76a' : '#f04438',
          }} />
          <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.72)' }}>
            {health === null ? 'Checking…' : isHealthy ? 'API Online' : 'API Offline'}
          </span>
        </div>

        <div className="w-px h-3.5" style={{ background: 'rgba(255,255,255,0.1)' }} />

        {/* Auto-sync */}
        <div className="flex items-center gap-1.5">
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5" style={{ color: 'rgba(255,255,255,0.65)' }}>
            <path fillRule="evenodd" d="M15.312 11.424a5.5 5.5 0 0 1-9.201 2.466l-.312-.311h2.433a.75.75 0 0 0 0-1.5H3.989a.75.75 0 0 0-.75.75v4.242a.75.75 0 0 0 1.5 0v-2.43l.31.31a7 7 0 0 0 11.712-3.138.75.75 0 0 0-1.449-.39Zm1.23-3.723a.75.75 0 0 0 .219-.53V2.929a.75.75 0 0 0-1.5 0V5.36l-.31-.31A7 7 0 0 0 3.239 8.188a.75.75 0 1 0 1.448.389A5.5 5.5 0 0 1 13.89 6.11l.311.31h-2.432a.75.75 0 0 0 0 1.5h4.243a.75.75 0 0 0 .53-.219Z" clipRule="evenodd" />
          </svg>
          <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.72)' }}>auto-sync · 24h</span>
        </div>

        <div className="w-px h-3.5" style={{ background: 'rgba(255,255,255,0.1)' }} />

        {/* Notifications */}
        <button
          className="relative w-7 h-7 flex items-center justify-center rounded transition-colors duration-150"
          style={{ color: 'rgba(255,255,255,0.4)' }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.8)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'rgba(255,255,255,0.4)'; }}
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-[15px] h-[15px]">
            <path d="M4.214 3.227a.75.75 0 0 0-1.156-.956 8.97 8.97 0 0 0-1.856 3.826.75.75 0 0 0 1.466.316 7.47 7.47 0 0 1 1.546-3.186ZM16.942 2.271a.75.75 0 0 0-1.157.956 7.47 7.47 0 0 1 1.547 3.186.75.75 0 0 0 1.466-.316 8.971 8.971 0 0 0-1.856-3.826ZM10 2a6 6 0 0 0-6 6v1.076l-.894 1.788A.75.75 0 0 0 3.776 12h12.448a.75.75 0 0 0 .67-1.136L16 9.076V8a6 6 0 0 0-6-6ZM9.249 14.504a.75.75 0 0 0-1.326.696C8.37 16.224 9.112 17 10 17c.888 0 1.63-.776 2.077-1.8a.75.75 0 0 0-1.326-.696c-.2.454-.428.746-.751.746-.323 0-.551-.292-.751-.746Z" />
          </svg>
          <span className="absolute top-1.5 right-1.5 w-1 h-1 rounded-full bg-sky-400" />
        </button>

        {/* Avatar */}
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0"
          style={{ background: 'rgba(255,255,255,0.15)' }}
        >
          HP
        </div>

      </div>
    </header>
  );
}
