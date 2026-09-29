import { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  Database, Users, ShoppingCart, DollarSign, BookOpen,
  Brain, Search, Lightbulb
} from 'lucide-react';
import api from '../api';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

interface DashboardData {
  cards: { label: string; value: any; icon?: string }[];
  revenue_by_region: { region: string; revenue: number }[];
  revenue_by_month: { month: string; revenue: number }[];
  top_customers: { name: string; segment: string; revenue: number }[];
  sales_by_product: { category: string; revenue: number; orders: number }[];
  recent_insights: { title: string; description: string; severity: string }[];
}

const ICON_MAP: Record<string, React.ElementType> = {
  database: Database, users: Users, 'shopping-cart': ShoppingCart,
  'dollar-sign': DollarSign, book: BookOpen, brain: Brain,
  search: Search,
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (!data) return <div className="p-8 text-surface-500">Failed to load dashboard</div>;

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Dashboard</h1>
          <p className="text-sm text-surface-500 mt-0.5">Business intelligence overview</p>
        </div>
        <div className="text-xs text-surface-400 bg-white px-3 py-1.5 rounded-lg border border-surface-200">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {data.cards.map((card, i) => {
          const Icon = ICON_MAP[card.icon || 'database'] || Database;
          return (
            <div key={i} className="bg-white rounded-xl border border-surface-200 p-4 hover:shadow-md hover:border-primary-200 transition-all duration-200 animate-fade-in" style={{ animationDelay: `${i * 50}ms` }}>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center">
                  <Icon size={16} className="text-primary-500" />
                </div>
              </div>
              <p className="text-lg font-bold text-surface-900">{card.value}</p>
              <p className="text-[11px] text-surface-500 mt-0.5 leading-tight">{card.label}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue by Region */}
        <div className="bg-white rounded-xl border border-surface-200 p-5">
          <h3 className="text-sm font-semibold text-surface-800 mb-4">Revenue by Region</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.revenue_by_region}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="region" tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(val: any) => [`$${Number(val || 0).toLocaleString()}`, 'Revenue']}
                contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
              />
              <Bar dataKey="revenue" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue Trend */}
        <div className="bg-white rounded-xl border border-surface-200 p-5">
          <h3 className="text-sm font-semibold text-surface-800 mb-4">Revenue Trend (12 Months)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.revenue_by_month}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 10 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(val: any) => [`$${Number(val || 0).toLocaleString()}`, 'Revenue']}
                contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
              />
              <Line type="monotone" dataKey="revenue" stroke="#8b5cf6" strokeWidth={2.5} dot={{ r: 3, fill: '#8b5cf6' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Sales by Product */}
        <div className="bg-white rounded-xl border border-surface-200 p-5">
          <h3 className="text-sm font-semibold text-surface-800 mb-4">Sales by Product Category</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={data.sales_by_product} dataKey="revenue" nameKey="category" cx="50%" cy="50%" outerRadius={85} innerRadius={45} strokeWidth={2}>
                {data.sales_by_product.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(val: any) => `$${Number(val || 0).toLocaleString()}`} contentStyle={{ borderRadius: 12, fontSize: 12 }} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Customers */}
        <div className="bg-white rounded-xl border border-surface-200 p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-surface-800 mb-4">Top Customers by Revenue</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-100">
                  <th className="text-left py-2 text-xs font-medium text-surface-500">#</th>
                  <th className="text-left py-2 text-xs font-medium text-surface-500">Customer</th>
                  <th className="text-left py-2 text-xs font-medium text-surface-500">Segment</th>
                  <th className="text-right py-2 text-xs font-medium text-surface-500">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.top_customers.map((c, i) => (
                  <tr key={i} className="border-b border-surface-50 hover:bg-surface-50 transition-colors">
                    <td className="py-2.5 text-surface-400 text-xs">{i + 1}</td>
                    <td className="py-2.5 font-medium text-surface-800">{c.name}</td>
                    <td className="py-2.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        c.segment === 'Enterprise' ? 'bg-primary-50 text-primary-700' :
                        c.segment === 'Mid-Market' ? 'bg-accent/10 text-accent' :
                        'bg-surface-100 text-surface-600'
                      }`}>{c.segment}</span>
                    </td>
                    <td className="py-2.5 text-right font-mono text-surface-700">${c.revenue.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Insights */}
      {data.recent_insights.length > 0 && (
        <div className="bg-white rounded-xl border border-surface-200 p-5">
          <h3 className="text-sm font-semibold text-surface-800 mb-4 flex items-center gap-2">
            <Lightbulb size={16} className="text-warning" /> AI Insights
          </h3>
          <div className="space-y-2">
            {data.recent_insights.map((insight, i) => (
              <div key={i} className={`p-3 rounded-lg border ${
                insight.severity === 'warning' ? 'bg-warning/5 border-warning/20' : 'bg-primary-50/50 border-primary-100'
              }`}>
                <p className="text-sm font-medium text-surface-800">{insight.title}</p>
                <p className="text-xs text-surface-600 mt-1">{insight.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto animate-pulse">
      <div className="h-8 w-48 bg-surface-200 rounded-lg" />
      <div className="grid grid-cols-7 gap-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="h-24 bg-surface-200 rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="h-80 bg-surface-200 rounded-xl" />
        <div className="h-80 bg-surface-200 rounded-xl" />
      </div>
    </div>
  );
}
