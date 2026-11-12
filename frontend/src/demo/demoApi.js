import { DEFAULT_EXPENSE_CATEGORIES } from '../utils/categories.js';

const MONEY = {
  'Rent & Housing': 22000,
  Groceries: 6800,
  'Food & Dining': 5200,
  Transportation: 2900,
  Utilities: 2300,
  'Health & Medical': 1600,
  Shopping: 4100,
  Education: 1500,
  Entertainment: 1900,
  Travel: 3400,
  Insurance: 2400,
};

const EXAMPLES = {
  'Rent & Housing': ['Apartment rent'],
  Groceries: ['Fresh market', 'Weekly groceries'],
  'Food & Dining': ['Cafe breakfast', 'Swiggy dinner'],
  Transportation: ['Metro card', 'Ride share'],
  Utilities: ['Electricity bill', 'Home internet'],
  'Health & Medical': ['Pharmacy', 'Wellness check'],
  Shopping: ['Home essentials', 'Bookstore'],
  Education: ['Online course'],
  Entertainment: ['Cinema tickets'],
  Travel: ['Weekend train trip'],
  Insurance: ['Health cover premium'],
};

const monthKey = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
const dateString = (date) => {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 10);
};
const rounded = (value) => Math.round(value * 100) / 100;
const clone = (value) => structuredClone(value);

function createSeedTransactions() {
  const now = new Date();
  const rows = [];
  let id = 1;

  // Synthetic examples across six months make trend and optimizer views useful.
  for (let offset = 5; offset >= 0; offset -= 1) {
    const first = new Date(now.getFullYear(), now.getMonth() - offset, 1);
    const monthMultiplier = 0.92 + ((5 - offset) % 4) * 0.045;
    const add = (day, txnType, description, amount, category, notes = '') => {
      const date = new Date(first.getFullYear(), first.getMonth(), Math.min(day, offset === 0 ? now.getDate() : 28));
      rows.push({ id: id++, txn_date: dateString(date), txn_type: txnType, description, amount, category, notes });
    };

    add(1, 'Income', 'Monthly salary', 86000, 'Salary', 'Synthetic demo entry');
    if (offset % 2 === 0) add(12, 'Income', 'Design project payment', 12000, 'Freelance', 'Synthetic demo entry');

    for (const [index, category] of DEFAULT_EXPENSE_CATEGORIES.entries()) {
      const baseline = MONEY[category];
      if (!baseline || (category === 'Travel' && offset % 3 === 1)) continue;
      const amount = rounded(baseline * monthMultiplier * (category === 'Shopping' && offset === 2 ? 2.6 : 1));
      const descriptions = EXAMPLES[category];
      add(3 + ((index * 2 + offset) % 18), 'Expense', descriptions[(index + offset) % descriptions.length], amount, category, 'Synthetic demo entry');
    }
  }
  return rows.sort((a, b) => b.txn_date.localeCompare(a.txn_date) || b.id - a.id);
}

function createStore() {
  const transactions = createSeedTransactions();
  const currentMonth = monthKey(new Date());
  const monthlySpending = new Map();
  transactions.filter((item) => item.txn_type === 'Expense' && item.txn_date.slice(0, 7) === currentMonth)
    .forEach((item) => monthlySpending.set(item.category, (monthlySpending.get(item.category) || 0) + item.amount));

  const budgets = [...monthlySpending.entries()].map(([category, spent], index) => ({
    id: index + 1,
    month: currentMonth,
    category,
    limit_amount: Math.ceil(spent * 1.18 / 500) * 500,
  }));
  const now = new Date();
  const due = (days) => dateString(new Date(now.getFullYear(), now.getMonth(), now.getDate() + days));

  return {
    transactions,
    budgets,
    bills: [
      { id: 1, description: 'Electricity & utilities', amount: 1850, due_date: due(4), paid: 0, frequency: 'Monthly', next_due_date: '' },
      { id: 2, description: 'Home internet', amount: 999, due_date: due(9), paid: 0, frequency: 'Monthly', next_due_date: '' },
      { id: 3, description: 'Streaming subscription', amount: 649, due_date: due(16), paid: 0, frequency: 'Monthly', next_due_date: '' },
    ],
    settings: { opening_balance: 48000, safety_reserve: 15000, monthly_savings_target: 9000 },
    locks: {},
    history: [],
    nextTransactionId: Math.max(...transactions.map((row) => row.id)) + 1,
    nextBudgetId: budgets.length + 1,
    nextBillId: 4,
    nextOptimizationId: 1,
  };
}

