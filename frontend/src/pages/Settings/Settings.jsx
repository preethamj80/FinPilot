import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  ShieldAlert,
  Database,
  User,
  Trash2,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  FolderPlus,
  Loader2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useFinance } from '../../context/FinanceContext';
import { api } from '../../api/client';
import { DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES } from '../../utils/categories';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { DEMO_MODE } from '../../demo/demoMode';

export default function Settings() {
  const { user } = useAuth();
  const { refreshTrigger, triggerRefresh, notify } = useFinance();

  const [loading, setLoading] = useState(true);
  const [openingBalance, setOpeningBalance] = useState('0');
  const [safetyReserve, setSafetyReserve] = useState('2000');
  const [savingsTarget, setSavingsTarget] = useState('0');
  const [savingSettings, setSavingSettings] = useState(false);

  // Reset confirmation modal state
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetConfirmInput, setResetConfirmInput] = useState('');
  const [resetting, setResetting] = useState(false);

  // Demo loading
  const [loadingDemo, setLoadingDemo] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadSettings() {
      setLoading(true);
      try {
        const res = await api.get('/api/settings');
        if (isMounted && res) {
          setOpeningBalance(res.opening_balance?.toString() || '0');
          setSafetyReserve(res.safety_reserve?.toString() || '2000');
          setSavingsTarget(res.monthly_savings_target?.toString() || '0');
        }
      } catch {
        // Fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadSettings();
    return () => {
      isMounted = false;
    };
  }, [refreshTrigger]);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSavingSettings(true);
    try {
      await api.put('/api/settings', {
        opening_balance: parseFloat(openingBalance) || 0,
        safety_reserve: parseFloat(safetyReserve) || 0,
        monthly_savings_target: parseFloat(savingsTarget) || 0,
      });
      notify('Financial parameters updated successfully!', 'success');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to update settings.', 'error');
    } finally {
      setSavingSettings(false);
    }
  };

  const handleLoadDemo = async () => {
    setLoadingDemo(true);
    try {
      const res = await api.post('/api/settings/load-demo');
      notify(res.message || 'Demo transactions loaded successfully!', 'success');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to load demo data.', 'error');
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleResetData = async () => {
    if (resetConfirmInput.trim().toUpperCase() !== 'RESET') {
      notify('Type RESET to confirm deletion.', 'warning');
      return;
    }
    setResetting(true);
    try {
      const res = await api.post('/api/settings/reset-data');
      notify(res.message || 'All transactions cleared successfully.', 'success');
      setShowResetModal(false);
      setResetConfirmInput('');
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Reset failed.', 'error');
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading financial settings..." />;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card">
        <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">Settings</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Configure financial rules, personal reserve limits, and data management.
        </p>
      </div>

      {/* Account Info */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-4 h-4 text-teal-600" />
          <h2 className="text-base font-bold text-slate-900">Account Details</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="text-slate-400 block mb-0.5">Signed In As</span>
            <span className="font-bold text-slate-900 text-sm">{user?.full_name || 'User'}</span>
          </div>
          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="text-slate-400 block mb-0.5">Email Address</span>
            <span className="font-bold text-slate-900 text-sm">{user?.email || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Financial Planning Guardrails Form */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <SettingsIcon className="w-4 h-4 text-teal-600" />
          <h2 className="text-base font-bold text-slate-900">Safe-to-Spend Parameters</h2>
        </div>
        <p className="text-xs text-slate-500">
          These three variables define the mathematical guardrails for your daily & monthly spendable cash.
        </p>

        <form onSubmit={handleSaveSettings} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Opening Cash Balance (₹)</label>
              <input
                type="number"
                step="50"
                min="0"
                required
                value={openingBalance}
                onChange={(e) => setOpeningBalance(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Starting account balance</span>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Safety Reserve Floor (₹)</label>
              <input
                type="number"
                step="50"
                min="0"
                required
                value={safetyReserve}
                onChange={(e) => setSafetyReserve(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Protected emergency cushion</span>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Monthly Savings Goal (₹)</label>
              <input
                type="number"
                step="50"
                min="0"
                required
                value={savingsTarget}
                onChange={(e) => setSavingsTarget(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Allocated before spendable cash</span>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={savingSettings}
              className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl font-bold transition-all disabled:opacity-50 cursor-pointer"
            >
              {savingSettings ? 'Saving...' : 'Update Parameters'}
            </button>
          </div>
        </form>
      </div>

      {/* Data Management Section */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <Database className="w-4 h-4 text-teal-600" />
          <h2 className="text-base font-bold text-slate-900">Data Management</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          {/* Demo Data Card */}
          {!DEMO_MODE && <div className="p-4 rounded-xl border border-slate-100 bg-slate-50 space-y-2 flex flex-col justify-between">
            <div>
              <div className="font-bold text-slate-900 mb-1 flex items-center gap-1.5">
                <RefreshCw className="w-4 h-4 text-teal-600" /> Load Demo Financial Records
              </div>
              <p className="text-slate-500 leading-relaxed">
                Add realistic demo transactions, bills, and monthly budgets to test and explore the interface.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLoadDemo}
              disabled={loadingDemo}
              className="mt-3 px-4 py-2 bg-white border border-slate-300 hover:border-teal-500 text-slate-700 rounded-xl font-bold disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loadingDemo ? 'Populating...' : 'Populate Demo Data'}
            </button>
          </div>}

          {/* Reset Card */}
          <div className="p-4 rounded-xl border border-rose-100 bg-rose-50/40 space-y-2 flex flex-col justify-between">
            <div>
              <div className="font-bold text-rose-800 mb-1 flex items-center gap-1.5">
                <Trash2 className="w-4 h-4 text-rose-600" /> {DEMO_MODE ? 'Restore Demo Samples' : 'Clear Financial History'}
              </div>
              <p className="text-rose-700/80 leading-relaxed">
                {DEMO_MODE
                  ? 'Restore the original synthetic examples for this browser session. No account or database is affected.'
                  : 'Permanently delete all transactions, budgets, and bills for your account. Settings are preserved.'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowResetModal(true)}
              className="mt-3 px-4 py-2 bg-white border border-rose-300 hover:bg-rose-600 hover:text-white text-rose-700 rounded-xl font-bold transition-all cursor-pointer"
            >
              {DEMO_MODE ? 'Restore Sample Dataset...' : 'Reset My Records...'}
            </button>
          </div>
        </div>
      </div>

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mb-3">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">{DEMO_MODE ? 'Restore Demo Samples' : 'Permanent Data Reset'}</h3>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              {DEMO_MODE
                ? <>This replaces only the current in-memory examples with the original synthetic dataset. Refreshing the browser also resets the demo. Type <span className="font-bold text-rose-600">RESET</span> to confirm.</>
                : <>This will permanently delete all transactions, budgets, and scheduled bills associated with your account. Please type <span className="font-bold text-rose-600">RESET</span> to confirm.</>}
            </p>
            <input
              type="text"
              placeholder="RESET"
              value={resetConfirmInput}
              onChange={(e) => setResetConfirmInput(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold text-center mb-4 uppercase"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowResetModal(false);
                  setResetConfirmInput('');
                }}
                className="px-4 py-2 text-xs font-semibold text-slate-600"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleResetData}
                disabled={resetConfirmInput.trim().toUpperCase() !== 'RESET' || resetting}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold disabled:opacity-30 cursor-pointer"
              >
                {resetting ? 'Resetting...' : DEMO_MODE ? 'Restore Samples' : 'Yes, Delete All'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
