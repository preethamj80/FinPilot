import React from 'react';
import {
  Sparkles,
  TrendingUp,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownLeft,
  PieChart as PieChartIcon,
  Bot,
  Zap,
  Lock,
} from 'lucide-react';
import BrandLogo from '../common/BrandLogo';

export default function AuthBrandShowcase() {
  return (
    <div className="relative w-full h-full bg-[var(--color-sidebar-bg)] text-white p-8 sm:p-10 lg:p-12 flex flex-col justify-between overflow-hidden select-none">
      {/* Ambient background lighting */}
      <div className="absolute top-0 right-0 -mr-24 -mt-24 w-96 h-96 rounded-full bg-teal-500/15 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-24 -mb-24 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-1/3 -translate-y-1/2 w-64 h-64 rounded-full bg-teal-600/10 blur-2xl pointer-events-none" />

      {/* Decorative Subtle Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* Top Header Content */}
      <div className="relative z-10 space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/15 text-teal-300 border border-teal-400/30 text-[11px] font-bold uppercase tracking-widest shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-teal-400" />
          Spend Smarter.
        </div>

        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
          Your Money. Your Future.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-300 via-emerald-300 to-teal-400">
            Under Control.
          </span>
        </h2>

        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-md font-normal">
          Understand your spending, optimize your budget and make smarter financial decisions with FinPilot.
        </p>
      </div>

      {/* Centerpiece: High-End Mockup Dashboard Display */}
      <div className="relative z-10 my-6 sm:my-8">
        <div className="relative mx-auto max-w-md rounded-3xl bg-slate-900/80 border border-slate-700/60 p-5 sm:p-6 shadow-2xl backdrop-blur-md space-y-4 ring-1 ring-white/10">
          {/* Top Bar inside mockup */}
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <BrandLogo size={28} className="rounded-lg" />
              <div>
                <span className="text-xs font-bold text-white tracking-tight">FinPilot Vault</span>
                <span className="block text-[10px] text-teal-400 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                  Real-Time Active
                </span>
              </div>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700/60">
              Demo Preview
            </span>
          </div>

          {/* 1. Floating Balance Card */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-800/90 to-slate-800/40 border border-slate-700/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="uppercase tracking-wider font-semibold text-[10px]">
                Available Liquid Cash
              </span>
              <span className="inline-flex items-center gap-0.5 text-emerald-400 font-semibold text-[11px] bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <TrendingUp className="w-3 h-3" /> +14.2%
              </span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-tabular">
                ₹1,48,500
              </span>
              <div className="text-right">
                <span className="text-[10px] font-bold text-teal-300 block">Safe to Spend</span>
                <span className="text-xs font-bold text-white font-tabular">₹4,950 /day</span>
              </div>
            </div>
          </div>

          {/* 2. Inflow / Outflow Quick Visualizer */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 mb-1">
                <ArrowDownLeft className="w-3.5 h-3.5" />
                <span>Monthly Inflow</span>
              </div>
              <span className="text-sm font-bold text-white font-tabular">₹85,000</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Salary & Returns</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <div className="flex items-center gap-1 text-[11px] font-semibold text-rose-400 mb-1">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>Monthly Outflow</span>
              </div>
              <span className="text-sm font-bold text-white font-tabular">₹32,400</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Bills & Spending</span>
            </div>
          </div>

          {/* 3. Category Spending Mini Bars */}
          <div className="p-3.5 rounded-2xl bg-slate-800/40 border border-slate-700/50 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400">
              <span>Category Outflows</span>
              <span className="text-teal-400">62% Savings Margin</span>
            </div>

            <div className="space-y-1.5">
              <div>
                <div className="flex justify-between text-[11px] text-slate-300 mb-0.5">
                  <span>Housing & Utilities</span>
                  <span className="font-tabular font-medium">₹18,000 (55%)</span>
                </div>
                <div className="w-full bg-slate-700/60 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-teal-400 h-full rounded-full" style={{ width: '55%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-slate-300 mb-0.5">
                  <span>Groceries & Food</span>
                  <span className="font-tabular font-medium">₹8,400 (26%)</span>
                </div>
                <div className="w-full bg-slate-700/60 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-emerald-400 h-full rounded-full" style={{ width: '26%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* 4. Small AI Coach Insight Pill */}
          <div className="p-3 rounded-xl bg-teal-950/60 border border-teal-500/30 flex items-start gap-2.5 shadow-md">
            <div className="p-1 rounded-lg bg-teal-500/20 text-teal-300 shrink-0 mt-0.5">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-300 block">
                AI Money Coach Insight
              </span>
              <p className="text-[11px] text-slate-200 leading-snug mt-0.5">
                "You're on track to save an extra <span className="font-bold text-teal-200">₹14,500</span> this month by optimizing flexible dining out."
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Footer Note */}
      <div className="relative z-10 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
          <span>Local SQLite Vault</span>
        </div>
        <span className="text-slate-500 text-[11px]">No third-party data tracking</span>
      </div>
    </div>
  );
}
