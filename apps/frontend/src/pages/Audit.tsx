import React, { useEffect, useState } from 'react';
import { Shield, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../api';

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    api.getAuditLogs(100).then(setLogs).catch(() => setLogs([])).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Audit Log</h1>
        <p className="text-sm text-surface-500 mt-0.5">Complete trace of AI interactions and tool executions</p>
      </div>

      {loading ? (
        <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="h-14 bg-surface-100 rounded-lg animate-pulse" />)}</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-16 text-surface-400">
          <Shield size={40} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No audit logs available</p>
          <p className="text-xs mt-1">Audit logs require analyst or admin role to view</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-50 border-b border-surface-200">
                <th className="text-left py-3 px-4 text-xs font-medium text-surface-500">Time</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-surface-500">Action</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-surface-500">Tool</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-surface-500">Status</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-surface-500">Latency</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-surface-500">ID</th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <React.Fragment key={log.id}>
                  <tr
                    onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                    className="border-b border-surface-50 hover:bg-surface-50 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-4 text-xs text-surface-600">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-xs font-medium text-surface-800">
                      {log.action}
                    </td>
                    <td className="py-2.5 px-4 text-xs text-surface-600">
                      {log.tool || '—'}
                    </td>
                    <td className="py-2.5 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        log.status === 'success' ? 'bg-success/10 text-success' :
                        log.status === 'denied' ? 'bg-danger/10 text-danger' :
                        log.status === 'error' ? 'bg-danger/10 text-danger' :
                        'bg-warning/10 text-warning'
                      }`}>{log.status}</span>
                    </td>
                    <td className="py-2.5 px-4 text-xs text-surface-500 text-right font-mono">
                      {log.latency_ms ? `${log.latency_ms.toFixed(0)}ms` : '—'}
                    </td>
                    <td className="py-2.5 px-4 text-[10px] text-surface-400 text-right font-mono">
                      {log.request_id?.substring(0, 8)}
                    </td>
                    <td className="py-2.5 px-2">
                      {expanded === log.id ? <ChevronUp size={14} className="text-surface-400" /> : <ChevronDown size={14} className="text-surface-400" />}
                    </td>
                  </tr>
                  {expanded === log.id && (
                    <tr key={`${log.id}-detail`}>
                      <td colSpan={7} className="px-4 py-3 bg-surface-50 border-b border-surface-100">
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          {log.query && (
                            <div>
                              <p className="text-surface-500 font-medium mb-1">SQL Query</p>
                              <pre className="bg-white p-2 rounded-md border border-surface-200 text-[11px] overflow-x-auto whitespace-pre-wrap">{log.query}</pre>
                            </div>
                          )}
                          {log.intent && (
                            <div>
                              <p className="text-surface-500 font-medium mb-1">Intent</p>
                              <span className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-md text-[10px]">{log.intent}</span>
                            </div>
                          )}
                          {log.metadata_json && Object.keys(log.metadata_json).length > 0 && (
                            <div className="col-span-2">
                              <p className="text-surface-500 font-medium mb-1">Metadata</p>
                              <pre className="bg-white p-2 rounded-md border border-surface-200 text-[11px] overflow-x-auto">
                                {JSON.stringify(log.metadata_json, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
