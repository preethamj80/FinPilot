import React from 'react';
import { Menu, LogOut, Calendar, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useFinance } from '../../context/FinanceContext';
// ProfileDropdown import removed – using inline user display
import NotificationIcon from '../common/NotificationIcon';

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  const { notify, notifications = [] } = useFinance();

  const handleLogout = async () => {
    try {
      await logout();
      notify('You have been logged out safely.', 'success');
    } catch {
      notify('Logged out.', 'success');
    }
  };

  const todayStr = new Intl.DateTimeFormat('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date());

  return (
    <header className="sticky top-0 z-30 h-16 bg-[var(--color-sidebar-bg)]/95 backdrop-blur-md border-b border-slate-300/80 px-4 sm:px-6 flex items-center justify-between text-slate-900">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-xl text-slate-300 hover:bg-slate-800/30 transition-colors"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-300 font-medium">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 text-slate-200 border border-slate-700/60">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            {todayStr}
          </span>
          <span className="text-slate-400">·</span>
          <span className="inline-flex items-center gap-1 text-teal-300 bg-teal-700/20 px-2 py-0.5 rounded-full border border-teal-600/60 text-[11px]">
            <ShieldCheck className="w-3 h-3 text-teal-400" />
            Live Vault Active
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <NotificationIcon count={notifications?.length || 0} />
        {user && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{user.full_name?.split(' ')[0] || user.username}</span>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-full text-slate-300 hover:text-white hover:bg-slate-800/30 transition-colors"
              aria-label="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

