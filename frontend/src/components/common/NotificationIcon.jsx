import React from 'react';
import { Bell } from 'lucide-react';

export default function NotificationIcon({ count = 0, onClick }) {
  const safeCount = Number.isFinite(count) ? count : 0;

  return (
    <button
      type="button"
      onClick={onClick}
      className="relative p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/40 transition-colors focus:outline-none"
      aria-label="Notifications"
    >
      <Bell className="w-5 h-5" />
      {safeCount > 0 && (
        <span className="absolute top-1 right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-slate-950 bg-teal-500 rounded-full border-2 border-[var(--color-sidebar-bg)]">
          {safeCount > 9 ? '9+' : safeCount}
        </span>
      )}
    </button>
  );
}
