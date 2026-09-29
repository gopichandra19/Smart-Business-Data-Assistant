import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
  LayoutDashboard, MessageSquare, Database, BookOpen,
  Brain, Shield, Settings, Lightbulb, LogOut, X, ChevronRight
} from 'lucide-react';
import api from '../api';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Business Chat' },
  { to: '/data-sources', icon: Database, label: 'Data Sources' },
  { to: '/knowledge', icon: BookOpen, label: 'Knowledge' },
  { to: '/memory', icon: Brain, label: 'Memory' },
  { to: '/insights', icon: Lightbulb, label: 'Insights' },
  { to: '/audit', icon: Shield, label: 'Audit Log' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const user = api.getUser();

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-surface-50">
      {/* Sidebar */}
      <aside className={`${collapsed ? 'w-16' : 'w-60'} bg-surface-900 text-white flex flex-col transition-all duration-300 ease-in-out`}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-surface-700/50">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent flex items-center justify-center font-bold text-sm shrink-0">
            SB
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-semibold truncate">Smart Business</h1>
              <p className="text-[10px] text-surface-400">Data Assistant</p>
            </div>
          )}
          <button onClick={() => setCollapsed(!collapsed)} className="ml-auto text-surface-400 hover:text-white p-1 rounded transition-colors">
            {collapsed ? <ChevronRight size={16} /> : <X size={16} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group ${
                  isActive
                    ? 'bg-primary-600/20 text-primary-300 font-medium'
                    : 'text-surface-300 hover:bg-surface-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} className="shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="border-t border-surface-700/50 p-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-accent flex items-center justify-center text-xs font-bold shrink-0">
              {user?.name?.charAt(0) || 'U'}
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{user?.name || 'User'}</p>
                <p className="text-[10px] text-surface-400 capitalize">{user?.role || 'user'}</p>
              </div>
            )}
            <button onClick={handleLogout} className="text-surface-400 hover:text-danger p-1 rounded transition-colors" title="Logout">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