let store = createStore();

function txFilters(searchParams) {
  return store.transactions.filter((row) => {
    const needle = (searchParams.get('search') || '').toLowerCase();
    if (needle && !`${row.description} ${row.category} ${row.notes}`.toLowerCase().includes(needle)) return false;
    if (searchParams.has('txn_type') && searchParams.get('txn_type') !== 'All' && row.txn_type !== searchParams.get('txn_type')) return false;
    if (searchParams.has('category') && searchParams.get('category') !== 'All' && row.category !== searchParams.get('category')) return false;
    if (searchParams.has('start_date') && row.txn_date < searchParams.get('start_date')) return false;
    if (searchParams.has('end_date') && row.txn_date > searchParams.get('end_date')) return false;
    return true;
  });
}

function monthSpend(month) {
  const sums = new Map();
  store.transactions.filter((row) => row.txn_type === 'Expense' && row.txn_date.slice(0, 7) === month)
    .forEach((row) => sums.set(row.category, (sums.get(row.category) || 0) + Number(row.amount)));
  return sums;
}

function summary() {
  const income = store.transactions.filter((row) => row.txn_type === 'Income').reduce((sum, row) => sum + Number(row.amount), 0);
  const expenses = store.transactions.filter((row) => row.txn_type === 'Expense').reduce((sum, row) => sum + Number(row.amount), 0);
  const currentMonth = monthKey(new Date());
  const monthRows = store.transactions.filter((row) => row.txn_date.slice(0, 7) === currentMonth);
  const currentMonthIncome = monthRows.filter((row) => row.txn_type === 'Income').reduce((sum, row) => sum + Number(row.amount), 0);
  const currentMonthExpenses = monthRows.filter((row) => row.txn_type === 'Expense').reduce((sum, row) => sum + Number(row.amount), 0);
  const unpaid = store.bills.filter((bill) => !bill.paid);
  const upcomingTotal = unpaid.reduce((sum, bill) => sum + Number(bill.amount), 0);
  const currentBudgets = store.budgets.filter((budget) => budget.month === currentMonth);
  const spending = monthSpend(currentMonth);
  const budgetLimit = currentBudgets.reduce((sum, budget) => sum + Number(budget.limit_amount), 0);
  const budgetSpent = currentBudgets.reduce((sum, budget) => sum + (spending.get(budget.category) || 0), 0);
  const currentCash = store.settings.opening_balance + income - expenses;
  const spendable = currentCash - upcomingTotal - store.settings.safety_reserve - store.settings.monthly_savings_target;
  const daysLeft = Math.max(1, new Date(nowYear(), nowMonth() + 1, 0).getDate() - new Date().getDate() + 1);
  return {
    current_cash: rounded(currentCash), opening_balance: store.settings.opening_balance,
    total_income: rounded(income), total_expenses: rounded(expenses), upcoming_bills_total: rounded(upcomingTotal),
    upcoming_bills_list: unpaid.map(({ description, amount, due_date }) => ({ description, amount, due_date })),
    safety_reserve: store.settings.safety_reserve, monthly_savings_target: store.settings.monthly_savings_target,
    uncommitted_cash: rounded(currentCash - upcomingTotal), has_budgets: currentBudgets.length > 0,
    total_budget_limit: rounded(budgetLimit), total_budget_spent: rounded(budgetSpent),
    remaining_budget_headroom: rounded(budgetLimit - budgetSpent), spendable: rounded(spendable),
    daily_spendable: rounded(spendable / daysLeft), weekly_spendable: rounded(spendable / daysLeft * Math.min(7, daysLeft)),
    days_left: daysLeft, as_of_date: dateString(new Date()), assumptions: ['Illustrative synthetic data for demonstration only.'],
    current_month_income: rounded(currentMonthIncome), current_month_expenses: rounded(currentMonthExpenses), current_month: currentMonth,
    recent_transactions: store.transactions.slice(0, 20),
  };
}

const nowYear = () => new Date().getFullYear();
const nowMonth = () => new Date().getMonth();

