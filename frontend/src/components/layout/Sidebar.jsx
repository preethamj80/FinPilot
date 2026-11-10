import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ArrowLeftRight,
  PieChart,
  Bot,
  Sparkles,
  SlidersHorizontal,
  LineChart,
  Settings,
  ShieldCheck,
  PlusCircle,
} from 'lucide-react';
import { useFinance } from '../../context/FinanceContext';
import BrandLogo from '../common/BrandLogo';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/budgets', label: 'Budgets & Bills', icon: PieChart },
  { to: '/coach', label: 'AI Money Coach', icon: Bot, badge: 'AI' },
  { to: '/budget-optimizer', label: 'AI Budget Optimizer', icon: Sparkles, badge: 'AI' },
  { to: '/simulator', label: 'Future Planner', icon: SlidersHorizontal },
  { to: '/insights', label: 'Smart Insights', icon: LineChart },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ isOpen, onClose }) {
  const { openAddTx } = useFinance();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs lg:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-[var(--color-sidebar-bg)] text-slate-300 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="h-18 px-6 flex items-center gap-3 border-b border-slate-800/80">
          <BrandLogo size={48} />
          <div>
            <div className="text-lg font-bold text-white tracking-tight flex items-center gap-1.5">
              FinPilot
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-sm bg-teal-500/20 text-teal-300 border border-teal-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Smart Finance Engine</p>
          </div>
        </div>

        {/* Quick Action Button */}
        <div className="p-4">
          <button
            onClick={() => {
              if (onClose) onClose();
              openAddTx();
            }}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white font-semibold text-sm shadow-sm shadow-teal-900/40 flex items-center justify-center gap-2 transition-all active:scale-[0.98] cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            Add Transaction
          </button>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-colors duration-150 ${
                    isActive
                      ? 'bg-teal-500/15 text-teal-300 font-semibold border-l-3 border-teal-400'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-teal-400/20 text-teal-300">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer info badge */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/30">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
            <span>Secure Offline Vault</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">FastAPI backend · Local SQLite</p>
        </div>
      </aside>
    </>
  );
}
