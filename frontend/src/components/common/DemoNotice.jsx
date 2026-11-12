import React from 'react';
import { DEMO_MODE } from '../../demo/demoMode';

export default function DemoNotice({ compact = false, ai = false, className = '' }) {
  if (!DEMO_MODE) return null;
  return (
    <div className={`flex items-start gap-2 rounded-xl border border-[var(--color-gold)]/35 bg-[var(--color-gold)]/10 px-3 py-2 text-xs text-[var(--color-text-primary)] ${compact ? 'text-[11px]' : ''} ${className}`} role="note">
      <span className="shrink-0 rounded-full border border-[var(--color-gold)]/50 px-2 py-0.5 font-bold uppercase tracking-wide text-[var(--color-gold)]">
        {ai ? 'Illustrative' : 'Demo Mode'}
      </span>
      <span>
        {ai
          ? 'Illustrative sample recommendations only — not live AI-generated financial advice.'
          : 'Sample data only. Changes stay in memory and reset when you refresh; no real financial information is stored.'}
      </span>
    </div>
  );
}
