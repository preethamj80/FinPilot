// Dashboard – Stage 3 Premium Desktop Redesign
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  ShieldAlert,
  Calendar,
  PieChart as PieChartIcon,
  Receipt,
  PlusCircle,
  Plus,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';

import MetricCard from '../../components/common/MetricCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useFinance } from '../../context/FinanceContext';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { formatCurrency, getCategoryColorMap } from '../../utils/categories';

export default function Dashboard() {
  const { refreshTrigger, openAddTx, filterByCategory } = useFinance();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [categoryMix, setCategoryMix] = useState([]);
  const [categoryPeriod] = useState('month'); // Fixed to month for consistency
  const [trend, setTrend] = useState([]);
  const [bills, setBills] = useState([]);
  const [coachInsights, setCoachInsights] = useState([]);
  const [error, setError] = useState('');

  // Date helpers – used for greetings and month labels
  const today = useMemo(() => new Date(), []);
  const currentMonthStr = useMemo(() => today.toISOString().slice(0, 7), [today]);
  const currentMonthName = useMemo(
    () => new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' }).format(today),
    [today]
  );

  const greeting = useMemo(() => {
    const hour = today.getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }, [today]);

  const firstName = useMemo(() => {
    if (user?.full_name) return user.full_name.split(' ')[0];
    return 'there';
  }, [user]);

  // ---------------------------------------------------------------------
  // Load core dashboard data (summary, trend, bills, AI coach)
  // ---------------------------------------------------------------------
  useEffect(() => {
    let mounted = true;
    async function fetchData() {
      setLoading(true);
      setError('');
      try {
        const [sumRes, trendRes, billsRes, coachRes] = await Promise.allSettled([
          api.get('/api/overview/summary'),
          api.get('/api/overview/monthly-trend?last_months=6'),
          api.get('/api/bills'),
          api.get('/api/coach/insights'),
        ]);
        if (!mounted) return;
        if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
        if (trendRes.status === 'fulfilled') setTrend(trendRes.value || []);
        if (billsRes.status === 'fulfilled') setBills(billsRes.value || []);
        if (coachRes.status === 'fulfilled' && coachRes.value?.insights) {
          setCoachInsights(coachRes.value.insights);
        }
      } catch (e) {
        if (mounted) setError(e.message || 'Failed to load dashboard');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchData();
    return () => {
      mounted = false;
    };
  }, [refreshTrigger]);

  // ---------------------------------------------------------------------
  // Load expense‑category breakdown for the current month
  // ---------------------------------------------------------------------
  useEffect(() => {
    let mounted = true;
    async function loadMix() {
      try {
        const endpoint = `/api/overview/category-mix?month=${currentMonthStr}`;
        const data = await api.get(endpoint);
        if (mounted) setCategoryMix(data || []);
      } catch {
        if (mounted) setCategoryMix([]);
      }
    }
    loadMix();
    return () => {
      mounted = false;
    };
  }, [currentMonthStr, refreshTrigger]);

  if (loading && !summary) {
    return <LoadingSpinner text="Loading dashboard…" />;
  }

  // ---------------------------------------------------------------------
  // Derived values – all based on the *same* month for consistency
  // ---------------------------------------------------------------------
  const thisMonthIncome = summary?.current_month_income ?? 0;
  const thisMonthExpenses = summary?.current_month_expenses ?? 0;
  const spendable = summary?.spendable ?? 0;
  const currentCash = summary?.current_cash ?? 0;
  const dailySpendable = Math.round(summary?.daily_spendable || 0);

  // Safe‑to‑spend badge logic (kept from previous version)
  let spendableBadge = 'Comfortable';
  let spendableType = 'teal';
  if (spendable <= 0) {
    spendableBadge = 'Protected Reserve';
    spendableType = 'danger';
  } else if (spendable < 1000) {
    spendableBadge = 'Watch Pace';
    spendableType = 'warning';
  }

  // Total of category expenses for the month – used for percentage calculations
  const categoryTotal = categoryMix.reduce((sum, c) => sum + (c.amount || 0), 0);
  const categoryColors = getCategoryColorMap(categoryMix.map((entry) => entry.category));

  const handleCategoryClick = (cat) => {
    filterByCategory(cat);
    navigate('/transactions');
  };

  // ---------------------------------------------------------------------
  // UI – Premium two‑column desktop layout
  // ---------------------------------------------------------------------
  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12" style={{ backgroundColor: 'var(--color-bg)' }}>
      {/* ==== HERO SECTION ==== */}
      <section className="bg-[var(--color-card-bg)] rounded-2xl p-6 shadow-card flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            {greeting}, {firstName} 👋
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)]">{currentMonthName} snapshot</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => openAddTx('Expense')}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-xl hover:bg-teal-500 transition"
          >
            <PlusCircle className="w-4 h-4" /> Add Expense
          </button>
          <button
            onClick={() => openAddTx('Income')}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl hover:bg-emerald-500 transition"
          >
            <Plus className="w-4 h-4" /> Add Income
          </button>
          <button
            onClick={() => navigate('/budgets')}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-500 transition"
          >
            <PieChartIcon className="w-4 h-4" /> Create Budget
          </button>
          <button
            onClick={() => navigate('/bills')}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-xl hover:bg-cyan-500 transition"
          >
            <Receipt className="w-4 h-4" /> Add Bill
          </button>
        </div>
      </section>

      {/* ==== MAIN TWO‑COLUMN GRID ==== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN – AI Assistant & Category Donut */}
        <div className="lg:col-span-5 space-y-6">
          {/* AI Assistant Panel */}
          <section className="bg-[var(--color-card-bg)] rounded-2xl p-6 shadow-card">
            <h2 className="text-xl font-semibold text-[var(--color-primary-violet)] mb-3">
              Your AI Money Coach
            </h2>
            <p className="text-sm text-[var(--color-text-secondary)] mb-4">
              {greeting}, here’s a quick look at your finances.
            </p>
            {/* Summary line – using data already fetched */}
            <ul className="space-y-2 text-sm text-[var(--color-text-primary)]">
              <li className="flex items-center gap-2"><Wallet className="w-4 h-4 text-[var(--color-sage)]" /> Liquid cash: {formatCurrency(currentCash)}</li>
              <li className="flex items-center gap-2"><TrendingUp className="w-4 h-4 text-[var(--color-positive)]" /> Income this month: {formatCurrency(thisMonthIncome)}</li>
              <li className="flex items-center gap-2"><TrendingDown className="w-4 h-4 text-[var(--color-negative)]" /> Expenses this month: {formatCurrency(thisMonthExpenses)}</li>
              <li className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-[var(--color-gold)]" /> Safe‑to‑spend: {formatCurrency(spendable)}</li>
            </ul>
            {/* Recommendations – first three insights from coach */}
            {coachInsights.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-[var(--color-primary-violet)] mb-2">Recommendations</h3>
                <ul className="flex flex-wrap gap-2">
                  {coachInsights.slice(0, 4).map((insight, idx) => (
                    <button
                      key={idx}
                      onClick={() => navigate(insight.link || '/transactions')}
                      className="px-3 py-1 bg-[var(--color-lavender)] text-[var(--color-text-primary)] rounded-full text-xs hover:bg-[var(--color-primary-violet)] hover:text-[var(--color-sidebar-bg)] transition"
                    >
                      {insight.title}
                    </button>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* Category Spending Donut */}
          <section className="bg-[var(--color-card-bg)] rounded-2xl p-6 shadow-card">
            <h2 className="text-xl font-semibold text-[var(--color-primary-violet)] mb-4">Spending by Category</h2>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={categoryMix}
                  dataKey="amount"
                  nameKey="category"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                >
                  {categoryMix.map((entry, i) => (
                    <Cell
                      key={`cell-${i}`}
                      fill={categoryColors[entry.category]}
                      stroke="var(--color-card-bg)"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <RechartsTooltip
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ backgroundColor: 'var(--color-card-bg)', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-text-primary)' }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Ranked list beside/under the chart */}
            <ul className="mt-4 space-y-2 text-sm">
              {categoryMix.map((cat) => {
                  const pct = categoryTotal ? ((cat.amount / categoryTotal) * 100).toFixed(1) : 0;
                  const color = categoryColors[cat.category];
                  return (
                    <li
                      key={cat.category}
                      className="flex items-center justify-between gap-3 cursor-pointer rounded-lg px-2 py-1.5 hover:bg-[var(--color-elevated-bg)]"
                      onClick={() => handleCategoryClick(cat.category)}
                    >
                      <span className="flex min-w-0 items-center gap-2 text-[var(--color-text-primary)]">
                        <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
                        <span className="truncate">{cat.category}</span>
                      </span>
                      <span className="shrink-0 font-medium tabular-nums" style={{ color }}>
                        {formatCurrency(cat.amount)} ({pct}%)
                      </span>
                    </li>
                  );
                })}
            </ul>
          </section>
        </div>

        {/* RIGHT COLUMN – Financial Overview Panels */}
        <div className="lg:col-span-7 space-y-6">
          {/* Financial Health Cards – reused MetricCard */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <MetricCard
              title="Total Liquid Cash"
              value={formatCurrency(currentCash)}
              subtitle="Cumulative net cash"
              icon={Wallet}
              badgeText={currentCash >= 0 ? 'Positive' : 'Negative'}
              badgeType={currentCash >= 0 ? 'success' : 'danger'}
            />
            <MetricCard
              title="Monthly Income"
              value={formatCurrency(thisMonthIncome)}
              subtitle={`Income for ${currentMonthName.split(' ')[0]}`}
              icon={TrendingUp}
              badgeText="Income"
              badgeType="success"
            />
            <MetricCard
              title="Monthly Expenses"
              value={formatCurrency(thisMonthExpenses)}
              subtitle={`Expenses for ${currentMonthName.split(' ')[0]}`}
              icon={TrendingDown}
              badgeText="Expenses"
              badgeType="warning"
            />
            <MetricCard
              title="Safe to Spend"
              value={formatCurrency(spendable)}
              subtitle={`${dailySpendable.toLocaleString('en-IN')}/day remaining`}
              icon={spendable <= 0 ? ShieldAlert : ShieldCheck}
              badgeText={spendableBadge}
              badgeType={spendableType}
              highlight
            />
          </section>

          {/* Quick Overview – Income vs Expense Bar */}
          <section className="bg-[var(--color-card-bg)] rounded-2xl p-4 shadow-card">
            <h2 className="text-lg font-medium text-[var(--color-primary-violet)] mb-3">Income / Expense Trend (6 months)</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trend.map((t) => ({ name: t.month.slice(5), Income: t.income, Expense: t.expenses }))}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                <XAxis dataKey="name" stroke="var(--color-text-secondary)" />
                <YAxis stroke="var(--color-text-secondary)" />
                <RechartsTooltip contentStyle={{ backgroundColor: 'var(--color-card-bg)', border: 'none' }} formatter={(v) => formatCurrency(v)} />
                <Legend />
                <Bar dataKey="Income" fill="var(--color-emerald)" />
                <Bar dataKey="Expense" fill="var(--color-expense-pink)" />
              </BarChart>
            </ResponsiveContainer>
          </section>

          {/* Savings Goals – placeholder if none */}
          <section className="bg-[var(--color-card-bg)] rounded-2xl p-4 shadow-card">
            <h2 className="text-lg font-medium text-[var(--color-primary-violet)] mb-3">Savings Goals</h2>
            {/* TODO: Replace with real goals endpoint when available */}
            <p className="text-sm text-[var(--color-text-secondary)]">No savings goals configured.</p>
          </section>

          {/* Recent Transactions Table */}
          <section className="bg-[var(--color-card-bg)] rounded-2xl p-4 shadow-card">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-medium text-[var(--color-primary-violet)]">Recent Transactions</h2>
              <button
                onClick={() => navigate('/transactions')}
                className="text-sm text-[var(--color-primary-violet)] hover:underline"
              >
                View all
              </button>
            </div>
            <table className="w-full table-auto text-sm text-[var(--color-text-primary)]">
              <thead className="border-b border-[var(--color-secondary-bg)]">
                <tr>
                  <th className="pb-2 text-left">Date</th>
                  <th className="pb-2 text-left">Description</th>
                  <th className="pb-2 text-left">Category</th>
                  <th className="pb-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {(summary?.recent_transactions || []).slice(0, 5).map((tx, idx) => (
                  <tr key={idx} className="border-b border-[var(--color-secondary-bg)]">
                    <td className="py-2">{new Date(tx.txn_date).toLocaleDateString('en-IN')}</td>
                    <td className="py-2">{tx.description || tx.merchant || '—'}</td>
                    <td className="py-2">{tx.category}</td>
                    <td className="py-2 text-right text-{tx.txn_type === 'Expense' ? 'rose-600' : 'emerald-600'}">
                      {formatCurrency(tx.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* Upcoming Bills */}
          <section className="bg-[var(--color-card-bg)] rounded-2xl p-4 shadow-card">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-medium text-[var(--color-primary-violet)]">Upcoming Bills</h2>
              <button
                onClick={() => navigate('/bills')}
                className="text-sm text-[var(--color-primary-violet)] hover:underline"
              >
                View all
              </button>
            </div>
            <ul className="space-y-2 text-sm">
              {bills
                .filter((b) => !b.paid)
                .slice(0, 4)
                .map((bill, idx) => (
                  <li key={idx} className="flex justify-between">
                    <span>{bill.description}</span>
                    <span>{formatCurrency(bill.amount)} – due {new Date(bill.due_date).toLocaleDateString('en-IN')}</span>
                  </li>
                ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