function categoryMix(month) {
  const totals = new Map();
  store.transactions.filter((row) => row.txn_type === 'Expense' && (!month || month === 'all' || row.txn_date.slice(0, 7) === month))
    .forEach((row) => totals.set(row.category, (totals.get(row.category) || 0) + Number(row.amount)));
  return [...totals.entries()].map(([category, amount]) => ({ category, amount: rounded(amount) })).sort((a, b) => b.amount - a.amount);
}

function monthlyTrend(count = 6) {
  return Array.from({ length: Math.min(12, Number(count) || 6) }, (_, index) => {
    const date = new Date(nowYear(), nowMonth() - (Math.min(12, Number(count) || 6) - 1 - index), 1);
    const month = monthKey(date);
    const rows = store.transactions.filter((row) => row.txn_date.slice(0, 7) === month);
    const income = rows.filter((row) => row.txn_type === 'Income').reduce((sum, row) => sum + Number(row.amount), 0);
    const expenses = rows.filter((row) => row.txn_type === 'Expense').reduce((sum, row) => sum + Number(row.amount), 0);
    return { month, income: rounded(income), expenses: rounded(expenses), net: rounded(income - expenses) };
  });
}

function coachInsights() {
  const mix = categoryMix(monthKey(new Date()));
  const top = mix[0] || { category: 'Groceries', amount: 0 };
  const period = monthKey(new Date());
  return {
    generated_at: new Date().toISOString(),
    insights: [
      { recommendation_type: 'Cashflow overview', priority: 'Low', observation: 'Your sample income is ahead of expenses this month.', reason: 'The example ledger includes a steady monthly salary and keeps spending below income.', action: 'Keep your savings target protected before discretionary purchases.', impact: 9000, evidence: 'Illustrative synthetic demo transactions', period, confidence: 'Illustrative', type: 'rule', severity: 'success' },
      { recommendation_type: 'Category review', priority: 'Medium', observation: `${top.category} is the largest category in this sample month.`, reason: 'Reviewing your largest spending area can make a budget easier to maintain.', action: `Compare ${top.category} purchases against your monthly limit.`, impact: Math.round(top.amount * 0.08), evidence: `${top.category}: ₹${Math.round(top.amount).toLocaleString('en-IN')} in synthetic entries`, period, confidence: 'Illustrative', type: 'rule', severity: 'info' },
      { recommendation_type: 'Bill planning', priority: 'Low', observation: 'A few upcoming sample bills are scheduled this month.', reason: 'Planning around due dates helps preserve your cash buffer.', action: 'Review the Bills panel and mark sample bills paid as you explore.', impact: 0, evidence: `${store.bills.filter((bill) => !bill.paid).length} synthetic bills`, period, confidence: 'Illustrative', type: 'rule', severity: 'info' },
    ],
  };
}

function budgetView() {
  const month = monthKey(new Date());
  const budgets = store.budgets.filter((row) => row.month === month).sort((a, b) => a.id - b.id);
  const spent = monthSpend(month);
  const utilization = budgets.map((budget) => {
    const used = rounded(spent.get(budget.category) || 0);
    const limit = Number(budget.limit_amount);
    const pct = limit > 0 ? rounded(used / limit * 100) : 0;
    return { category: budget.category, limit_amount: limit, spent: used, remaining: rounded(limit - used), pct_used: pct, status: pct >= 100 ? 'Exceeded' : pct >= 80 ? 'Warning' : 'Within Budget' };
  });
  return { budgets: clone(budgets), utilization, current_month: month };
}

