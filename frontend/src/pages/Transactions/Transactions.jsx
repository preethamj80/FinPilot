import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Filter,
  Download,
  Upload,
  Plus,
  Trash2,
  Edit,
  ArrowUpDown,
  FileSpreadsheet,
  CheckCircle2,
  X,
  AlertCircle,
  FolderPlus,
} from 'lucide-react';
import { useFinance } from '../../context/FinanceContext';
import { api } from '../../api/client';
import { formatCurrency, getCategoryColorMap, DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES } from '../../utils/categories';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { DEMO_MODE } from '../../demo/demoMode';

export default function Transactions() {
  const { refreshTrigger, triggerRefresh, openAddTx, selectedCategoryFilter, filterByCategory, notify } = useFinance();

  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [txnType, setTxnType] = useState('All');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 25;

  // Custom Category State
  const [customCategoryInput, setCustomCategoryInput] = useState('');
  const [showAddCategoryModal, setShowAddCategoryModal] = useState(false);
  const [availableCategories, setAvailableCategories] = useState([...DEFAULT_EXPENSE_CATEGORIES, ...DEFAULT_INCOME_CATEGORIES]);

  // CSV Import State
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importSummary, setImportSummary] = useState(null);
  const [importing, setImporting] = useState(false);

  // Edit Transaction State
  const [editingTxn, setEditingTxn] = useState(null);

  // Delete Confirmation State
  const [deletingTxnId, setDeletingTxnId] = useState(null);
  const categoryColors = useMemo(
    () => getCategoryColorMap(transactions.map((transaction) => transaction.category)),
    [transactions]
  );

  // Load transactions
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setError('');
      try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (txnType !== 'All') params.append('txn_type', txnType);
        if (selectedCategoryFilter !== 'All') params.append('category', selectedCategoryFilter);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        params.append('limit', pageSize.toString());
        params.append('offset', (page * pageSize).toString());

        const res = await api.get(`/api/transactions?${params.toString()}`);
        if (!isMounted) return;
        setTransactions(res.data || []);
        setTotalCount(res.total || 0);

        // Fetch user custom categories or all unique categories in transactions
        const existingCats = new Set([...availableCategories, ...(res.data || []).map((t) => t.category)]);
        setAvailableCategories(Array.from(existingCats));
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to load transactions.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [refreshTrigger, search, txnType, selectedCategoryFilter, startDate, endDate, page]);

  // Handle CSV Export
  const handleExport = async () => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (txnType !== 'All') params.append('txn_type', txnType);
    if (selectedCategoryFilter !== 'All') params.append('category', selectedCategoryFilter);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    if (DEMO_MODE) {
      try {
        const result = await api.get(`/api/transactions?${params.toString()}`);
        const fields = ['txn_date', 'txn_type', 'description', 'amount', 'category', 'notes'];
        const quote = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
        const csv = [fields.join(','), ...result.data.map((row) => fields.map((field) => quote(row[field])).join(','))].join('\r\n');
        const link = document.createElement('a');
        link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
        link.download = 'finpilot-demo-transactions.csv';
        link.click();
        window.setTimeout(() => URL.revokeObjectURL(link.href), 0);
        notify('Synthetic demo transactions exported locally.', 'success');
      } catch (err) {
        notify(err.message || 'Unable to export demo transactions.', 'error');
      }
      return;
    }
    window.open(`/api/transactions/export-csv?${params.toString()}`, '_blank');
    notify('Export started — downloading CSV file.', 'success');
  };

  // Handle CSV Upload preview
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (DEMO_MODE) {
      notify('CSV import is unavailable in the frontend-only demo. Add sample transactions with the form instead.', 'warning');
      e.target.value = '';
      return;
    }
    setImportFile(file);
    setImporting(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const summary = await api.upload('/api/transactions/import-csv', formData);
      setImportSummary(summary);
    } catch (err) {
      notify(err.message || 'Failed to parse CSV.', 'error');
    } finally {
      setImporting(false);
    }
  };

  // Confirm CSV bulk insert
  const handleConfirmImport = async () => {
    if (!importSummary?.preview || importSummary.preview.length === 0) return;
    setImporting(true);
    try {
      const res = await api.post('/api/transactions/confirm-import', {
        rows: importSummary.preview,
      });
      notify(res.message || 'Transactions imported successfully!', 'success');
      setShowImportModal(false);
      setImportFile(null);
      setImportSummary(null);
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Import confirmation failed.', 'error');
    } finally {
      setImporting(false);
    }
  };

  // Delete transaction
  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/transactions/${id}`);
      notify('Transaction deleted successfully.', 'success');
      setDeletingTxnId(null);
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to delete transaction.', 'error');
    }
  };

  // Save edited transaction
  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editingTxn) return;

    try {
      await api.put(`/api/transactions/${editingTxn.id}`, {
        txn_date: editingTxn.txn_date,
        txn_type: editingTxn.txn_type,
        description: editingTxn.description,
        amount: parseFloat(editingTxn.amount),
        category: editingTxn.category,
        notes: editingTxn.notes || '',
      });
      notify('Transaction updated successfully.', 'success');
      setEditingTxn(null);
      triggerRefresh();
    } catch (err) {
      notify(err.message || 'Failed to update transaction.', 'error');
    }
  };

  // Add Custom Category
  const handleAddCustomCategory = (e) => {
    e.preventDefault();
    const trimmed = customCategoryInput.trim();
    if (!trimmed) return;
    if (!availableCategories.includes(trimmed)) {
      setAvailableCategories((prev) => [trimmed, ...prev]);
    }
    filterByCategory(trimmed);
    notify(`Custom category "${trimmed}" added and active!`, 'success');
    setCustomCategoryInput('');
    setShowAddCategoryModal(false);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[var(--color-card-bg)] p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">Transactions</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Search, filter, categorize, and audit your personal financial ledger.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowAddCategoryModal(true)}
            className="px-3.5 py-2.5 rounded-2xl border border-slate-200/80 text-slate-700 hover:bg-slate-50 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <FolderPlus className="w-4 h-4 text-slate-500" />
            + Category
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="px-3.5 py-2.5 rounded-2xl border border-slate-200/80 text-slate-700 hover:bg-slate-50 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Upload className="w-4 h-4 text-slate-500" />
            Import CSV
          </button>
          <button
            onClick={handleExport}
            className="px-3.5 py-2.5 rounded-2xl border border-slate-200/80 text-slate-700 hover:bg-slate-50 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4 text-slate-500" />
            Export CSV
          </button>
          <button
            onClick={openAddTx}
            className="px-5 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-teal-700/20 active:scale-95 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Add Transaction
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Controls Bar */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-card space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3">
          {/* Search box (5 cols) */}
          <div className="lg:col-span-5 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search description, merchant, or notes..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 text-xs text-slate-900 placeholder:text-slate-400 outline-hidden transition-colors"
            />
          </div>

          {/* Type Toggle (3 cols) */}
          <div className="lg:col-span-3">
            <select
              value={txnType}
              onChange={(e) => {
                setTxnType(e.target.value);
                setPage(0);
              }}
              className="w-full px-3 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 text-xs text-slate-700 outline-hidden bg-white transition-colors"
            >
              <option value="All">All Types (Income & Expense)</option>
              <option value="Expense">Expense Only</option>
              <option value="Income">Income Only</option>
            </select>
          </div>

          {/* Category Dropdown (4 cols) */}
          <div className="lg:col-span-4">
            <select
              value={selectedCategoryFilter}
              onChange={(e) => {
                filterByCategory(e.target.value);
                setPage(0);
              }}
              className="w-full px-3 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 text-xs text-slate-700 outline-hidden bg-white transition-colors"
            >
              <option value="All">All Categories ({availableCategories.length})</option>
              {availableCategories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Category Pills Quick Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 text-xs">
          <button
            onClick={() => {
              filterByCategory('All');
              setPage(0);
            }}
            className={`px-3 py-1.5 rounded-xl font-semibold transition-colors shrink-0 ${
              selectedCategoryFilter === 'All'
                ? 'bg-[var(--color-secondary-bg)] text-slate-900 shadow-xs border border-slate-300'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All
          </button>
          {DEFAULT_EXPENSE_CATEGORIES.slice(0, 8).map((cat) => (
            <button
              key={cat}
              onClick={() => {
                filterByCategory(cat);
                setPage(0);
              }}
              className={`px-3 py-1.5 rounded-xl font-medium transition-colors shrink-0 ${
                selectedCategoryFilter === cat
                  ? 'bg-teal-600 text-white font-semibold shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Transaction Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-card overflow-hidden">
        {loading ? (
          <LoadingSpinner text="Loading transactions..." />
        ) : transactions.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-base font-semibold text-slate-800">No transactions match your filter.</p>
            <p className="text-xs text-slate-400 mt-1">
              Try adjusting your search criteria or add a new transaction.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 font-bold border-b border-slate-200/80">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((tx) => {
                  const categoryColor = categoryColors[tx.category];
                  const isExpense = tx.txn_type === 'Expense';
                  return (
                    <tr key={tx.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-4 font-mono text-slate-600 whitespace-nowrap">
                        {tx.txn_date}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900">{tx.description}</div>
                        {tx.notes && <div className="text-[11px] text-slate-400 mt-0.5">{tx.notes}</div>}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <button
                          onClick={() => {
                            filterByCategory(tx.category);
                            setPage(0);
                          }}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border hover:opacity-80 transition-opacity"
                          style={{ color: categoryColor, backgroundColor: `${categoryColor}1A`, borderColor: `${categoryColor}66` }}
                        >
                          <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: categoryColor }} aria-hidden="true" />
                          <span>{tx.category}</span>
                        </button>
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-md font-bold text-[10px] uppercase ${
                            isExpense
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          }`}
                        >
                          {tx.txn_type}
                        </span>
                      </td>
                      <td
                        className={`py-3.5 px-4 text-right font-bold font-mono text-sm whitespace-nowrap ${
                          isExpense ? 'text-slate-900' : 'text-emerald-600'
                        }`}
                      >
                        {isExpense ? '-' : '+'}
                        {formatCurrency(tx.amount)}
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap space-x-1">
                        <button
                          onClick={() => setEditingTxn(tx)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-teal-600 hover:bg-slate-100 transition-colors"
                          title="Edit Transaction"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeletingTxnId(tx.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                          title="Delete Transaction"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-100 bg-slate-50/50 text-xs text-slate-600">
          <div>
            Showing {transactions.length} of {totalCount} transactions
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-semibold disabled:opacity-40"
            >
              Previous
            </button>
            <span className="font-bold">Page {page + 1}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={(page + 1) * pageSize >= totalCount}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-semibold disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Add Custom Category Modal */}
      {showAddCategoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Create Custom Category</h3>
            <p className="text-xs text-slate-500 mb-4">
              Add your own unique expense or income category for tracking.
            </p>
            <form onSubmit={handleAddCustomCategory} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category Name
                </label>
                <input
                  type="text"
                  required
                  autoFocus
                  placeholder="e.g. Pet Care, Gaming, Side Hustle"
                  value={customCategoryInput}
                  onChange={(e) => setCustomCategoryInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm outline-hidden focus:border-teal-500"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddCategoryModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold"
                >
                  Save Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Transaction Modal */}
      {editingTxn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-4">Edit Transaction #{editingTxn.id}</h3>
            <form onSubmit={handleUpdate} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={editingTxn.amount}
                  onChange={(e) => setEditingTxn({ ...editingTxn, amount: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm font-bold"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  required
                  value={editingTxn.description}
                  onChange={(e) => setEditingTxn({ ...editingTxn, description: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Category</label>
                <select
                  value={editingTxn.category}
                  onChange={(e) => setEditingTxn({ ...editingTxn, category: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                >
                  {availableCategories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Date</label>
                <input
                  type="date"
                  required
                  value={editingTxn.txn_date}
                  onChange={(e) => setEditingTxn({ ...editingTxn, txn_date: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm bg-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setEditingTxn(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-bold"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingTxnId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-2">Delete Transaction?</h3>
            <p className="text-xs text-slate-500 mb-5">
              This action cannot be undone. Are you sure you want to permanently delete transaction #{deletingTxnId}?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeletingTxnId(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Keep Transaction
              </button>
              <button
                onClick={() => handleDelete(deletingTxnId)}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-teal-600" />
                <h3 className="text-base font-bold text-slate-900">Import Transactions CSV</h3>
              </div>
              <button onClick={() => setShowImportModal(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Upload bank statements or CSV files. FinPilot will validate dates, amounts, detect duplicates, and preview records before inserting.
            </p>

            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full p-3 border-2 border-dashed border-slate-300 rounded-xl text-xs text-slate-600 mb-4 cursor-pointer"
            />

            {importSummary && (
              <div className="space-y-3 mb-4">
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="font-bold text-slate-900">{importSummary.total_rows}</div>
                    <div className="text-[10px] text-slate-500">Total Rows</div>
                  </div>
                  <div className="p-2.5 bg-emerald-50 rounded-xl border border-emerald-200">
                    <div className="font-bold text-emerald-700">{importSummary.valid_count}</div>
                    <div className="text-[10px] text-emerald-600">Valid</div>
                  </div>
                  <div className="p-2.5 bg-amber-50 rounded-xl border border-amber-200">
                    <div className="font-bold text-amber-700">
                      {importSummary.skipped_db_dup_count + importSummary.skipped_file_dup_count}
                    </div>
                    <div className="text-[10px] text-amber-600">Duplicates</div>
                  </div>
                  <div className="p-2.5 bg-rose-50 rounded-xl border border-rose-200">
                    <div className="font-bold text-rose-700">{importSummary.invalid_count}</div>
                    <div className="text-[10px] text-rose-600">Invalid</div>
                  </div>
                </div>

                {importSummary.preview && importSummary.preview.length > 0 && (
                  <div className="max-h-48 overflow-y-auto rounded-xl border border-slate-200 text-xs">
                    <table className="w-full text-left">
                      <thead className="bg-slate-100 font-bold sticky top-0">
                        <tr>
                          <th className="p-2">Date</th>
                          <th className="p-2">Description</th>
                          <th className="p-2">Category</th>
                          <th className="p-2 text-right">Amount</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {importSummary.preview.map((r, i) => (
                          <tr key={i}>
                            <td className="p-2">{r.txn_date}</td>
                            <td className="p-2">{r.description}</td>
                            <td className="p-2">{r.category}</td>
                            <td className="p-2 text-right font-mono font-bold">
                              ₹{r.amount.toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowImportModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmImport}
                disabled={!importSummary?.valid_count || importing}
                className="px-5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold disabled:opacity-40"
              >
                {importing ? 'Importing...' : `Import ${importSummary?.valid_count || 0} Transactions`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
