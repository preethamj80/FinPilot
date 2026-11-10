import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ text = 'Loading financial data...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Loader2 className="w-9 h-9 text-teal-600 animate-spin mb-3" />
      <p className="text-sm text-slate-500 font-medium">{text}</p>
    </div>
  );
}
