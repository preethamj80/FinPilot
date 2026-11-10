/**
 * FinPilot Category Utilities & Configuration
 * Provides icons, colors, labels, and aliases across the application.
 */

export const DEFAULT_EXPENSE_CATEGORIES = [
  'Food & Dining',
  'Groceries',
  'Rent & Housing',
  'Transportation',
  'Shopping',
  'Utilities',
  'Health & Medical',
  'Education',
  'Entertainment',
  'Travel',
  'Personal Care',
  'Insurance',
  'Subscriptions',
  'Miscellaneous',
  'Other',
];

export const DEFAULT_INCOME_CATEGORIES = [
  'Salary',
  'Freelance',
  'Investment Returns',
  'Business Income',
  'Other Income',
];

// Shared category colors used by charts, category lists, budget cards, and
// transaction labels. Canonical expense categories keep their approved colors.
export const CATEGORY_COLOR_PALETTE = Object.freeze({
  'Rent & Housing': '#D6B875',
  Travel: '#86A9C7',
  Groceries: '#55B88A',
  'Food & Dining': '#E27D78',
  'Health & Medical': '#E6A36F',
  Education: '#A78BDB',
  Shopping: '#8298D6',
  Utilities: '#A4B9A8',
  Entertainment: '#D18FB0',
  Insurance: '#B7A1D9',
  Transportation: '#67C5C2',
  'Personal Care': '#D39A75',
  Subscriptions: '#C28DCD',
  Miscellaneous: '#C0C978',
  Other: '#B8A08C',
  // Historical category names remain visually consistent with their meaning.
  Food: '#E27D78',
  Transport: '#67C5C2',
  Rent: '#D6B875',
  Health: '#E6A36F',
  Salary: '#55B88A',
  Freelance: '#55B88A',
  'Investment Returns': '#55B88A',
  'Business Income': '#55B88A',
  'Other Income': '#55B88A',
  Investment: '#55B88A',
});

const CANONICAL_EXPENSE_ORDER = [
  'Food & Dining', 'Groceries', 'Rent & Housing', 'Transportation', 'Shopping',
  'Utilities', 'Health & Medical', 'Education', 'Entertainment', 'Travel',
  'Personal Care', 'Insurance', 'Subscriptions', 'Miscellaneous', 'Other',
];

