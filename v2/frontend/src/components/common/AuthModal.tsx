import React, { useState } from 'react';
import { X, Lock, Mail, User as UserIcon, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, authModalMode, closeAuthModal, login, register, openAuthModal } = useAuth();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isAuthModalOpen) return null;

  const isLogin = authModalMode === 'login';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await login(username, password);
      } else {
        if (!email.includes('@')) {
          throw new Error('Please enter a valid email address.');
        }
        await register(username, email, password);
      }
      closeAuthModal();
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axErr = err as { response?: { data?: { detail?: string } } };
        setError(axErr.response?.data?.detail || 'Authentication failed. Please verify credentials.');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      {/* Modal Card */}
      <div className="relative w-full max-w-md p-8 rounded-3xl bg-[#090f24]/95 border border-cyan-500/30 shadow-neon-cyan text-slate-100 overflow-hidden">
        {/* Holographic background glows */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-3">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold text-holo-gradient">
            {isLogin ? 'Welcome Back' : 'Join MovieRec Universe'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {isLogin
              ? 'Sign in to access your personal SVD recommendations'
              : 'Create your account for personalized AI recommendations'}
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex rounded-xl bg-white/5 p-1 mb-6 border border-white/10">
          <button
            type="button"
            onClick={() => {
              setError(null);
              openAuthModal('login');
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              isLogin ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setError(null);
              openAuthModal('register');
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              !isLogin ? 'bg-cyan-500 text-black shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Username</label>
            <div className="relative">
              <UserIcon className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="cinéphile_99"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 focus:border-cyan-400 focus:outline-none text-sm text-white placeholder-slate-500 transition-colors"
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@galaxy.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 focus:border-cyan-400 focus:outline-none text-sm text-white placeholder-slate-500 transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 focus:border-cyan-400 focus:outline-none text-sm text-white placeholder-slate-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-400 via-teal-400 to-purple-500 text-black font-semibold text-sm hover:opacity-95 transition-opacity shadow-neon-cyan mt-2 disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
};