function recommendations(savingsTarget) {
  const currentMonth = monthKey(new Date());
  const pastMonths = Array.from({ length: 3 }, (_, index) => monthKey(new Date(nowYear(), nowMonth() - index - 1, 1)));
  const monthly = new Map();
  let incomeTotal = 0;
  for (const month of pastMonths) {
    const rows = store.transactions.filter((row) => row.txn_date.slice(0, 7) === month);
    incomeTotal += rows.filter((row) => row.txn_type === 'Income').reduce((sum, row) => sum + Number(row.amount), 0);
    for (const row of rows.filter((item) => item.txn_type === 'Expense')) {
      const key = `${month}|${row.category}`;
      monthly.set(key, (monthly.get(key) || 0) + Number(row.amount));
    }
  }
  const averageIncome = incomeTotal / pastMonths.length;
  const sums = new Map();
  for (const [key, amount] of monthly.entries()) {
    const category = key.slice(key.indexOf('|') + 1);
    sums.set(category, (sums.get(category) || 0) + amount / pastMonths.length);
  }
  const target = savingsTarget == null ? store.settings.monthly_savings_target || averageIncome * 0.1 : Number(savingsTarget);
  const essential = new Set(['Rent & Housing', 'Utilities', 'Insurance', 'Health & Medical']);
  const totalSpending = [...sums.values()].reduce((sum, amount) => sum + amount, 0);
  const roomForSpending = Math.max(0, averageIncome - target);
  const reductionNeeded = Math.max(0, totalSpending - roomForSpending);
  const flexible = [...sums.entries()].filter(([category]) => !essential.has(category)).reduce((sum, [, amount]) => sum + amount, 0);
  const locks = store.locks[currentMonth] || {};
  return [...sums.entries()].map(([category, average]) => {
    const current = store.budgets.find((row) => row.month === currentMonth && row.category === category);
    const locked = Object.prototype.hasOwnProperty.call(locks, category);
    const lockedLimit = locks[category];
    const recommended = locked ? lockedLimit : essential.has(category)
      ? (current?.limit_amount ?? average)
      : Math.max(0, average - (flexible ? reductionNeeded * average / flexible : 0));
    const reduction = Math.max(0, average - recommended);
    return {
      category,
      current_limit: current?.limit_amount ?? null,
      recommended_limit: rounded(recommended),
      reason: locked ? `Locked at ₹${Number(lockedLimit).toLocaleString('en-IN')} for this demo.` : essential.has(category) ? 'Essential category held steady in this illustrative plan.' : `Sample history suggests a flexible monthly amount near ₹${Math.round(recommended).toLocaleString('en-IN')}.`,
      impact_estimate: rounded(reduction),
      confidence: 'Illustrative',
      locked,
    };
  }).sort((a, b) => b.impact_estimate - a.impact_estimate);
}

function createOptimization(savingsTarget) {
  const month = monthKey(new Date());
  const item = {
    optimization_id: store.nextOptimizationId++,
    month,
    recommendations: recommendations(savingsTarget),
    generated_at: new Date().toISOString(),
    status: 'pending',
    savings_target: savingsTarget == null ? store.settings.monthly_savings_target : Number(savingsTarget),
    unpaid_bills: store.bills.filter((bill) => !bill.paid).map(({ description, amount, due_date }) => ({ description, amount, due_date })),
    previous_budgets: null,
  };
  store.history.unshift(item);
  return clone(item);
}

function detectCategory(description, txnType = 'Expense') {
  if (txnType === 'Income') return /freelance|project/i.test(description) ? 'Freelance' : 'Salary';
  const lower = description.toLowerCase();
  const rules = [
    [/rent|apartment|housing|mortgage/, 'Rent & Housing'], [/grocery|market|vegetable/, 'Groceries'],
    [/swiggy|restaurant|cafe|food|dining/, 'Food & Dining'], [/uber|metro|taxi|fuel|transport/, 'Transportation'],
    [/electric|internet|utility|water/, 'Utilities'], [/doctor|pharmacy|health|medical/, 'Health & Medical'],
    [/book|course|tuition|education/, 'Education'], [/flight|hotel|travel|train trip/, 'Travel'],
    [/movie|cinema|concert|entertainment/, 'Entertainment'], [/insurance|premium/, 'Insurance'],
    [/shopping|store|amazon/, 'Shopping'],
  ];
  return rules.find(([pattern]) => pattern.test(lower))?.[1] || 'Miscellaneous';
}

