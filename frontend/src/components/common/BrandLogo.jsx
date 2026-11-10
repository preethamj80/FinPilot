import React, { useState } from 'react';
import mascot from '../../assets/finpilot-mascot.png';

export default function BrandLogo({ size = 48, className = '' }) {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <span
      role="img"
      aria-label="FinPilot logo"
      className={`inline-flex shrink-0 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}
      style={{ width: size, height: size }}
    >
      {imageFailed ? (
        <span className="font-bold leading-none text-[#D6B875]" style={{ fontSize: size * 0.48 }}>
          F
        </span>
      ) : (
        <img
          src={mascot}
          alt=""
          aria-hidden="true"
          onError={() => setImageFailed(true)}
          className="h-full w-full object-contain"
        />
      )}
    </span>
  );
}
