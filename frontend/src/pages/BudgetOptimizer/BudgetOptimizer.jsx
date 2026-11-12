import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  Check,
  LockKeyhole,
  RefreshCw,
  Sparkles,
  Undo2,
  UnlockKeyhole,
} from 'lucide-react';
import { api } from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useFinance } from '../../context/FinanceContext';
import { formatCurrency } from '../../utils/categories';
import DemoNotice from '../../components/common/DemoNotice';

const surface = 'rounded-2xl border border-[var(--color-border)] bg-[var(--color-card-bg)] shadow-card';
const primaryButton = 'inline-flex items-center justify-center gap-2 rounded-xl bg-[var(--color-gold)] px-4 py-2.5 text-sm font-bold text-[#17221D] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50';
const secondaryButton = 'inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--surface-raised)] px-3.5 py-2 text-sm font-semibold text-[var(--color-text-primary)] transition hover:border-[var(--color-gold)] disabled:cursor-not-allowed disabled:opacity-50';

export default function BudgetOptimizer() {
  const { refreshTrigger, triggerRefresh } = useFinance();
  const [history, setHistory] = useState([]);
  const [active, setActive] = useState(null);
  const [savingsTarget, setSavingsTarget] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadHistory = useCallback(async (isMounted = () => true) => {
    try {
      const response = await api.get('/api/budget/history');
      if (!isMounted()) return;
      const records = response?.history || [];
      setHistory(records);
      setActive((current) => current || records[0] || null);
      setError('');
    } catch (err) {
      if (isMounted()) setError(err.message || 'Unable to load optimization history.');
    } finally {
      if (isMounted()) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    loadHistory(() => mounted);
    return () => { mounted = false; };
  }, [loadHistory, refreshTrigger]);

  const saveActive = (updated) => {
    setActive(updated);
    setHistory((items) => items.map((item) => (
      item.optimization_id === updated.optimization_id ? updated : item
    )));
  };

  const generateRecommendations = async () => {
    setBusy('generate');
    setError('');
    setSuccess('');
    try {
      const target = savingsTarget.trim() === '' ? null : Number(savingsTarget);
      if (target !== null && (!Number.isFinite(target) || target < 0)) {
        throw new Error('Enter a savings target of zero or more.');
      }
      const response = await api.post('/api/budget/optimize', {
        months_history: 3,
        savings_target: target,
      });
      setActive(response);
      setHistory((items) => [response, ...items.filter((item) => item.optimization_id !== response.optimization_id)]);
      setSuccess('Recommendations are ready. Your budgets have not been changed.');
    } catch (err) {
      setError(err.message || 'Unable to generate recommendations from your transaction history.');
    } finally {
      setBusy('');
    }
  };

  const changeLock = async (recommendation) => {
    if (!active) return;
    setBusy(`lock:${recommendation.category}`);
    setError('');
    setSuccess('');
    try {
      const lockedLimit = recommendation.locked
        ? null
        : (recommendation.current_limit ?? recommendation.recommended_limit);
      await api.patch('/api/budget/lock', {
        month: active.month,
        category: recommendation.category,
        locked_limit: lockedLimit,
      });
      // Regenerate so the saved proposal that can be approved includes the lock.
      const refreshed = await api.post('/api/budget/optimize', {
        months_history: 3,
        savings_target: active.savings_target ?? (savingsTarget.trim() ? Number(savingsTarget) : null),
      });
      setActive(refreshed);
      setHistory((items) => [refreshed, ...items.filter((item) => item.optimization_id !== refreshed.optimization_id)]);
      setSuccess(lockedLimit === null
        ? `${recommendation.category} unlocked and recommendations refreshed.`
        : `${recommendation.category} locked at ${formatCurrency(lockedLimit)}.`);
    } catch (err) {
      setError(err.message || `Unable to update the ${recommendation.category} lock.`);
    } finally {
      setBusy('');
    }
  };

  const approve = async () => {
    if (!active || active.status !== 'pending') return;
    setBusy('approve');
    setError('');
    setSuccess('');
    try {
      await api.post('/api/budget/approve', { optimization_id: active.optimization_id });
      const updated = { ...active, status: 'approved' };
      saveActive(updated);
      setSuccess('Approved recommendations have been applied to your budgets.');
      triggerRefresh();
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Unable to approve this optimization.');
    } finally {
      setBusy('');
    }
  };

  const undo = async (record = active) => {
    if (!record || record.status !== 'approved') return;
    setBusy(`undo:${record.optimization_id}`);
    setError('');
    setSuccess('');
    try {
      await api.post('/api/budget/undo', { optimization_id: record.optimization_id });
      const updated = { ...record, status: 'undone' };
      saveActive(updated);
      setSuccess('The previous budget values have been restored.');
      triggerRefresh();
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Unable to undo this optimization.');
    } finally {
      setBusy('');
    }
  };

  if (loading) return <LoadingSpinner text="Loading budget optimization history..." />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-12">
      <header className={`${surface} flex flex-col justify-between gap-5 p-6 sm:flex-row sm:items-center sm:p-7`}>
        <div className="flex items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-[var(--color-border)] bg-[var(--surface-raised)] text-[var(--color-gold)]">
            <Sparkles className="h-6 w-6" />
          </span>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-sage)]">AI planning</p>
            <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[var(--color-text-primary)]">Budget Optimizer</h1>
            <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-secondary)]">
              A transparent spending heuristic based on completed transaction history and existing budgets, with current unpaid bills surfaced for review.
            </p>
            <DemoNotice ai compact className="mt-3 max-w-2xl" />
          </div>
        </div>
        <div className="flex w-full flex-col gap-2 sm:max-w-xs">
          <label htmlFor="savings-target" className="text-xs font-semibold text-[var(--color-text-secondary)]">Monthly savings target</label>
          <div className="flex gap-2">
            <div className="relative min-w-0 flex-1">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--color-text-secondary)]">₹</span>
              <input
                id="savings-target"
                type="number"
                min="0"
                step="500"
                value={savingsTarget}
                onChange={(event) => setSavingsTarget(event.target.value)}
                placeholder="Use saved target / 10%"
                className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--surface-raised)] py-2.5 pl-7 pr-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)]"
              />
            </div>
            <button type="button" onClick={generateRecommendations} disabled={!!busy} className={primaryButton}>
              <RefreshCw className={`h-4 w-4 ${busy === 'generate' ? 'animate-spin' : ''}`} />
              <span className="whitespace-nowrap">{busy === 'generate' ? 'Generating…' : 'Generate'}</span>
            </button>
          </div>
          <p className="text-[11px] text-[var(--color-text-secondary)]">Blank uses your saved target, or 10% of average monthly income.</p>
        </div>
      </header>

      {error && (
        <div role="alert" className="flex items-start gap-3 rounded-2xl border border-[var(--color-negative)]/40 bg-[var(--color-negative)]/10 p-4 text-sm text-[var(--color-text-primary)]">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-negative)]" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div role="status" className="flex items-start gap-3 rounded-2xl border border-[var(--color-positive)]/40 bg-[var(--color-positive)]/10 p-4 text-sm text-[var(--color-text-primary)]">
          <Check className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-positive)]" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className={`${surface} min-w-0 overflow-hidden`}>
          <div className="flex flex-col gap-3 border-b border-[var(--color-border)] p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
            <div>
              <h2 className="text-lg font-bold text-[var(--color-text-primary)]">Current vs recommended budgets</h2>
              <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                {active ? `Plan for ${active.month} · ${active.status}` : 'Generate a plan from your recorded transactions.'}
              </p>
            </div>
            {active?.status === 'pending' && active.recommendations?.length > 0 && (
              <button type="button" onClick={approve} disabled={!!busy} className={primaryButton}>
                <Check className="h-4 w-4" />
                {busy === 'approve' ? 'Applying…' : 'Approve & apply'}
              </button>
            )}
            {active?.status === 'approved' && (
              <button type="button" onClick={() => undo(active)} disabled={!!busy} className={secondaryButton}>
                <Undo2 className="h-4 w-4" />
                {busy === `undo:${active.optimization_id}` ? 'Restoring…' : 'Undo approval'}
              </button>
            )}
          </div>

          {active?.unpaid_bills?.length > 0 && (
            <div className="border-b border-[var(--color-border)] bg-[var(--surface-raised)]/50 px-5 py-4 sm:px-6">
              <p className="text-xs font-semibold text-[var(--color-sage)]">Unpaid bills due this month</p>
              <p className="mt-1 text-[11px] text-[var(--color-text-secondary)]">Shown as current obligations; historical spending already includes past bill payments.</p>
              <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-[var(--color-text-secondary)]">
                {active.unpaid_bills.map((bill, index) => (
                  <span key={`${bill.description}-${bill.due_date}-${index}`}>
                    {bill.description} · {formatCurrency(bill.amount)} · due {bill.due_date}
                  </span>
                ))}
              </div>
            </div>
          )}

          {!active ? (
            <div className="px-6 py-14 text-center">
              <Sparkles className="mx-auto h-9 w-9 text-[var(--color-gold)]" />
              <h3 className="mt-3 font-bold text-[var(--color-text-primary)]">No recommendations yet</h3>
              <p className="mx-auto mt-1 max-w-md text-sm text-[var(--color-text-secondary)]">
                Generate a plan to analyze your recorded income and expenses. The optimizer needs at least one completed month; no sample data is used.
              </p>
            </div>
          ) : active.recommendations?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-[var(--surface-raised)]/70 text-xs uppercase tracking-wide text-[var(--color-text-secondary)]">
                  <tr>
                    <th className="px-5 py-3 font-semibold sm:px-6">Category</th>
                    <th className="px-4 py-3 font-semibold">Current limit</th>
                    <th className="px-4 py-3 font-semibold">Recommended</th>
                    <th className="px-4 py-3 font-semibold">Impact / confidence</th>
                    <th className="px-4 py-3 font-semibold">Lock</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border)]">
                  {active.recommendations.map((recommendation) => (
                    <tr key={recommendation.category} className="align-top hover:bg-[var(--surface-raised)]/35">
                      <td className="px-5 py-4 sm:px-6">
                        <p className="font-semibold text-[var(--color-text-primary)]">{recommendation.category}</p>
                        <p className="mt-1 max-w-sm text-xs leading-relaxed text-[var(--color-text-secondary)]">{recommendation.reason}</p>
                      </td>
                      <td className="px-4 py-4 tabular-nums text-[var(--color-text-secondary)]">
                        {recommendation.current_limit == null ? 'Not set' : formatCurrency(recommendation.current_limit)}
                      </td>
                      <td className="px-4 py-4 font-bold tabular-nums text-[var(--color-text-primary)]">
                        {formatCurrency(recommendation.recommended_limit)}
                      </td>
                      <td className="px-4 py-4">
                        <p className="font-semibold tabular-nums text-[var(--color-positive)]">{formatCurrency(recommendation.impact_estimate)}</p>
                        <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{recommendation.confidence} confidence</p>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          type="button"
                          aria-pressed={recommendation.locked}
                          aria-label={`${recommendation.locked ? 'Unlock' : 'Lock'} ${recommendation.category}`}
                          onClick={() => changeLock(recommendation)}
                          disabled={!!busy || active.status !== 'pending'}
                          className={secondaryButton}
                        >
                          {busy === `lock:${recommendation.category}` ? <RefreshCw className="h-4 w-4 animate-spin" /> : recommendation.locked ? <UnlockKeyhole className="h-4 w-4" /> : <LockKeyhole className="h-4 w-4" />}
                          {recommendation.locked ? 'Unlock' : 'Lock'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-6 py-12 text-center text-sm text-[var(--color-text-secondary)]">
              No expense categories were available in the completed transaction history.
            </div>
          )}

          {active?.status === 'pending' && active.recommendations?.length > 0 && (
            <p className="border-t border-[var(--color-border)] px-5 py-3 text-xs text-[var(--color-text-secondary)] sm:px-6">
              Nothing is applied until you approve this plan. Essential categories are preserved by the heuristic; locked categories retain their chosen limits.
            </p>
          )}
        </section>

        <aside className={`${surface} h-fit p-5 sm:p-6`}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-[var(--color-text-primary)]">Optimization history</h2>
              <p className="mt-1 text-xs text-[var(--color-text-secondary)]">Your saved proposals and actions</p>
            </div>
            <span className="rounded-lg bg-[var(--surface-raised)] px-2 py-1 text-xs font-bold text-[var(--color-sage)]">{history.length}</span>
          </div>

          {history.length === 0 ? (
            <p className="mt-6 rounded-xl border border-dashed border-[var(--color-border)] p-4 text-sm text-[var(--color-text-secondary)]">
              Generated proposals will appear here. Creating one does not change your budgets.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {history.map((item) => (
                <li key={item.optimization_id}>
                  <button
                    type="button"
                    onClick={() => { setActive(item); setError(''); setSuccess(''); }}
                    className={`w-full rounded-xl border p-3 text-left transition ${active?.optimization_id === item.optimization_id ? 'border-[var(--color-gold)] bg-[var(--surface-raised)]' : 'border-[var(--color-border)] bg-[var(--color-card-bg)] hover:bg-[var(--surface-raised)]'}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-[var(--color-text-primary)]">{item.month}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${item.status === 'approved' ? 'bg-[var(--color-positive)]/15 text-[var(--color-positive)]' : item.status === 'undone' ? 'bg-[var(--color-negative)]/15 text-[var(--color-negative)]' : 'bg-[var(--color-gold)]/15 text-[var(--color-gold)]'}`}>
                        {item.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                      {item.recommendations.length} categories · {new Date(item.generated_at).toLocaleString()}
                    </p>
                  </button>
                  {item.status === 'approved' && (
                    <button type="button" onClick={() => undo(item)} disabled={!!busy} className="mt-2 inline-flex items-center gap-1 px-2 text-xs font-semibold text-[var(--color-sage)] hover:text-[var(--color-gold)] disabled:opacity-50">
                      <Undo2 className="h-3.5 w-3.5" /> Undo this approval
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </div>
  );
}
