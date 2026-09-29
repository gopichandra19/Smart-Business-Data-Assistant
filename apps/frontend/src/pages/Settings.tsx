import { useEffect, useState } from 'react';
import api from '../api';

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const user = api.getUser();

  useEffect(() => {
    if (user?.role === 'admin') {
      api.getSettings().then(setSettings).catch(() => setSettings(null)).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  if (user?.role !== 'admin') {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-surface-900 mb-2">Settings</h1>
        <div className="bg-warning/5 border border-warning/20 rounded-xl p-4 text-sm text-warning">
          Settings are available to admin users only.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Settings</h1>
        <p className="text-sm text-surface-500 mt-0.5">System configuration</p>
      </div>

      {loading ? (
        <div className="h-64 bg-surface-100 rounded-xl animate-pulse" />
      ) : settings ? (
        <div className="space-y-4">
          <SettingSection title="LLM Configuration">
            <SettingRow label="Provider" value={settings.llm_provider} />
            <SettingRow label="Model" value={settings.llm_model} />
          </SettingSection>

          <SettingSection title="RAG Configuration">
            <SettingRow label="Vector Store" value={settings.vector_store} />
            <SettingRow label="Top K Results" value={settings.rag_top_k} />
          </SettingSection>

          <SettingSection title="Memory">
            <SettingRow label="Enabled" value={settings.memory_enabled ? 'Yes' : 'No'} />
            <SettingRow label="Max Results" value={settings.memory_max_results} />
          </SettingSection>

          <SettingSection title="Query Safety">
            <SettingRow label="Max Rows" value={settings.max_query_rows} />
            <SettingRow label="Timeout" value={`${settings.sql_timeout_seconds}s`} />
          </SettingSection>

          <SettingSection title="System">
            <SettingRow label="Log Level" value={settings.log_level} />
          </SettingSection>
        </div>
      ) : (
        <p className="text-sm text-surface-500">Unable to load settings</p>
      )}
    </div>
  );
}

function SettingSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-surface-200 overflow-hidden">
      <div className="px-5 py-3 bg-surface-50 border-b border-surface-200">
        <h3 className="text-sm font-semibold text-surface-700">{title}</h3>
      </div>
      <div className="divide-y divide-surface-100">
        {children}
      </div>
    </div>
  );
}

function SettingRow({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <span className="text-sm text-surface-600">{label}</span>
      <span className="text-sm font-medium text-surface-800 bg-surface-50 px-3 py-1 rounded-md">{String(value)}</span>
    </div>
  );
}
