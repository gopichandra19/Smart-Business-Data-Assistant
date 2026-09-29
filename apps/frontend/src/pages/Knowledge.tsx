import { useEffect, useState } from 'react';
import { Search, Tag } from 'lucide-react';
import api from '../api';

const CATEGORIES = ['all', 'schema', 'column_definition', 'business_rule', 'kpi', 'relationship', 'glossary', 'policy', 'example'];

const CATEGORY_COLORS: Record<string, string> = {
  schema: 'bg-primary-50 text-primary-700',
  column_definition: 'bg-accent/10 text-accent',
  business_rule: 'bg-success/10 text-success',
  kpi: 'bg-warning/10 text-warning',
  relationship: 'bg-cyan-50 text-cyan-700',
  glossary: 'bg-rose-50 text-rose-700',
  policy: 'bg-orange-50 text-orange-700',
  example: 'bg-surface-100 text-surface-600',
};

export default function KnowledgePage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');

  const fetchDocs = () => {
    setLoading(true);
    api.getKnowledge(category === 'all' ? undefined : category, search || undefined)
      .then(setDocs)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDocs(); }, [category]);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Knowledge Base</h1>
          <p className="text-sm text-surface-500 mt-0.5">Business definitions, schemas, rules, and KPIs</p>
        </div>
        <span className="text-sm text-surface-500 bg-white px-3 py-1.5 rounded-lg border border-surface-200">
          {docs.length} documents
        </span>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchDocs()}
            placeholder="Search knowledge..."
            className="w-full pl-9 pr-4 py-2 bg-white border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/30 transition-all"
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {CATEGORIES.map(c => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                category === c ? 'bg-primary-500 text-white' : 'bg-white border border-surface-200 text-surface-600 hover:border-primary-300'
              }`}
            >
              {c === 'all' ? 'All' : c.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Documents */}
      {loading ? (
        <div className="grid gap-3">{[1,2,3,4].map(i => <div key={i} className="h-28 bg-surface-100 rounded-xl animate-pulse" />)}</div>
      ) : (
        <div className="grid gap-3">
          {docs.map((doc: any) => (
            <div key={doc.id} className="bg-white rounded-xl border border-surface-200 p-4 hover:shadow-md hover:border-primary-200 transition-all animate-fade-in">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <h3 className="text-sm font-semibold text-surface-800">{doc.title}</h3>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium ${CATEGORY_COLORS[doc.category] || 'bg-surface-100 text-surface-600'}`}>
                      {doc.category.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-surface-600 leading-relaxed">{doc.content}</p>
                  <div className="flex items-center gap-3 mt-2">
                    {doc.table_name && (
                      <span className="text-[10px] text-surface-400 flex items-center gap-1">
                        <Tag size={9} /> {doc.table_name}{doc.column_name ? `.${doc.column_name}` : ''}
                      </span>
                    )}
                    {doc.business_domain && (
                      <span className="text-[10px] text-surface-400">{doc.business_domain}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
