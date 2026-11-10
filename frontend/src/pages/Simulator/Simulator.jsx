import React, { useState } from 'react';
import {
  ShoppingBag,
  Scissors,
  TrendingDown,
  PiggyBank,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  Info,
} from 'lucide-react';
import { api } from '../../api/client';
import { formatCurrency, DEFAULT_EXPENSE_CATEGORIES } from '../../utils/categories';

const SCENARIOS = [
  {
    id: 'purchase',
    title: 'Can I afford this purchase?',
    desc: 'Test a major one-time expense and check if your cash and budget can safely handle it.',
    icon: ShoppingBag,
    color: 'text-blue-600 bg-blue-50 border-blue-200',
  },
  {
    id: 'expense',
    title: 'What if I reduce my expenses?',
    desc: 'See how cutting spending by 10% to 50% in a category builds your extra savings.',
    icon: Scissors,
    color: 'text-teal-600 bg-teal-50 border-teal-200',
  },
  {
    id: 'income',
    title: 'What if my income decreases?',
    desc: 'See what happens if your income drops and how many months your emergency savings last.',
    icon: TrendingDown,
    color: 'text-amber-600 bg-amber-50 border-amber-200',
  },
  {
    id: 'savings',
    title: 'How much could I save?',
    desc: 'Set a monthly savings goal and calculate your accumulated wealth over 6 to 36 months.',
    icon: PiggyBank,
    color: 'text-emerald-600 bg-emerald-50 border-emerald-200',
  },
];