function hashCategoryName(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function hslToHex(hue, saturation, lightness) {
  const s = saturation / 100;
  const l = lightness / 100;
  const chroma = (1 - Math.abs(2 * l - 1)) * s;
  const x = chroma * (1 - Math.abs(((hue / 60) % 2) - 1));
  const match = l - chroma / 2;
  let rgb;
  if (hue < 60) rgb = [chroma, x, 0];
  else if (hue < 120) rgb = [x, chroma, 0];
  else if (hue < 180) rgb = [0, chroma, x];
  else if (hue < 240) rgb = [0, x, chroma];
  else if (hue < 300) rgb = [x, 0, chroma];
  else rgb = [chroma, 0, x];
  return `#${rgb.map((value) => Math.round((value + match) * 255).toString(16).padStart(2, '0')).join('')}`.toUpperCase();
}

function customCategoryColor(name, attempt = 0) {
  const hash = hashCategoryName(name);
  const hue = ((hash % 360) + attempt * 137.508) % 360;
  const saturation = 58 + ((hash >>> 8) % 9) + (Math.floor(attempt / 360) % 12);
  const lightness = 64 + ((hash >>> 16) % 7) + (Math.floor(attempt / 4320) % 8);
  return hslToHex(hue, saturation, lightness);
}

/** Return stable, collision-resolved colors for the supplied category set. */
export function getCategoryColorMap(categories = []) {
  const names = [...new Set((categories || []).filter(Boolean).map((category) => String(category)))];
  const included = new Set(names);
  const colors = Object.create(null);
  const used = new Set();

  for (const category of CANONICAL_EXPENSE_ORDER) {
    if (included.has(category)) {
      colors[category] = CATEGORY_COLOR_PALETTE[category];
      used.add(colors[category]);
    }
  }

  for (const category of names.filter((name) => !Object.prototype.hasOwnProperty.call(colors, name)).sort((a, b) => a.localeCompare(b))) {
    const preferred = Object.prototype.hasOwnProperty.call(CATEGORY_COLOR_PALETTE, category)
      ? CATEGORY_COLOR_PALETTE[category]
      : undefined;
    if (preferred && !used.has(preferred)) {
      colors[category] = preferred;
      used.add(preferred);
      continue;
    }
    let attempt = 0;
    let color = customCategoryColor(category, attempt);
    while (used.has(color)) {
      attempt += 1;
      color = customCategoryColor(category, attempt);
    }
    colors[category] = color;
    used.add(color);
  }

  return colors;
}

export function getCategoryColor(category) {
  if (!category) return CATEGORY_COLOR_PALETTE.Other;
  return getCategoryColorMap([category])[category];
}

export const CATEGORY_METADATA = {
  'Food & Dining': { icon: 'Utensils', color: 'text-teal-300 bg-slate-800 border-slate-700', hex: '#E27D78' },
  'Groceries': { icon: 'ShoppingBag', color: 'text-emerald-400 bg-slate-800 border-slate-700', hex: '#55B88A' },
  'Rent & Housing': { icon: 'Home', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#D6B875' },
  'Transportation': { icon: 'Car', color: 'text-teal-300 bg-slate-800 border-slate-700', hex: '#67C5C2' },
  'Shopping': { icon: 'Tag', color: 'text-rose-400 bg-slate-800 border-slate-700', hex: '#8298D6' },
  'Utilities': { icon: 'Zap', color: 'text-teal-300 bg-slate-800 border-slate-700', hex: '#A4B9A8' },
  'Health & Medical': { icon: 'HeartPulse', color: 'text-rose-400 bg-slate-800 border-slate-700', hex: '#E6A36F' },
  'Medical & Healthcare': { icon: 'HeartPulse', color: 'text-rose-400 bg-slate-800 border-slate-700', hex: '#E6A36F' },
  'Education': { icon: 'GraduationCap', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#A78BDB' },
  'Entertainment': { icon: 'Film', color: 'text-rose-400 bg-slate-800 border-slate-700', hex: '#D18FB0' },
  'Travel': { icon: 'Plane', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#86A9C7' },
  'Personal Care': { icon: 'Sparkles', color: 'text-teal-300 bg-slate-800 border-slate-700', hex: '#D39A75' },
  'Insurance': { icon: 'Shield', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#B7A1D9' },
  'Subscriptions': { icon: 'CreditCard', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#C28DCD' },
  'Miscellaneous': { icon: 'Package', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#C0C978' },
  'Salary': { icon: 'Briefcase', color: 'text-emerald-400 bg-slate-800 border-slate-700', hex: '#55B88A' },
  'Freelance': { icon: 'Laptop', color: 'text-emerald-400 bg-slate-800 border-slate-700', hex: '#55B88A' },
  'Investment Returns': { icon: 'TrendingUp', color: 'text-emerald-400 bg-slate-800 border-slate-700', hex: '#55B88A' },
  'Business Income': { icon: 'Building', color: 'text-emerald-400 bg-slate-800 border-slate-700', hex: '#55B88A' },
  'Other Income': { icon: 'PlusCircle', color: 'text-emerald-400 bg-slate-800 border-slate-700', hex: '#55B88A' },
  'Other': { icon: 'Folder', color: 'text-slate-300 bg-slate-800 border-slate-700', hex: '#A8B2AA' },
  // Legacy aliases map seamlessly:
  'Food': { icon: 'Utensils', color: 'text-amber-600 bg-amber-50 border-amber-200', hex: '#E27D78' },
  'Transport': { icon: 'Car', color: 'text-cyan-600 bg-cyan-50 border-cyan-200', hex: '#67C5C2' },
  'Rent': { icon: 'Home', color: 'text-blue-600 bg-blue-50 border-blue-200', hex: '#D6B875' },
  'Health': { icon: 'HeartPulse', color: 'text-rose-600 bg-rose-50 border-rose-200', hex: '#E6A36F' },
  'Investment': { icon: 'TrendingUp', color: 'text-blue-700 bg-blue-50 border-blue-200', hex: '#55B88A' },
};

export function getCategoryMeta(cat) {
  if (!cat) return { ...CATEGORY_METADATA['Other'], hex: CATEGORY_COLOR_PALETTE.Other };
  const metadata = CATEGORY_METADATA[cat] || {
    icon: 'Folder',
    color: 'text-slate-600 bg-slate-50 border-slate-200',
    hex: CATEGORY_COLOR_PALETTE.Other,
  };
  return { ...metadata, hex: getCategoryColor(cat) };
}

export function formatCurrency(amount) {
  const num = typeof amount === 'number' ? amount : parseFloat(amount) || 0;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(num);
}
