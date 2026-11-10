import React, { useState, useEffect } from 'react';
import {
  LineChart as LineChartIcon,
  TrendingUp,
  AlertTriangle,
  BrainCircuit,
  Search,
  Sparkles,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../api/client';
import { formatCurrency, getCategoryColorMap } from '../../utils/categories';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function Insights() {
  const [activeTab, setActiveTab] = useState('forecast');
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [categorizerStatus, setCategorizerStatus] = useState(null);
  const [testDesc, setTestDesc] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testingCategory, setTestingCategory] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const [fRes, aRes, pRes, cRes] = await Promise.allSettled([
          api.get('/api/insights/forecast'),
          api.get('/api/insights/anomalies'),
          api.get('/api/insights/patterns'),
          api.get('/api/insights/categorization'),
        ]);

        if (!isMounted) return;
        if (fRes.status === 'fulfilled') setForecast(fRes.value);
        if (aRes.status === 'fulfilled') setAnomalies(aRes.value);
        if (pRes.status === 'fulfilled') setPatterns(pRes.value);
        if (cRes.status === 'fulfilled') setCategorizerStatus(cRes.value);
      } catch {
        // Fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleTestCategory = async (e) => {
    e.preventDefault();
    if (!testDesc.trim()) return;
    setTestingCategory(true);
    setTestResult(null);
    try {
      const res = await api.post('/api/insights/categorization/test', {
        description: testDesc.trim(),
        txn_type: 'Expense',
      });
      setTestResult(res);
    } catch {
      // Fallback
    } finally {
      setTestingCategory(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Analysing your spending trends & forecasts..." />;
  }

  const overall = forecast?.overall || {};
  const byCat = forecast?.by_category || [];
  const anomalyList = anomalies?.anomalies || [];
  const clusters = patterns?.clusters || [];
  const categoryColors = getCategoryColorMap([
    ...byCat.map((item) => item.category),
    ...anomalyList.map((item) => item.category),
  ]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200/80 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Smart Spending Insights
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            See your projected expenses for next month, spot unusual transactions, and explore your spending habits.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 p-1.5 bg-slate-100 rounded-2xl text-xs font-semibold overflow-x-auto">
          {[
            { id: 'forecast', label: 'Next-Month Forecast' },
            { id: 'anomalies', label: `Unusual Spending (${anomalyList.length})` },
            { id: 'patterns', label: 'Spending Habits' },
            { id: 'categorizer', label: 'Category Detector' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-xl transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-white text-slate-900 shadow-xs font-bold'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* TAB 1: Expense Forecasting */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-card">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Predicted Next-Month Outflow
              </span>
              <div className="text-2xl font-extrabold text-slate-900 mt-2 font-tabular">
                {overall.prediction ? formatCurrency(overall.prediction) : 'Insufficient Data'}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Best validated model: <span className="font-bold text-teal-700">{overall.best_model || 'None'}</span>
              </p>
            </div>

            <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-card">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                80% Confidence Range
              </span>
              <div className="text-lg font-bold text-slate-900 mt-2 font-tabular">
                {overall.interval_80
                  ? `${formatCurrency(overall.interval_80[0])} – ${formatCurrency(overall.interval_80[1])}`
                  : 'N/A'}
              </div>
              <p className="text-xs text-slate-500 mt-1">Expected range under typical spending variations</p>
            </div>

            <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-card">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                95% Outer Bounds
              </span>
              <div className="text-lg font-bold text-slate-900 mt-2 font-tabular">
                {overall.interval_95
                  ? `${formatCurrency(overall.interval_95[0])} – ${formatCurrency(overall.interval_95[1])}`
                  : 'N/A'}
              </div>
              <p className="text-xs text-slate-500 mt-1">Accounts for potential emergency spikes</p>
            </div>
          </div>

          {/* By-Category Forecast Breakdown */}
          {byCat.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <h2 className="text-base font-bold text-slate-900 mb-4">Projected Spending by Category</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold">
                    <tr>
                      <th className="p-3">Category</th>
                      <th className="p-3 text-right">Predicted Amount</th>
                      <th className="p-3 text-right">History Avg</th>
                      <th className="p-3">Trend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {byCat.map((c, i) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="p-3 font-semibold text-slate-900">
                          <span className="inline-flex items-center gap-2">
                            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: categoryColors[c.category] }} aria-hidden="true" />
                            {c.category}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono font-bold" style={{ color: categoryColors[c.category] }}>
                          {formatCurrency(c.forecast || c.predicted_amount || 0)}
                        </td>
                        <td className="p-3 text-right font-mono text-slate-500">
                          {formatCurrency(c.historical_avg || 0)}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                              c.trend === 'increasing'
                                ? 'bg-rose-50 text-rose-700'
                                : c.trend === 'decreasing'
                                ? 'bg-emerald-50 text-emerald-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {c.trend || 'stable'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Statistical Anomaly Detection */}
      {activeTab === 'anomalies' && (
        <div className="space-y-4">
          <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-start gap-3">
            <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block mb-0.5">Spending Review Notice</span>
              Flags highlight transactions that were noticeably higher than your typical spending in that category, helping you review your expenses easily. These flags do not mean unauthorized charges or fraud.
            </div>
          </div>

          {anomalyList.length === 0 ? (
            <div className="bg-white p-12 rounded-2xl border border-slate-200/80 text-center text-slate-500">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-900">No anomalous spending detected</h3>
              <p className="text-xs text-slate-400 mt-1">
                All {anomalies?.total_scanned || 0} screened transactions fell within expected statistical thresholds.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">
                  {anomalyList.length} Flagged Outliers Screened
                </span>
                <span className="text-xs text-slate-500">
                  Total screened: {anomalies?.total_scanned || 0}
                </span>
              </div>
              <div className="divide-y divide-slate-100 text-xs">
                {anomalyList.map((item, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-50 flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">{item.description}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                          {item.reason || item.flag || 'Unusual Outlier'}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">
                        Date: <span className="font-mono">{item.txn_date}</span> · Category:{' '}
                        <span className="inline-flex items-center gap-1.5 font-semibold">
                          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: categoryColors[item.category] }} aria-hidden="true" />
                          {item.category}
                        </span>
                      </div>
                    </div>
                    <div className="text-right font-mono font-bold text-base text-slate-900">
                      {formatCurrency(item.amount)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Spending Pattern Clusters */}
      {activeTab === 'patterns' && (
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
            <h2 className="text-base font-bold text-slate-900 mb-2">Your Spending Patterns</h2>
            <p className="text-xs text-slate-600 mb-4">{patterns?.summary || 'Spending pattern insights'}</p>

            {clusters.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                Need at least 3 months of expense history to detect spending patterns.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {clusters.map((c, i) => (
                  <div key={i} className="p-4 rounded-xl border border-slate-100 bg-slate-50 space-y-2">
                    <div className="flex justify-between items-center text-xs font-bold text-slate-900">
                      <span>{c.cluster_name || `Pattern #${i + 1}`}</span>
                      <span className="text-teal-700">{c.month_count || 0} months</span>
                    </div>
                    <p className="text-xs text-slate-600">{c.description || c.profile}</p>
                    <div className="text-xs font-mono font-bold text-slate-800">
                      Avg Outflow: {formatCurrency(c.avg_monthly_spending || c.avg_spend || 0)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: ML Categorizer Diagnostics & Interactive Test */}
      {activeTab === 'categorizer' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
            <h2 className="text-base font-bold text-slate-900">Category Auto-Detector</h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50">
                <span className="text-slate-500">Detection Engine:</span>
                <span className="font-bold text-slate-900">
                  {categorizerStatus?.model_type || 'AI Auto-Categorizer'}
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50">
                <span className="text-slate-500">Learned Transactions:</span>
                <span className="font-bold text-slate-900">
                  {categorizerStatus?.training_samples || 0} transactions
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50">
                <span className="text-slate-500">Status:</span>
                <span className="font-bold text-emerald-600">
                  {categorizerStatus?.model_loaded ? 'Trained & Active' : 'Keyword Fallback Active'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
            <h2 className="text-base font-bold text-slate-900">Try Auto-Category Detection</h2>
            <form onSubmit={handleTestCategory} className="space-y-3 text-xs">
              <input
                type="text"
                placeholder="Type a merchant name (e.g. Swiggy, Uber, Shell Fuel, Apollo Pharmacy)"
                value={testDesc}
                onChange={(e) => setTestDesc(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-300 text-sm outline-hidden focus:border-teal-500"
              />
              <button
                type="submit"
                disabled={testingCategory}
                className="w-full py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl font-bold cursor-pointer"
              >
                {testingCategory ? 'Detecting...' : 'Detect Category'}
              </button>
            </form>

            {testResult && (
              <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-xs space-y-1">
                <div className="text-teal-900 font-bold text-sm">
                  Predicted: {testResult.category}
                </div>
                <div className="text-teal-700">Method: {testResult.method}</div>
                {testResult.confidence && (
                  <div className="text-teal-700">
                    Confidence: {(testResult.confidence * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