function makeSimulation(kind, payload) {
  const safe = summary().spendable;
  const duration = Number(payload.duration_months || 12);
  if (kind === 'major-purchase') {
    const purchase = Number(payload.purchase_amount || 0);
    const remainder = safe - purchase;
    return { status: remainder > 0 ? 'Within the sample buffer' : 'Would use the sample reserve', status_color: remainder > 5000 ? 'success' : remainder > 0 ? 'warning' : 'danger', verdict: `After a ₹${purchase.toLocaleString('en-IN')} purchase, illustrative spendable cash would be ₹${Math.round(remainder).toLocaleString('en-IN')}.`, baseline_cash: safe, simulated_cash: remainder, assumptions: ['Synthetic demo balances only; this is not financial advice.'] };
  }
  if (kind === 'expense-reduction') {
    const current = categoryMix(monthKey(new Date())).find((row) => row.category === payload.category)?.amount || 0;
    const monthly = current * Number(payload.reduction_pct || 0) / 100;
    return { status: 'Illustrative savings projection', status_color: 'success', verdict: `Reducing sample ${payload.category} spending by ${payload.reduction_pct}% could free about ₹${Math.round(monthly).toLocaleString('en-IN')} per month.`, monthly_savings: monthly, cumulative_savings: monthly * duration, duration_months: duration, assumptions: ['Based on synthetic sample spending.'] };
  }
  if (kind === 'income-reduction') {
    const cut = summary().current_month_income * Number(payload.reduction_pct || 0) / 100;
    return { status: 'Illustrative income stress test', status_color: 'warning', verdict: `A ${payload.reduction_pct}% sample income reduction would reduce monthly cashflow by about ₹${Math.round(cut).toLocaleString('en-IN')}.`, cumulative_income_loss: cut * duration, duration_months: duration, assumptions: ['Synthetic demo income only.'] };
  }
  const contribution = Number(payload.monthly_contribution || 0);
  return { status: 'Illustrative savings projection', status_color: 'success', verdict: `Saving ₹${contribution.toLocaleString('en-IN')} each month would build ₹${(contribution * duration).toLocaleString('en-IN')} over ${duration} months before interest.`, monthly_contribution: contribution, projected_savings_pool: contribution * duration, cumulative_savings: contribution * duration, duration_months: duration, assumptions: ['Excludes interest, tax, and fees. Synthetic projection only.'] };
}

function settingsReset() {
  const previousSettings = clone(store.settings);
  store = createStore();
  store.settings = previousSettings;
  return { message: 'The synthetic sample dataset has been restored in this browser session.' };
}

function insightsForecast() {
  const byCategory = categoryMix('all').slice(0, 7).map((row) => {
    const amounts = store.transactions.filter((tx) => tx.category === row.category && tx.txn_type === 'Expense').map((tx) => tx.amount);
    const average = amounts.length ? amounts.reduce((sum, value) => sum + value, 0) / amounts.length : 0;
    return { category: row.category, forecast: rounded(average), predicted_amount: rounded(average), historical_avg: rounded(average), trend: row.category === 'Shopping' ? 'increasing' : 'stable' };
  });
  const prediction = byCategory.reduce((sum, row) => sum + row.forecast, 0);
  return { overall: { status: 'illustrative', prediction, best_model: 'Demo projection', interval_80: [rounded(prediction * 0.9), rounded(prediction * 1.1)], interval_95: [rounded(prediction * 0.82), rounded(prediction * 1.18)] }, by_category: byCategory };
}

