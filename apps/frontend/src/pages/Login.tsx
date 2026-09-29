import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight } from 'lucide-react';
import api from '../api';

export default function LoginPage() {
  const [email, setEmail] = useState('analyst@example.local');
  const [password, setPassword] = useState('analyst123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const demoUsers = [
    { email: 'admin@example.local', password: 'admin123', role: 'Admin' },
    { email: 'analyst@example.local', password: 'analyst123', role: 'Analyst' },
    { email: 'manager@example.local', password: 'manager123', role: 'Manager' },
    { email: 'employee@example.local', password: 'employee123', role: 'Employee' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-surface-900 via-surface-800 to-surface-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent mx-auto flex items-center justify-center text-white font-bold text-xl mb-4 shadow-lg shadow-primary-500/20">
            SB
          </div>
          <h1 className="text-2xl font-bold text-white">Smart Business</h1>
          <p className="text-surface-400 text-sm mt-1">Data Assistant</p>
        </div>

        {/* Login Form */}
        <div className="bg-surface-800/60 backdrop-blur-xl rounded-2xl border border-surface-700/50 p-8 shadow-2xl">
          <h2 className="text-lg font-semibold text-white mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-surface-300 mb-1.5">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-surface-900/60 border border-surface-600/50 rounded-xl text-white text-sm placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50 transition-all"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-surface-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-surface-900/60 border border-surface-600/50 rounded-xl text-white text-sm placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50 transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="text-danger text-xs bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white font-medium rounded-xl text-sm transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg shadow-primary-500/20"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Sign In <ArrowRight size={16} /></>
              )}
            </button>
          </form>

          {/* Demo Users */}
          <div className="mt-6 pt-6 border-t border-surface-700/50">
            <p className="text-[11px] text-surface-400 mb-3 uppercase tracking-wider font-medium">Demo Accounts</p>
            <div className="grid grid-cols-2 gap-2">
              {demoUsers.map(u => (
                <button
                  key={u.email}
                  onClick={() => { setEmail(u.email); setPassword(u.password); }}
                  className="text-left px-3 py-2 rounded-lg bg-surface-900/40 border border-surface-700/30 hover:border-primary-500/30 hover:bg-surface-900/60 transition-all group"
                >
                  <span className="text-xs font-medium text-surface-200 group-hover:text-primary-300">{u.role}</span>
                  <span className="block text-[10px] text-surface-500 truncate">{u.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-[11px] text-surface-500 mt-6">
          Prototype • Development Authentication Only
        </p>
      </div>
    </div>
  );
}