export default function Simulator() {
  const [activeScenario, setActiveScenario] = useState('purchase');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Scenario 1: Major Purchase
  const [purchaseAmount, setPurchaseAmount] = useState('15000');
  const [purchaseCategory, setPurchaseCategory] = useState('Shopping');

  // Scenario 2: Expense Reduction
  const [reductionCategory, setReductionCategory] = useState('Food & Dining');
  const [reductionPct, setReductionPct] = useState(25);
  const [reductionMonths, setReductionMonths] = useState(6);

  // Scenario 3: Income Reduction
  const [incomeCutPct, setIncomeCutPct] = useState(15);
  const [incomeCutMonths, setIncomeCutMonths] = useState(6);

  // Scenario 4: Monthly Savings
  const [savingsContribution, setSavingsContribution] = useState('5000');
  const [savingsDuration, setSavingsDuration] = useState(12);

  const handleSimulate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      let res;
      if (activeScenario === 'purchase') {
        res = await api.post('/api/simulator/major-purchase', {
          purchase_amount: parseFloat(purchaseAmount),
          category: purchaseCategory,
        });
      } else if (activeScenario === 'expense') {
        res = await api.post('/api/simulator/expense-reduction', {
          category: reductionCategory,
          reduction_pct: parseFloat(reductionPct),
          duration_months: parseInt(reductionMonths, 10),
        });
      } else if (activeScenario === 'income') {
        res = await api.post('/api/simulator/income-reduction', {
          reduction_pct: parseFloat(incomeCutPct),
          duration_months: parseInt(incomeCutMonths, 10),
        });
      } else if (activeScenario === 'savings') {
        res = await api.post('/api/simulator/monthly-savings', {
          monthly_contribution: parseFloat(savingsContribution),
          duration_months: parseInt(savingsDuration, 10),
        });
      }
      setResult(res?.result);
    } catch (err) {
      setError(err.message || 'Simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card">
        <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
          Future Decision Planner
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Test purchases and money decisions safely before spending real money.
        </p>
      </div>

      {/* 4 Scenario Cards Selector */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {SCENARIOS.map((sc) => {
          const Icon = sc.icon;
          const isSelected = activeScenario === sc.id;
          return (
            <div
              key={sc.id}
              onClick={() => {
                setActiveScenario(sc.id);
                setResult(null);
                setError('');
              }}
              className={`p-5 sm:p-6 rounded-3xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-white border-teal-500 ring-2 ring-teal-500/20 shadow-card'
                  : 'bg-white border-slate-200/80 hover:border-slate-300 hover:shadow-card'
              }`}
            >
              <div>
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center mb-3.5 border ${sc.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1 leading-snug">{sc.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{sc.desc}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-xs font-bold text-teal-600">
                <span>{isSelected ? 'Selected' : 'Test this'}</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive Controls & Live Verdict */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card">
          <h2 className="text-base font-bold text-slate-900 mb-4">Your Plan Details</h2>

          <form onSubmit={handleSimulate} className="space-y-4 text-xs">
            {/* Scenario 1: Major Purchase Inputs */}
            {activeScenario === 'purchase' && (
              <>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    How much does it cost? (₹)
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={purchaseAmount}
                    onChange={(e) => setPurchaseAmount(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold outline-hidden focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Which category does it belong to?
                  </label>
                  <select
                    value={purchaseCategory}
                    onChange={(e) => setPurchaseCategory(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                  >
                    {DEFAULT_EXPENSE_CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {/* Scenario 2: Expense Reduction Inputs */}
            {activeScenario === 'expense' && (
              <>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Which category do you want to cut?
                  </label>
                  <select
                    value={reductionCategory}
                    onChange={(e) => setReductionCategory(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                  >
                    {DEFAULT_EXPENSE_CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Reduction percentage:</span>
                    <span className="font-bold text-teal-600">{reductionPct}%</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="75"
                    step="5"
                    value={reductionPct}
                    onChange={(e) => setReductionPct(e.target.value)}
                    className="w-full accent-teal-600 cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Duration (months)</label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={reductionMonths}
                    onChange={(e) => setReductionMonths(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
                  />
                </div>
              </>
            )}

            {/* Scenario 3: Income Reduction Inputs */}
            {activeScenario === 'income' && (
              <>
                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Expected Income Reduction:</span>
                    <span className="font-bold text-rose-600">{incomeCutPct}%</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="5"
                    value={incomeCutPct}
                    onChange={(e) => setIncomeCutPct(e.target.value)}
                    className="w-full accent-rose-500 cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Duration (months)</label>
                  <input
                    type="number"
                    min="1"
                    max="36"
                    value={incomeCutMonths}
                    onChange={(e) => setIncomeCutMonths(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
                  />
                </div>
              </>
            )}

            {/* Scenario 4: Monthly Savings Inputs */}
            {activeScenario === 'savings' && (
              <>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Monthly savings contribution (₹)
                  </label>
                  <input
                    type="number"
                    min="500"
                    step="500"
                    value={savingsContribution}
                    onChange={(e) => setSavingsContribution(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Duration (months)</label>
                  <select
                    value={savingsDuration}
                    onChange={(e) => setSavingsDuration(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                  >
                    <option value="6">6 Months</option>
                    <option value="12">1 Year (12 Months)</option>
                    <option value="24">2 Years (24 Months)</option>
                    <option value="36">3 Years (36 Months)</option>
                  </select>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-teal-600 hover:bg-teal-500 text-white rounded-xl font-bold shadow-md shadow-teal-700/20 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Calculating Impact...
                </>
              ) : (
                'Check Financial Impact'
              )}
            </button>
          </form>
        </div>

        {/* Results Column (7 cols) */}
        <div className="lg:col-span-7 bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900">Estimated Outcome</h2>
              <span className="text-[11px] text-slate-400 flex items-center gap-1">
                <Info className="w-3.5 h-3.5" /> Estimates only · No real money changed
              </span>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs mb-4">
                {error}
              </div>
            )}

            {!result ? (
              <div className="py-16 text-center text-slate-400">
                <p className="text-sm font-semibold text-slate-700">No calculation yet.</p>
                <p className="text-xs mt-1">
                  Fill in your details on the left and click "Check Financial Impact" to view results.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Verdict Box */}
                <div
                  className={`p-4 rounded-xl border text-sm font-semibold leading-relaxed flex items-start gap-3 ${
                    result.status_color === 'danger'
                      ? 'bg-rose-50 border-rose-200 text-rose-800'
                      : result.status_color === 'warning'
                      ? 'bg-amber-50 border-amber-200 text-amber-800'
                      : 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  }`}
                >
                  {result.status_color === 'danger' ? (
                    <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                  ) : result.status_color === 'warning' ? (
                    <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="font-bold mb-0.5">{result.status || 'Analysis Result'}</div>
                    <div className="text-xs font-normal">{result.verdict}</div>
                  </div>
                </div>

                {/* Scenario Metrics Comparison */}
                {activeScenario === 'purchase' && (
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="text-slate-500 mb-1">Liquid Cash Today</div>
                      <div className="text-base font-bold text-slate-900">
                        {formatCurrency(result.baseline_cash)}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="text-slate-500 mb-1">Cash After Purchase</div>
                      <div
                        className={`text-base font-bold ${
                          result.simulated_cash < 0 ? 'text-rose-600' : 'text-slate-900'
                        }`}
                      >
                        {formatCurrency(result.simulated_cash)}
                      </div>
                    </div>
                  </div>
                )}

                {activeScenario === 'expense' && (
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="text-slate-500 mb-1">Monthly Savings</div>
                      <div className="text-base font-bold text-teal-700">
                        +{formatCurrency(result.monthly_savings)}/mo
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="text-slate-500 mb-1">Total Accumulated</div>
                      <div className="text-base font-bold text-emerald-700">
                        {formatCurrency(result.cumulative_savings)}
                      </div>
                    </div>
                  </div>
                )}

                {activeScenario === 'income' && (
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="text-slate-500 mb-1">Revised Monthly Net Cashflow</div>
                      <div
                        className={`text-base font-bold ${
                          result.revised_net_cashflow < 0 ? 'text-rose-600' : 'text-slate-900'
                        }`}
                      >
                        {formatCurrency(result.revised_net_cashflow)}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="text-slate-500 mb-1">Total Income Difference</div>
                      <div className="text-base font-bold text-rose-600">
                        -{formatCurrency(result.cumulative_income_loss)}
                      </div>
                    </div>
                  </div>
                )}

                {activeScenario === 'savings' && (
                  <div className="p-4 bg-teal-50/50 rounded-xl border border-teal-200 text-xs">
                    <div className="text-teal-900 font-semibold mb-1">Projected Savings Pool:</div>
                    <div className="text-2xl font-extrabold text-teal-700">
                      {formatCurrency(result.projected_savings_pool)}
                    </div>
                    <p className="text-[11px] text-teal-800 mt-1">
                      In {result.duration_months} months by depositing {formatCurrency(result.monthly_contribution)} every month.
                    </p>
                  </div>
                )}

                {/* Audit Assumptions List */}
                {result.assumptions && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Underlying Audit Calculations:
                    </div>
                    <ul className="text-[11px] text-slate-600 space-y-0.5 list-disc pl-4">
                      {result.assumptions.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
