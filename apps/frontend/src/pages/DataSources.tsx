import { useEffect, useState } from 'react';
import { Database, CheckCircle, AlertCircle, RefreshCw, Eye } from 'lucide-react';
import api from '../api';

export default function DataSourcesPage() {
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDataSources().then(setSources).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Data Sources</h1>
        <p className="text-sm text-surface-500 mt-0.5">Connected data sources and their status</p>
      </div>

      {loading ? (
        <div className="space-y-3">{[1,2].map(i => <div key={i} className="h-24 bg-surface-100 rounded-xl animate-pulse" />)}</div>
      ) : sources.length === 0 ? (
        <div className="text-center py-16 text-surface-400">
          <Database size={40} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No data sources configured</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sources.map(s => (
            <div key={s.id} className="bg-white rounded-xl border border-surface-200 p-5 hover:shadow-md transition-shadow animate-fade-in">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                    <Database size={20} className="text-primary-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-surface-800">{s.name}</h3>
                    <p className="text-xs text-surface-500 mt-0.5">{s.source_type.toUpperCase()}</p>
                  </div>
                </div>
                <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                  s.status === 'active' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                }`}>
                  {s.status === 'active' ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
                  {s.status}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-surface-100">
                <div>
                  <p className="text-xs text-surface-500">Records</p>
                  <p className="text-sm font-semibold text-surface-800">{s.record_count?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-surface-500">Tables</p>
                  <p className="text-sm font-semibold text-surface-800">{s.table_count}</p>
                </div>
                <div>
                  <p className="text-xs text-surface-500">Last Sync</p>
                  <p className="text-sm font-semibold text-surface-800">
                    {s.last_sync ? new Date(s.last_sync).toLocaleDateString() : '—'}
                  </p>
                </div>
                <div className="flex items-end gap-2 justify-end">
                  <button className="px-3 py-1.5 text-xs bg-surface-100 hover:bg-surface-200 text-surface-600 rounded-lg transition-colors flex items-center gap-1">
                    <Eye size={12} /> Schema
                  </button>
                  <button className="px-3 py-1.5 text-xs bg-primary-50 hover:bg-primary-100 text-primary-600 rounded-lg transition-colors flex items-center gap-1">
                    <RefreshCw size={12} /> Sync
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
