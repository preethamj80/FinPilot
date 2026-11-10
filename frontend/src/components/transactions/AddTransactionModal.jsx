import React, { useState, useEffect } from 'react';
import { X, Sparkles, Plus, Loader2 } from 'lucide-react';
import { useFinance } from '../../context/FinanceContext';
import { api } from '../../api/client';
import { DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES } from '../../utils/categories';

export default function AddTransactionModal() {
  const { isAddTxModalOpen, addTxDefaultType, closeAddTx, triggerRefresh, notify } = useFinance();

  const [txnType, setTxnType] = useState('Expense');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Food & Dining');
  const [txnDate, setTxnDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [predicting, setPredicting] = useState(false);
  const [predictionMethod, setPredictionMethod] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Sync default type when modal opens
  useEffect(() => {
    if (isAddTxModalOpen && addTxDefaultType) {
      setTxnType(addTxDefaultType);
      if (addTxDefaultType === 'Income') {
        setCategory('Salary');
      } else {
        setCategory('Food & Dining');
      }
    }
  }, [isAddTxModalOpen, addTxDefaultType]);

  // Reset category default when type flips
  useEffect(() => {
    if (txnType === 'Income') {
      setCategory('Salary');
    } else {
      setCategory('Food & Dining');
    }
  }, [txnType]);

  // Real-time category suggestion with debounce
  useEffect(() => {
    if (!description.trim() || description.length < 3) {
      setPredictionMethod('');
      return;
    }

    const timer = setTimeout(async () => {
      setPredicting(true);
      try {
        const res = await api.post('/api/transactions/predict-category', {
          description,
          txn_type: txnType,
        });
        if (res && res.category) {
          setCategory(res.category);
          setPredictionMethod(res.method || 'Auto-suggested');
        }
      } catch {
        // Fallback silently
      } finally {
        setPredicting(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [description, txnType]);

  if (!isAddTxModalOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Please enter a valid amount greater than zero.');
      return;
    }

    if (!description.trim()) {
      setError('Please provide a description.');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/api/transactions', {
        txn_date: txnDate,
        txn_type: txnType,
        description: description.trim(),
        amount: parsedAmount,
        category,
        notes: notes.trim(),
      });

      notify(
        `${txnType === 'Income' ? 'Income' : 'Expense'} of ₹${parsedAmount.toLocaleString('en-IN')} saved successfully!`,
        'success'
      );

      // Reset form
      setAmount('');
      setDescription('');
      setNotes('');
      setPredictionMethod('');
      triggerRefresh();
      closeAddTx();
    } catch (err) {
      setError(err.message || 'Failed to save transaction.');
    } finally {
      setSubmitting(false);
    }
  };

  const categories = txnType === 'Income' ? DEFAULT_INCOME_CATEGORIES : DEFAULT_EXPENSE_CATEGORIES;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden animate-scale-up">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-700 flex items-center justify-center font-bold">
              <Plus className="w-5 h-5 text-teal-600" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Add Transaction</h3>
          </div>
          <button
            onClick={closeAddTx}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          {/* Type Toggle */}
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
            <button
              type="button"
              onClick={() => setTxnType('Expense')}
              className={`py-2 text-xs font-bold rounded-lg transition-all ${
                txnType === 'Expense'
                  ? 'bg-white text-rose-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Expense (Outflow)
            </button>
            <button
              type="button"
              onClick={() => setTxnType('Income')}
              className={`py-2 text-xs font-bold rounded-lg transition-all ${
                txnType === 'Income'
                  ? 'bg-white text-emerald-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Income (Inflow)
            </button>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Amount (₹) <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-lg">
                ₹
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                autoFocus
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-lg font-bold text-slate-900 placeholder:text-slate-300 outline-hidden transition-all"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">
                Description <span className="text-rose-500">*</span>
              </label>
              {predicting && (
                <span className="text-[11px] text-teal-600 flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" /> Suggesting category...
                </span>
              )}
            </div>
            <input
              type="text"
              required
              placeholder="e.g. Swiggy lunch, Grocery store, Uber"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-sm text-slate-900 placeholder:text-slate-400 outline-hidden transition-all"
            />
          </div>

          {/* Category */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">Category</label>
              {predictionMethod && (
                <span className="text-[10px] text-teal-700 font-medium bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-teal-600" />
                  {predictionMethod}
                </span>
              )}
            </div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-sm text-slate-900 outline-hidden bg-white cursor-pointer"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Date</label>
            <input
              type="date"
              required
              value={txnDate}
              onChange={(e) => setTxnDate(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-sm text-slate-900 outline-hidden bg-white"
            />
          </div>

          {/* Notes (Optional) */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">
              Notes <span className="font-normal text-slate-400">(optional)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Split with Priya"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl border border-slate-200 focus:border-teal-500 text-xs text-slate-700 placeholder:text-slate-400 outline-hidden"
            />
          </div>

          {/* Submit */}
          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={closeAddTx}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold shadow-sm shadow-teal-700/30 flex items-center gap-2 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving...
                </>
              ) : (
                'Save Transaction'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