function getDemoResponse(url, options = {}) {
  const parsed = new URL(url, window.location.origin);
  const path = parsed.pathname.replace(/\/$/, '') || '/';
  const method = (options.method || 'GET').toUpperCase();
  const payload = typeof options.body === 'string' ? JSON.parse(options.body || '{}') : options.body || {};

  if (path === '/api/auth/me' && method === 'GET') return Promise.resolve({ full_name: 'Alex Morgan', username: 'Demo account', email: 'Not collected', is_demo: true });
  if (path === '/api/auth/csrf-token' && method === 'GET') return Promise.resolve({ csrf_token: 'demo-session-only' });
  if (path === '/api/auth/login' && method === 'POST') return Promise.resolve({ user: { full_name: 'Alex Morgan', username: 'Demo account', email: 'Not collected', is_demo: true }, csrf_token: 'demo-session-only' });
  if (path === '/api/auth/register' && method === 'POST') return Promise.reject(new Error('Real account registration is disabled in Demo Mode. Choose Explore Demo.'));
  if (path === '/api/auth/logout' && method === 'POST') return Promise.resolve({ message: 'Demo session ended.' });

  if (path === '/api/overview/summary') return Promise.resolve(summary());
  if (path === '/api/overview/category-mix') return Promise.resolve(categoryMix(parsed.searchParams.get('month')));
  if (path === '/api/overview/monthly-trend') return Promise.resolve(monthlyTrend(parsed.searchParams.get('last_months')));
  if (path === '/api/transactions' && method === 'GET') {
    const rows = txFilters(parsed.searchParams);
    const offset = Math.max(0, Number(parsed.searchParams.get('offset') || 0));
    const limit = Math.max(1, Number(parsed.searchParams.get('limit') || 200));
    return Promise.resolve({ data: clone(rows.slice(offset, offset + limit)), total: rows.length, limit, offset });
  }
  if (path === '/api/transactions' && method === 'POST') {
    const row = { ...payload, id: store.nextTransactionId++, notes: payload.notes || '' };
    store.transactions.unshift(row);
    return Promise.resolve(clone(row));
  }
  if (path === '/api/transactions/predict-category' && method === 'POST') return Promise.resolve({ category: detectCategory(payload.description || '', payload.txn_type), method: 'Illustrative keyword suggestion', confidence: 0.82 });
  if (path === '/api/transactions/import-csv' && method === 'POST') return Promise.resolve({ preview: [], imported_rows: 0, skipped_rows: 0, message: 'CSV imports are not available in this frontend-only demo. Add sample entries with the transaction form.' });
  if (path === '/api/transactions/confirm-import' && method === 'POST') return Promise.resolve({ message: 'CSV import is unavailable in demo mode.', imported: 0 });
  const transactionMatch = path.match(/^\/api\/transactions\/(\d+)$/);
  if (transactionMatch && method === 'DELETE') {
    const id = Number(transactionMatch[1]);
    store.transactions = store.transactions.filter((row) => row.id !== id);
    return Promise.resolve({ deleted: id, message: 'Synthetic demo transaction removed.' });
  }
  if (transactionMatch && method === 'PUT') {
    const id = Number(transactionMatch[1]);
    const index = store.transactions.findIndex((row) => row.id === id);
    if (index < 0) return Promise.reject(new Error('Demo transaction not found.'));
    store.transactions[index] = { ...store.transactions[index], ...payload, id };
    return Promise.resolve(clone(store.transactions[index]));
  }

  if (path === '/api/budgets' && method === 'GET') return Promise.resolve(budgetView());
  if (path === '/api/budgets' && method === 'POST') {
    let budget = store.budgets.find((row) => row.month === payload.month && row.category === payload.category);
    if (budget) budget.limit_amount = Number(payload.limit_amount);
    else {
      budget = { id: store.nextBudgetId++, month: payload.month, category: payload.category, limit_amount: Number(payload.limit_amount) };
      store.budgets.push(budget);
    }
    return Promise.resolve(clone(budget));
  }
  const budgetMatch = path.match(/^\/api\/budgets\/(\d+)$/);
  if (budgetMatch && method === 'DELETE') {
    const id = Number(budgetMatch[1]);
    store.budgets = store.budgets.filter((row) => row.id !== id);
    return Promise.resolve({ deleted: id, message: 'Synthetic demo budget removed.' });
  }
  if (path === '/api/bills' && method === 'GET') return Promise.resolve(clone(store.bills));
  if (path === '/api/bills' && method === 'POST') {
    const bill = { id: store.nextBillId++, paid: 0, frequency: 'One-time', next_due_date: '', ...payload };
    store.bills.push(bill);
    return Promise.resolve(clone(bill));
  }
  const billMatch = path.match(/^\/api\/bills\/(\d+)(?:\/pay)?$/);
  if (billMatch && path.endsWith('/pay') && method === 'PATCH') {
    const bill = store.bills.find((row) => row.id === Number(billMatch[1]));
    if (bill) bill.paid = 1;
    return Promise.resolve({ success: true, message: 'Synthetic demo bill marked paid.', next_bill_created: false, next_bill_message: '' });
  }
  if (billMatch && method === 'DELETE') {
    const id = Number(billMatch[1]);
    store.bills = store.bills.filter((row) => row.id !== id);
    return Promise.resolve({ deleted: id, message: 'Synthetic demo bill removed.' });
  }

  if (path === '/api/coach/insights') return Promise.resolve(coachInsights());
  if (path === '/api/budget/history') return Promise.resolve({ history: clone(store.history) });
  if (path === '/api/budget/optimize' && method === 'POST') return Promise.resolve(createOptimization(payload.savings_target));
  if (path === '/api/budget/lock' && method === 'PATCH') {
    store.locks[payload.month] ||= {};
    if (payload.locked_limit == null) delete store.locks[payload.month][payload.category];
    else store.locks[payload.month][payload.category] = Number(payload.locked_limit);
    return Promise.resolve({ locked: payload.locked_limit != null, category: payload.category, month: payload.month });
  }
  if (['/api/budget/approve', '/api/budget/undo'].includes(path) && method === 'POST') {
    const item = store.history.find((row) => row.optimization_id === Number(payload.optimization_id));
    if (!item) return Promise.reject(new Error('Demo optimization was not found.'));
    if (path.endsWith('/approve')) {
      item.previous_budgets = item.recommendations.map((recommendation) => {
        const previous = store.budgets.find((row) => row.month === item.month && row.category === recommendation.category);
        return { category: recommendation.category, previous: previous ? clone(previous) : null };
      });
      for (const recommendation of item.recommendations) {
        const existing = store.budgets.find((row) => row.month === item.month && row.category === recommendation.category);
        if (existing) existing.limit_amount = recommendation.recommended_limit;
        else store.budgets.push({ id: store.nextBudgetId++, month: item.month, category: recommendation.category, limit_amount: recommendation.recommended_limit });
      }
      item.status = 'approved';
      return Promise.resolve({ status: item.status, optimization_id: item.optimization_id, message: 'Illustrative recommendations applied to in-memory sample budgets.' });
    }
    if (item.status === 'approved' && item.previous_budgets) {
      for (const entry of item.previous_budgets) {
        store.budgets = store.budgets.filter((row) => !(row.month === item.month && row.category === entry.category));
        if (entry.previous) store.budgets.push(entry.previous);
      }
    }
    item.status = 'undone';
    return Promise.resolve({ status: item.status, optimization_id: item.optimization_id, message: 'Previous synthetic budget values restored in memory.' });
  }

  if (path === '/api/settings' && method === 'GET') return Promise.resolve(clone(store.settings));
  if (path === '/api/settings' && method === 'PUT') {
    store.settings = { ...store.settings, ...payload };
    return Promise.resolve(clone(store.settings));
  }
  if (path === '/api/settings/load-demo' && method === 'POST') return Promise.resolve({ message: 'Synthetic demo data is already loaded in this browser session.' });
  if (path === '/api/settings/reset-data' && method === 'POST') return Promise.resolve(settingsReset());

  if (path === '/api/insights/forecast') return Promise.resolve(insightsForecast());
  if (path === '/api/insights/anomalies') {
    const outlier = store.transactions.find((row) => row.category === 'Shopping' && row.amount > 10000);
    return Promise.resolve({ anomalies: outlier ? [{ ...outlier, anomaly_score: 0.91, flags: ['Higher than this sample category average'], reason: 'Unusually large synthetic sample purchase' }] : [], total_scanned: store.transactions.length, anomaly_count: outlier ? 1 : 0 });
  }
  if (path === '/api/insights/patterns') return Promise.resolve({
    summary: 'Synthetic sample activity clusters around recurring essentials, steady household purchases, and occasional discretionary spikes.',
    clusters: [
      { cluster_name: 'Recurring essentials', month_count: 6, description: 'Housing, utilities, insurance, and healthcare remain steady across the sample.', avg_monthly_spending: 28300 },
      { cluster_name: 'Flexible lifestyle spend', month_count: 6, description: 'Dining, shopping, and travel vary more month to month.', avg_monthly_spending: 16200 },
    ],
  });
  if (path === '/api/insights/categorization') return Promise.resolve({ model_loaded: false, training_samples: store.transactions.length, model_type: 'Illustrative demo categorizer', categories: DEFAULT_EXPENSE_CATEGORIES });
  if (path === '/api/insights/categorization/test' && method === 'POST') return Promise.resolve({ category: detectCategory(payload.description || '', payload.txn_type), method: 'Illustrative keyword suggestion', confidence: 0.82 });

  const simulatorMatch = path.match(/^\/api\/simulator\/(major-purchase|expense-reduction|income-reduction|monthly-savings)$/);
  if (simulatorMatch && method === 'POST') return Promise.resolve({ scenario: simulatorMatch[1], result: makeSimulation(simulatorMatch[1], payload) });

  return Promise.reject(new Error(`The demo does not include ${method} ${path}. No network request was sent.`));
}

export function demoRequest(url, options) {
  return Promise.resolve().then(() => getDemoResponse(url, options));
}

export function getDemoTransactionsForExport() {
  return clone(store.transactions);
}
