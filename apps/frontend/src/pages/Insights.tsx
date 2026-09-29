import { useEffect, useState } from 'react';
import { Lightbulb, AlertTriangle, Info } from 'lucide-react';
import api from '../api';

const SEVERITY_STYLES: Record<string, { bg: string; icon: React.ElementType; color: string }> = {
  info: { bg: 'bg-primary-50 border-primary-200', icon: Info, color: 'text-primary-600' },
  warning: { bg: 'bg-warning/5 border-warning/20', icon: AlertTriangle, color: 'text-warning' },
  critical: { bg: 'bg-danger/5 border-danger/20', icon: AlertTriangle, color: 'text-danger' },
};

export default function InsightsPage() {
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getInsights().then(setInsights).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Insights</h1>
        <p className="text-sm text-surface-500 mt-0.5">Rule-based prototype insights detected from business data</p>
      </div>

      <div className="bg-surface-100 rounded-lg px-4 py-2.5 flex items-center gap-2 text-xs text-surface-500">
        <Info size={14} />
        These are rule-based prototype insights. Production would include ML/anomaly detection models.
      </div>

      {loading ? (
        <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-28 bg-surface-100 rounded-xl animate-pulse" />)}</div>
      ) : insights.length === 0 ? (
        <div className="text-center py-16 text-surface-400">
          <Lightbulb size={40} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No insights detected</p>
        </div>
      ) : (
        <div className="space-y-3">
          {insights.map((insight, i) => {
            const style = SEVERITY_STYLES[insight.severity] || SEVERITY_STYLES.info;
            const Icon = style.icon;
            return (
              <div
                key={insight.id || i}
                className={`rounded-xl border p-5 ${style.bg} animate-fade-in transition-shadow hover:shadow-md`}
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-9 h-9 rounded-lg bg-white/80 flex items-center justify-center shrink-0 ${style.color}`}>
                    <Icon size={18} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-surface-800">{insight.title}</h3>
                    <p className="text-xs text-surface-600 mt-1 leading-relaxed">{insight.description}</p>
                    <div className="flex items-center gap-3 mt-3">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium ${style.color} bg-white/60`}>
                        {insight.severity}
                      </span>
                      <span className="text-[10px] text-surface-400">{insight.category?.replace('_', ' ')}</span>
                      <span className="text-[10px] text-surface-400">
                        {new Date(insight.detected_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
