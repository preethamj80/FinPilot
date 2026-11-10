import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeType = 'neutral',
  highlight = false,
  trendText,
  trendDirection, // 'up' | 'down' | 'neutral'
  onClick,
}) {
  let badgeStyles = 'bg-slate-100 text-slate-700 border-slate-200';
  let iconBg = 'bg-slate-100/80 text-slate-700 border-slate-200/60';

  if (badgeType === 'success') {
    badgeStyles = 'bg-emerald-50 text-emerald-700 border-emerald-200/80';
    iconBg = 'bg-emerald-50 text-emerald-700 border-emerald-200/60';
  } else if (badgeType === 'warning') {
    badgeStyles = 'bg-amber-50 text-amber-700 border-amber-200/80';
    iconBg = 'bg-amber-50 text-amber-700 border-amber-200/60';
  } else if (badgeType === 'danger') {
    badgeStyles = 'bg-rose-50 text-rose-700 border-rose-200/80';
    iconBg = 'bg-rose-50 text-rose-700 border-rose-200/60';
  } else if (badgeType === 'teal') {
    badgeStyles = 'bg-teal-50 text-teal-800 border-teal-200/80';
    iconBg = 'bg-teal-50 text-teal-700 border-teal-200/60';
  } else if (badgeType === 'blue') {
    badgeStyles = 'bg-blue-50 text-blue-700 border-blue-200/80';
    iconBg = 'bg-blue-50 text-blue-700 border-blue-200/60';
  }

  return (
    <div
      onClick={onClick}
      className={`relative bg-white rounded-2xl p-5 sm:p-6 transition-all duration-200 border ${
        highlight
          ? 'border-teal-500/50 shadow-sm shadow-teal-500/10 ring-1 ring-teal-500/20 bg-gradient-to-br from-slate-100 via-slate-200 to-slate-100'
          : 'border-slate-200/80 shadow-xs hover:border-slate-300 hover:shadow-md hover:-translate-y-0.5'
      } ${onClick ? 'cursor-pointer' : ''}`}
    >
      {/* Top row: Title and Icon */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
          {title}
        </span>
        {Icon && (
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${iconBg}`}
          >
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Metric value and badge */}
      <div className="flex items-baseline justify-between gap-2 flex-wrap">
        <div className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 font-tabular">
          {value}
        </div>
        {badgeText && (
          <span
            className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${badgeStyles}`}
          >
            {badgeText}
          </span>
        )}
      </div>

      {/* Trend or Subtitle */}
      {(trendText || subtitle) && (
        <div className="mt-2.5 pt-2 border-t border-slate-100/80 flex items-center justify-between text-xs text-slate-500">
          <p className="line-clamp-1">{subtitle}</p>
          {trendText && (
            <span
              className={`shrink-0 text-[11px] font-semibold flex items-center gap-0.5 ${
                trendDirection === 'up'
                  ? 'text-emerald-600'
                  : trendDirection === 'down'
                  ? 'text-rose-600'
                  : 'text-slate-500'
              }`}
            >
              {trendText}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
