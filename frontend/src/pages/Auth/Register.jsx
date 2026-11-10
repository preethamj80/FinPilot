import React, { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowRight, Loader2, Lock, Mail, User, Check, X, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useFinance } from '../../context/FinanceContext';
import AuthBrandShowcase from '../../components/auth/AuthBrandShowcase';
import BrandLogo from '../../components/common/BrandLogo';

export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register } = useAuth();
  const { notify } = useFinance();
  const navigate = useNavigate();

  // Password rules validation
  const rules = useMemo(() => {
    return {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      number: /[0-9]/.test(password),
      matches: password.length > 0 && password === confirmPassword,
    };
  }, [password, confirmPassword]);

  // Password strength calculation
  const strength = useMemo(() => {
    if (!password) return { level: 0, label: 'None', color: 'bg-slate-200', text: 'text-slate-400' };
    let score = 0;
    if (rules.length) score += 1;
    if (rules.uppercase) score += 1;
    if (rules.number) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    if (password.length >= 12) score += 1;

    if (score <= 1) return { level: 1, label: 'Weak', color: 'bg-rose-500', text: 'text-rose-600' };
    if (score === 2) return { level: 2, label: 'Fair', color: 'bg-amber-500', text: 'text-amber-600' };
    if (score === 3) return { level: 3, label: 'Good', color: 'bg-teal-500', text: 'text-teal-600' };
    return { level: 4, label: 'Strong', color: 'bg-emerald-500', text: 'text-emerald-600' };
  }, [password, rules]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!rules.length || !rules.uppercase || !rules.number) {
      setError('Please meet all password requirements before continuing.');
      return;
    }

    if (!rules.matches) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await register(fullName.trim(), email.trim(), password, confirmPassword);
      notify('Account created successfully! Welcome to FinPilot.', 'success');
      navigate('/');
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-outer-bg)] flex items-center justify-center p-4 sm:p-6 lg:p-10 font-sans selection:bg-teal-500 selection:text-slate-950">
      {/* Centered Main Container with Soft Shadow and Rounded Corners */}
      <div className="max-w-6xl w-full bg-[var(--color-card-bg)] rounded-3xl sm:rounded-[32px] shadow-2xl border border-[var(--color-border)] overflow-hidden flex flex-col lg:flex-row">
        {/* ─────────────────────────────────────────────────────────────
            LEFT SIDE (43% width): Register Form
        ───────────────────────────────────────────────────────────── */}
        <div className="w-full lg:w-[43%] p-8 sm:p-10 lg:p-12 flex flex-col justify-between bg-white shrink-0">
          <div>
            {/* FinPilot Header & Label */}
            <div className="flex items-center justify-between gap-3 mb-6">
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

              <span className="text-[11px] font-semibold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-200/60 hidden sm:inline-block">
                Create Account
              </span>
            </div>

            {/* Welcome Heading */}
            <div className="mb-5">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Create your account.
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1 leading-relaxed">
                Take control of your finances and make every money decision count.
              </p>
            </div>

            {/* Error Notification */}
            {error && (
              <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold leading-relaxed flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Sign Up Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {/* Full Name */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    autoFocus
                    placeholder="Your legal or preferred name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 focus:bg-white focus:ring-3 focus:ring-teal-500/15 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-hidden bg-slate-50/60 transition-all"
                  />
                </div>
              </div>

              {/* Email Address */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 focus:bg-white focus:ring-3 focus:ring-teal-500/15 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-hidden bg-slate-50/60 transition-all"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-11 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 focus:bg-white focus:ring-3 focus:ring-teal-500/15 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-hidden bg-slate-50/60 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 cursor-pointer transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="Re-enter your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 focus:border-teal-500 focus:bg-white focus:ring-3 focus:ring-teal-500/15 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 outline-hidden bg-slate-50/60 transition-all"
                  />
                </div>
              </div>

              {/* Password Strength Meter & Real-Time Rule Check */}
              {password && (
                <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-[11px]">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Security Strength:</span>
                    <span className={`font-bold ${strength.text}`}>{strength.label}</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${strength.color} transition-all duration-300`}
                      style={{ width: `${(strength.level / 4) * 100}%` }}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-1.5 pt-1 text-slate-500">
                    <div className="flex items-center gap-1.5">
                      {rules.length ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <X className="w-3.5 h-3.5 text-slate-400" />
                      )}
                      <span className={rules.length ? 'text-emerald-700 font-medium' : ''}>
                        8+ characters
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {rules.uppercase ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <X className="w-3.5 h-3.5 text-slate-400" />
                      )}
                      <span className={rules.uppercase ? 'text-emerald-700 font-medium' : ''}>
                        Uppercase letter
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {rules.number ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <X className="w-3.5 h-3.5 text-slate-400" />
                      )}
                      <span className={rules.number ? 'text-emerald-700 font-medium' : ''}>
                        Number (0-9)
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {rules.matches ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <X className="w-3.5 h-3.5 text-slate-400" />
                      )}
                      <span className={rules.matches ? 'text-emerald-700 font-medium' : ''}>
                        Passwords match
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-5 rounded-2xl bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white font-bold text-sm shadow-md shadow-teal-800/20 active:scale-[0.99] transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Creating Account...
                    </>
                  ) : (
                    <>
                      Create FinPilot Account <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Bottom Switcher */}
          <div className="mt-6 pt-4 border-t border-slate-100 text-center text-xs text-slate-500">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-bold text-teal-600 hover:text-teal-700 hover:underline inline-flex items-center gap-0.5"
            >
              Sign in
            </Link>
          </div>
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
