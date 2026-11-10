import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Trash2,
  Check,
  CreditCard,
  AlertCircle,
  Repeat,
} from 'lucide-react';
import { useFinance } from '../../context/FinanceContext';
import { api } from '../../api/client';
import { formatCurrency, getCategoryColorMap, DEFAULT_EXPENSE_CATEGORIES } from '../../utils/categories';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function Budgets() {
  const { refreshTrigger, triggerRefresh, notify } = useFinance();

  const [loading, setLoading] = useState(true);
  const [budgetsData, setBudgetsData] = useState(null);
  const [bills, setBills] = useState([]);
  const [error, setError] = useState('');

  // Add Budget Form
  const [showAddBudget, setShowAddBudget] = useState(false);
  const [budgetMonth, setBudgetMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [budgetCategory, setBudgetCategory] = useState(DEFAULT_EXPENSE_CATEGORIES[0]);
  const [budgetLimit, setBudgetLimit] = useState('');

  // Add Bill Form
  const [showAddBill, setShowAddBill] = useState(false);
  const [billDesc, setBillDesc] = useState('');
  const [billAmount, setBillAmount] = useState('');
  const [billDueDate, setBillDueDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [billFrequency, setBillFrequency] = useState('Monthly');

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setError('');
      try {
        const [bRes, billsRes] = await Promise.allSettled([
          api.get('/api/budgets'),
          api.get('/api/bills'),
        ]);

        if (!isMounted) return;
        if (bRes.status === 'fulfilled') setBudgetsData(bRes.value);
        if (billsRes.status === 'fulfilled') setBills(billsRes.value || []);
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to load budgets and bills.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [refreshTrigger]);

  const handleCreateBudget = async (e) => {
    e.preventDefault();
    const limit = parseFloat(budgetLimit);
    if (isNaN(limit) || limit < 0) {
      notify('Please enter a valid budget limit.', 'warning');
      return;
    }
    try {
      await api.post('/api/budgets', {
        month: budgetMonth,
        category: budgetCategory,
        limit_amount: limit,
      });
      notify(`Budget of ₹${limit.toLocaleString('en-IN')} saved for ${budgetCategory}.`, 'success');
      setShowAddBudget(false);
      setBudgetLimit('');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to save budget.', 'error');
    }
  };

  const handleDeleteBudget = async (id) => {
    try {
      await api.delete(`/api/budgets/${id}`);
      notify('Budget deleted.', 'success');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to delete budget.', 'error');
    }
  };

  const handleCreateBill = async (e) => {
    e.preventDefault();
    const amt = parseFloat(billAmount);
    if (isNaN(amt) || amt <= 0) {
      notify('Please enter a valid bill amount.', 'warning');
      return;
    }
    try {
      await api.post('/api/bills', {
        description: billDesc.trim(),
        amount: amt,
        due_date: billDueDate,
        frequency: billFrequency,
      });
      notify(`Bill "${billDesc}" scheduled successfully.`, 'success');
      setShowAddBill(false);
      setBillDesc('');
      setBillAmount('');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to save bill.', 'error');
    }
  };

  const handlePayBill = async (id) => {
    try {
      const res = await api.patch(`/api/bills/${id}/pay`);
      notify(res.message || 'Bill marked as paid.', 'success');
      if (res.next_bill_created) {
        notify(res.next_bill_message, 'success');
      }
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to mark bill as paid.', 'error');
    }
  };

  const handleDeleteBill = async (id) => {
    try {
      await api.delete(`/api/bills/${id}`);
      notify('Bill removed.', 'success');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to delete bill.', 'error');
    }
  };

  if (loading && !budgetsData) {
    return <LoadingSpinner text="Loading your monthly budgets and bill schedules..." />;
  }

  const utilization = budgetsData?.utilization || [];
  const budgetsList = budgetsData?.budgets || [];
  const categoryColors = getCategoryColorMap(utilization.map((item) => item.category));

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">Budgets & Bills</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time monthly category limits and recurring obligation tracking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddBudget(true)}
            className="px-4 py-2.5 rounded-2xl border border-teal-500 text-teal-700 hover:bg-teal-50 text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Set Budget
          </button>
          <button
            onClick={() => setShowAddBill(true)}
            className="px-5 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-teal-700/20 active:scale-95 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Add Bill
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* SECTION 1: Monthly Category Budgets */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <PieChart className="w-4 h-4 text-teal-600" /> Monthly Category Budgets
          </h2>
          <span className="text-xs font-semibold text-slate-500">
            Month: {budgetsData?.current_month}
          </span>
        </div>

        {utilization.length === 0 ? (
          <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center text-slate-500 shadow-card">
            <p className="font-semibold text-slate-800 text-sm">No budgets set for this month.</p>
            <p className="text-xs text-slate-400 mt-1">
              Click "+ Set Budget" above to assign limits to your spending categories.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {utilization.map((item) => {
              const categoryColor = categoryColors[item.category];
              let statusColor = 'text-emerald-700 bg-emerald-50 border-emerald-200';
              let statusText = "You're within your budget";
              let barColor = 'bg-emerald-500';

              if (item.status === 'Exceeded') {
                statusColor = 'text-rose-700 bg-rose-50 border-rose-200';
                statusText = "You've exceeded your budget";
                barColor = 'bg-rose-500';
              } else if (item.status === 'Warning') {
                statusColor = 'text-amber-700 bg-amber-50 border-amber-200';
                statusText = "You're approaching your limit";
                barColor = 'bg-amber-500';
              }

              // Match budget row id
              const matchingBudget = budgetsList.find((b) => b.category === item.category);

              return (
                <div
                  key={item.category}
                  className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-card flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: categoryColor }} />
                        {item.category}
                      </span>
                      {matchingBudget && (
                        <button
                          onClick={() => handleDeleteBudget(matchingBudget.id)}
                          className="text-slate-300 hover:text-rose-500 transition-colors p-1"
                          title="Remove Budget"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    <div className="flex items-baseline justify-between mb-2">
                      <span className="text-lg font-extrabold font-tabular" style={{ color: categoryColor }}>
                        {formatCurrency(item.spent)}
                      </span>
                      <span className="text-xs text-slate-500 font-tabular">
                        of {formatCurrency(item.limit_amount)}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-3">
                      <div
                        className={`h-full ${barColor} transition-all duration-500`}
                        style={{ width: `${Math.min(100, item.pct_used)}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${statusColor}`}>
                      {statusText}
                    </span>
                    <span className="text-[11px] font-tabular text-slate-500">
                      {item.remaining > 0 ? `${formatCurrency(item.remaining)} left` : '₹0 left'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: Bills & Recurring Subscriptions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-teal-600" /> Upcoming & Recurring Bills
          </h2>
          <span className="text-xs font-semibold text-slate-500">
            {bills.filter((b) => !b.paid).length} unpaid bills
          </span>
        </div>

        {bills.length === 0 ? (
          <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center text-slate-500 shadow-card">
            <p className="font-semibold text-slate-800 text-sm">No bills recorded.</p>
            <p className="text-xs text-slate-400 mt-1">
              Add recurring rent, electricity, Wi-Fi, or loan EMIs to protect cash automatically.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-card overflow-hidden">
            <div className="divide-y divide-slate-100">
              {bills.map((bill) => (
                <div
                  key={bill.id}
                  className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors ${
                    bill.paid ? 'bg-slate-50/50 opacity-60' : 'hover:bg-slate-50/80'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <button
                      onClick={() => !bill.paid && handlePayBill(bill.id)}
                      disabled={bill.paid}
                      className={`w-7 h-7 rounded-full flex items-center justify-center border transition-all ${
                        bill.paid
                          ? 'bg-emerald-500 border-emerald-500 text-white cursor-default'
                          : 'border-slate-300 hover:border-teal-500 hover:bg-teal-50 text-transparent hover:text-teal-600 cursor-pointer'
                      }`}
                      title={bill.paid ? 'Paid' : 'Click to mark as paid'}
                    >
                      <Check className="w-4 h-4 stroke-[3]" />
                    </button>
                    <div>
                      <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <span className={bill.paid ? 'line-through text-slate-500' : ''}>
                          {bill.description}
                        </span>
                        {bill.frequency !== 'One-time' && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 flex items-center gap-1">
                            <Repeat className="w-2.5 h-2.5" /> {bill.frequency}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" /> Due: {bill.due_date}
                        </span>
                        {bill.next_due_date && (
                          <span className="text-teal-700 font-medium">
                            (Next due: {bill.next_due_date})
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-4 pl-10 sm:pl-0">
                    <span className="text-base font-bold font-mono text-slate-900">
                      {formatCurrency(bill.amount)}
                    </span>
                    {!bill.paid && (
                      <button
                        onClick={() => handlePayBill(bill.id)}
                        className="px-3 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 text-xs font-bold border border-teal-200 transition-colors"
                      >
                        Mark Paid
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteBill(bill.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors"
                      title="Delete bill"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Set Budget Modal */}
      {showAddBudget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Set Category Budget</h3>
            <p className="text-xs text-slate-500 mb-4">Set a spending guardrail for this calendar month.</p>
            <form onSubmit={handleCreateBudget} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Month</label>
                <input
                  type="month"
                  required
                  value={budgetMonth}
                  onChange={(e) => setBudgetMonth(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Category</label>
                <select
                  value={budgetCategory}
                  onChange={(e) => setBudgetCategory(e.target.value)}
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
                <label className="block font-semibold text-slate-700 mb-1">Monthly Limit (₹)</label>
                <input
                  type="number"
                  step="50"
                  min="0"
                  required
                  autoFocus
                  placeholder="e.g. 5000"
                  value={budgetLimit}
                  onChange={(e) => setBudgetLimit(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-base font-bold"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddBudget(false)}
                  className="px-4 py-2 font-semibold text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl font-bold"
                >
                  Save Budget
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Bill Modal */}
      {showAddBill && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Schedule a Bill</h3>
            <p className="text-xs text-slate-500 mb-4">
              FinPilot protects cash for upcoming bills automatically.
            </p>
            <form onSubmit={handleCreateBill} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Bill Name</label>
                <input
                  type="text"
                  required
                  autoFocus
                  placeholder="e.g. Rent, Electricity, Netflix"
                  value={billDesc}
                  onChange={(e) => setBillDesc(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Amount (₹)</label>
                <input
                  type="number"
                  step="1"
                  min="1"
                  required
                  placeholder="e.g. 1500"
                  value={billAmount}
                  onChange={(e) => setBillAmount(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-base font-bold"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Due Date</label>
                <input
                  type="date"
                  required
                  value={billDueDate}
                  onChange={(e) => setBillDueDate(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Frequency</label>
                <select
                  value={billFrequency}
                  onChange={(e) => setBillFrequency(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                >
                  <option value="One-time">One-time</option>
                  <option value="Weekly">Weekly</option>
                  <option value="Monthly">Monthly</option>
                  <option value="Yearly">Yearly</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddBill(false)}
                  className="px-4 py-2 font-semibold text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl font-bold"
                >
                  Save Bill
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
