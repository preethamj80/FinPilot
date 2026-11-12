import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowRight, Loader2, Lock, Mail, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useFinance } from '../../context/FinanceContext';
import AuthBrandShowcase from '../../components/auth/AuthBrandShowcase';
import BrandLogo from '../../components/common/BrandLogo';
import DemoNotice from '../../components/common/DemoNotice';
import { DEMO_MODE } from '../../demo/demoMode';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login, enterDemo } = useAuth();
  const { notify } = useFinance();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password) {
      setError('Please provide both email address and password.');
      return;
    }

    setLoading(true);
    try {
      await login(email.trim(), password);
      notify('Signed in successfully! Welcome to FinPilot.', 'success');
      navigate('/');
    } catch (err) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleExploreDemo = () => {
    enterDemo();
    notify('You are exploring FinPilot with synthetic demo data.', 'success');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[var(--color-outer-bg)] flex items-center justify-center p-4 sm:p-6 lg:p-10 font-sans selection:bg-teal-500 selection:text-slate-950">
      {/* Centered Main Container with Soft Shadow and Rounded Corners */}
      <div className="max-w-6xl w-full bg-[var(--color-card-bg)] rounded-3xl sm:rounded-[32px] shadow-2xl border border-[var(--color-border)] overflow-hidden flex flex-col lg:flex-row">
        {/* ─────────────────────────────────────────────────────────────
            LEFT SIDE (43% width): Login Form
        ───────────────────────────────────────────────────────────── */}
        <div className="w-full lg:w-[43%] p-8 sm:p-10 lg:p-12 flex flex-col justify-between bg-white shrink-0">
          <div>
            {/* FinPilot Header & Label */}
            <div className="flex items-center justify-between gap-3 mb-8">
              <div className="flex items-center gap-3">
                <BrandLogo size={48} className="rounded-2xl" />
                <div>
                  <span className="text-xl font-extrabold tracking-tight text-slate-900">
                    FinPilot
                  </span>
                  <span className="block text-[10px] font-bold text-teal-700 uppercase tracking-widest -mt-0.5">
                    Personal Finance Intelligence
                  </span>
                </div>
              </div>

              <span className="text-[11px] font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200/60 hidden sm:inline-block">
                Secure Vault
              </span>
            </div>

            {/* Welcome Heading */}
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Welcome back.
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1.5 leading-relaxed">
                Take control of your finances and make every money decision count.
              </p>
            </div>

            {/* Error Notification */}
            {error && (
              <div className="mb-5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold leading-relaxed flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Login Form */}
            {DEMO_MODE ? (
              <div className="space-y-4">
                <DemoNotice className="mb-5" />
                <button
                  type="button"
                  onClick={handleExploreDemo}
                  className="w-full py-3.5 px-5 rounded-2xl bg-[var(--color-gold)] hover:brightness-105 text-[#17221D] font-bold text-sm shadow-md active:scale-[0.99] transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  Explore Demo <ArrowRight className="w-4 h-4" />
                </button>
                <p className="text-center text-xs text-slate-500">
                  No account or credentials needed. Try the sample dashboard and tools.
                </p>
              </div>
            ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email Field */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    autoFocus
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-2xl border border-slate-200 focus:border-teal-500 focus:bg-white focus:ring-3 focus:ring-teal-500/15 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-hidden bg-slate-50/60 transition-all"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-bold text-slate-700">Password</label>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-11 py-3 rounded-2xl border border-slate-200 focus:border-teal-500 focus:bg-white focus:ring-3 focus:ring-teal-500/15 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-hidden bg-slate-50/60 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 cursor-pointer transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Sign In Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 px-5 rounded-2xl bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white font-bold text-sm shadow-md shadow-teal-800/20 active:scale-[0.99] transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Signing in...
                    </>
                  ) : (
                    <>
                      Sign In to FinPilot <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
            )}
          </div>

          {/* Bottom Switcher */}
          {!DEMO_MODE && (
            <div className="mt-8 pt-6 border-t border-slate-100 text-center text-xs text-slate-500">
              Don't have an account yet?{' '}
              <Link
                to="/register"
                className="font-bold text-teal-600 hover:text-teal-700 hover:underline inline-flex items-center gap-0.5"
              >
                Create an account
              </Link>
            </div>
          )}
        </div>

        {/* ─────────────────────────────────────────────────────────────
            RIGHT SIDE (57% width): Brand Showcase
        ───────────────────────────────────────────────────────────── */}
        <div className="w-full lg:w-[57%] p-0 flex">
          <AuthBrandShowcase />
        </div>
      </div>
    </div>
  );
}
