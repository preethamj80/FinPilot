import React, { useState, useEffect } from 'react';
import {
  Bot,
  Sparkles,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  DollarSign,
  FileText,
  ShieldAlert,
} from 'lucide-react';
import { useFinance } from '../../context/FinanceContext';
import { api } from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function Coach() {
  const { refreshTrigger, triggerRefresh } = useFinance();
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterPriority, setFilterPriority] = useState('All');

  useEffect(() => {
    let isMounted = true;
    async function loadCoach() {
      setLoading(true);
      setError('');
      try {
        const res = await api.get('/api/coach/insights');
        if (isMounted && res?.insights) {
          setInsights(res.insights);
        }
      } catch (err) {
        if (isMounted) setError(err.message || 'Unable to load AI Money Coach insights.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadCoach();
    return () => {
      isMounted = false;
    };
  }, [refreshTrigger]);

  const filtered =
    filterPriority === 'All'
      ? insights
      : insights.filter((i) => i.priority?.toLowerCase() === filterPriority.toLowerCase());

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 border border-slate-300 text-amber-600 flex items-center justify-center font-bold">
            <Bot className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              AI Money Coach
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Friendly, evidence-backed advice to optimize savings and cut unnecessary expenses.
            </p>
          </div>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-2xl text-xs font-semibold">
          {['All', 'High', 'Medium', 'Low'].map((p) => (
            <button
              key={p}
              onClick={() => setFilterPriority(p)}
              className={`px-3 py-1.5 rounded-xl transition-colors cursor-pointer ${
                filterPriority === p
                  ? 'bg-white text-slate-900 shadow-xs font-bold'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner text="Analyzing your transactions, budgets, and spending habits..." />
      ) : error ? (
        <div role="alert" className="bg-rose-50/50 p-8 rounded-3xl border border-rose-200 text-center shadow-card">
          <ShieldAlert className="w-9 h-9 text-rose-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-900">Unable to load coach insights</h3>
          <p className="text-sm text-slate-300 mt-2">{error}</p>
          <button
            type="button"
            onClick={triggerRefresh}
            className="mt-5 px-4 py-2 rounded-xl bg-teal-600 text-white font-semibold hover:bg-teal-500"
          >
            Try again
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white p-12 rounded-3xl border border-slate-200/80 text-center text-slate-500 shadow-card">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-900">Your finances look well balanced!</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            No urgent alerts found right now. Continue logging your income and expenses to receive personalized savings opportunities.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((item, idx) => {
            const isHigh = item.priority === 'High';
            let badgeBg = isHigh
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : 'bg-slate-100 text-amber-600 border-slate-300';

            return (
              <div
                key={idx}
                className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-card hover:border-amber-600 transition-all space-y-4"
              >
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="p-1.5 rounded-lg bg-slate-100 text-amber-600">
                      <Sparkles className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-600">
                      {item.recommendation_type}
                    </span>
                  </div>
                  <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${badgeBg}`}>
                    {item.priority} Priority
                  </span>
                </div>

                {/* What happened */}
                <div>
                  <h3 className="text-base font-bold text-slate-900 leading-snug">
                    {item.observation}
                  </h3>
                </div>

                {/* Why it matters & What to do */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Why this matters
                    </div>
                    <p className="text-slate-300 leading-relaxed">{item.reason}</p>
                  </div>

                  <div className="p-3.5 bg-slate-100 rounded-xl border border-slate-200">
                    <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-600" /> What you can do
                    </div>
                    <p className="text-slate-200 leading-relaxed">{item.action}</p>
                  </div>
                </div>

                {/* Footer: Potential Savings & Mathematical Evidence */}
                <div className="pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  {item.impact != null && (
                    <div className="flex items-center gap-1.5 font-bold text-emerald-400">
                      <DollarSign className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>Potential Saving: ₹{Number(item.impact).toLocaleString('en-IN')}</span>
                    </div>
                  )}

                  {item.evidence && (
                    <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[11px]">
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>Evidence: {item.evidence}</span>
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                  <span>{item.period}</span>
                  <span>·</span>
                  <span>{item.confidence} confidence</span>
                  <span>·</span>
                  <span className="capitalize">{item.severity}</span>
                  <span>·</span>
                  <span>{item.type === 'ml' ? 'ML assisted' : 'Rule based'}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
