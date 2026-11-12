import React, { useState, useEffect } from 'react';
import { Sparkles, ArrowRight, Check, X, Wallet, TrendingUp, PiggyBank, PieChart, Plus } from 'lucide-react';
import { api } from '../../api/client';
import { useFinance } from '../../context/FinanceContext';
import { DEFAULT_EXPENSE_CATEGORIES } from '../../utils/categories';
import { DEMO_MODE } from '../../demo/demoMode';

export default function OnboardingModal() {
  const { triggerRefresh, notify } = useFinance();
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(1);

  // Form states
  const [openingBalance, setOpeningBalance] = useState('');
  const [incomeAmount, setIncomeAmount] = useState('');
  const [incomeSource, setIncomeSource] = useState('Salary');
  const [savingsTarget, setSavingsTarget] = useState('');
  const [firstBudgetCat, setFirstBudgetCat] = useState('Food & Dining');
  const [firstBudgetLimit, setFirstBudgetLimit] = useState('');

  useEffect(() => {
    if (DEMO_MODE) return;
    // Check if onboarding completed for this user
    const completed = localStorage.getItem('finpilot_onboarding_completed');
    if (!completed) {
      setIsOpen(true);
    }
  }, []);

  const handleFinish = async () => {
    // Save settings if provided
    try {
      const ob = parseFloat(openingBalance) || 0;
      const st = parseFloat(savingsTarget) || 0;
      if (ob > 0 || st > 0) {
        await api.put('/api/settings', {
          opening_balance: ob,
          safety_reserve: 2000,
          monthly_savings_target: st,
        });
      }

      // Add starting income transaction if provided
      const inc = parseFloat(incomeAmount);
      if (!isNaN(inc) && inc > 0) {
        await api.post('/api/transactions', {
          txn_date: new Date().toISOString().split('T')[0],
          txn_type: 'Income',
          description: `Starting ${incomeSource}`,
          amount: inc,
          category: incomeSource,
          notes: 'Added during onboarding',
        });
      }

      // Add first budget if provided
      const bLimit = parseFloat(firstBudgetLimit);
      if (!isNaN(bLimit) && bLimit > 0) {
        const month = new Date().toISOString().slice(0, 7);
        await api.post('/api/budgets', {
          month,
          category: firstBudgetCat,
          limit_amount: bLimit,
        });
      }

      notify('Welcome to FinPilot! Your finances are set up.', 'success');
      triggerRefresh();
    } catch {
      // Continue anyway
    } finally {
      localStorage.setItem('finpilot_onboarding_completed', 'true');
      setIsOpen(false);
    }
  };

  const handleSkip = () => {
    localStorage.setItem('finpilot_onboarding_completed', 'true');
    setIsOpen(false);
  };

  if (!isOpen || DEMO_MODE) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 animate-scale-up relative">
        <button
          onClick={handleSkip}
          className="absolute right-5 top-5 p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
          title="Skip onboarding"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Step Indicator */}
        <div className="flex items-center gap-1.5 mb-6">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`h-1.5 rounded-full flex-1 transition-all ${
                s <= step ? 'bg-teal-500' : 'bg-slate-100'
              }`}
            />
          ))}
        </div>

        {/* STEP 1: Welcome & Starting Balance */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center mb-2">
              <Wallet className="w-6 h-6 text-teal-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">Welcome to FinPilot!</h2>
            <p className="text-xs text-slate-500 leading-relaxed">
              Let's personalize your Safe-to-Spend engine in less than a minute. What is your current available bank balance across savings and checking accounts?
            </p>
            <div className="relative pt-2">
              <span className="absolute left-3.5 top-5 text-slate-400 font-bold text-lg">₹</span>
              <input
                type="number"
                min="0"
                autoFocus
                placeholder="e.g. 25000"
                value={openingBalance}
                onChange={(e) => setOpeningBalance(e.target.value)}
                className="w-full pl-8 pr-4 py-3 rounded-xl border border-slate-300 text-lg font-bold text-slate-900 outline-hidden focus:border-teal-500"
              />
            </div>
          </div>
        )}

        {/* STEP 2: Monthly Income */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center mb-2">
              <TrendingUp className="w-6 h-6 text-emerald-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">Monthly Inflow</h2>
            <p className="text-xs text-slate-500 leading-relaxed">
              How much money do you typically earn or receive each month? We use this to calculate monthly cashflow trends.
            </p>
            <div className="space-y-3 pt-2 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Estimated Monthly Income (₹)</label>
                <input
                  type="number"
                  min="0"
                  autoFocus
                  placeholder="e.g. 50000"
                  value={incomeAmount}
                  onChange={(e) => setIncomeAmount(e.target.value)}
                  className="w-full p-3 rounded-xl border border-slate-300 text-base font-bold text-slate-900 outline-hidden focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Primary Source</label>
                <select
                  value={incomeSource}
                  onChange={(e) => setIncomeSource(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 bg-white"
                >
                  <option value="Salary">Salary (Full-time)</option>
                  <option value="Freelance">Freelance / Contract</option>
                  <option value="Business Income">Business / Trade</option>
                  <option value="Other Income">Other / Allowance</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Monthly Savings Target */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center mb-2">
              <PiggyBank className="w-6 h-6 text-teal-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">Monthly Savings Goal</h2>
            <p className="text-xs text-slate-500 leading-relaxed">
              How much would you like to protect and save each month before calculating daily spendable cash? (Leave 0 to skip).
            </p>
            <div className="relative pt-2">
              <span className="absolute left-3.5 top-5 text-slate-400 font-bold text-lg">₹</span>
              <input
                type="number"
                min="0"
                autoFocus
                placeholder="e.g. 5000"
                value={savingsTarget}
                onChange={(e) => setSavingsTarget(e.target.value)}
                className="w-full pl-8 pr-4 py-3 rounded-xl border border-slate-300 text-lg font-bold text-slate-900 outline-hidden focus:border-teal-500"
              />
            </div>
          </div>
        )}

        {/* STEP 4: First Category Budget */}
        {step === 4 && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-700 flex items-center justify-center mb-2">
              <PieChart className="w-6 h-6 text-indigo-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">Your First Spending Budget</h2>
            <p className="text-xs text-slate-500 leading-relaxed">
              Pick your most frequent expense category (like Dining or Groceries) and set a monthly spending cap.
            </p>
            <div className="space-y-3 pt-2 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Category</label>
                <select
                  value={firstBudgetCat}
                  onChange={(e) => setFirstBudgetCat(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 bg-white"
                >
                  {DEFAULT_EXPENSE_CATEGORIES.slice(0, 8).map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Monthly Spending Limit (₹)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 4000"
                  value={firstBudgetLimit}
                  onChange={(e) => setFirstBudgetLimit(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-base font-bold text-slate-900 outline-hidden focus:border-teal-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Modal Footer Controls */}
        <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between">
          <button
            type="button"
            onClick={handleSkip}
            className="text-xs font-semibold text-slate-400 hover:text-slate-600"
          >
            Skip for now
          </button>

          <div className="flex items-center gap-2">
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Back
              </button>
            )}

            {step < 4 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-teal-700/20"
              >
                Continue <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinish}
                className="px-6 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md shadow-teal-700/30"
              >
                Launch Dashboard <Check className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
