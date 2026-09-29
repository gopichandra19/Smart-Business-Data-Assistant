import { useEffect, useState } from 'react';
import { Brain, Trash2, Clock, Star } from 'lucide-react';
import api from '../api';

const TYPE_COLORS: Record<string, string> = {
  insight: 'bg-accent/10 text-accent',
  analysis: 'bg-primary-50 text-primary-700',
  conversation: 'bg-surface-100 text-surface-600',
  user_preference: 'bg-warning/10 text-warning',
  entity: 'bg-success/10 text-success',
  business_context: 'bg-cyan-50 text-cyan-700',
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const type = filter === 'all' ? undefined : filter;
    api.getMemories(type).then(setMemories).finally(() => setLoading(false));
  }, [filter]);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this memory?')) return;
    await api.deleteMemory(id);
    setMemories(prev => prev.filter(m => m.id !== id));
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Memory Store</h1>
          <p className="text-sm text-surface-500 mt-0.5">Persistent analytical memories and insights</p>
        </div>
        <span className="text-sm text-surface-500 bg-white px-3 py-1.5 rounded-lg border border-surface-200">
          {memories.length} memories
        </span>
      </div>

      {/* Filter */}
      <div className="flex gap-1.5 flex-wrap">
        {['all', 'insight', 'analysis', 'user_preference', 'entity', 'business_context'].map(t => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filter === t ? 'bg-primary-500 text-white' : 'bg-white border border-surface-200 text-surface-600 hover:border-primary-300'
            }`}
          >
            {t === 'all' ? 'All' : t.replace('_', ' ')}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-24 bg-surface-100 rounded-xl animate-pulse" />)}</div>
      ) : memories.length === 0 ? (
        <div className="text-center py-16 text-surface-400">
          <Brain size={40} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No memories stored yet</p>
          <p className="text-xs mt-1">Memories are created from your chat interactions</p>
        </div>
      ) : (
        <div className="space-y-2">
          {memories.map(m => (
            <div key={m.id} className="bg-white rounded-xl border border-surface-200 p-4 hover:shadow-sm transition-shadow animate-fade-in group">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium ${TYPE_COLORS[m.memory_type] || 'bg-surface-100 text-surface-600'}`}>
                      {m.memory_type.replace('_', ' ')}
                    </span>
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={10} className={i < Math.round(m.importance_score * 5) ? 'text-warning fill-warning' : 'text-surface-200'} />
                      ))}
                    </div>
                  </div>
                  <p className="text-sm text-surface-800 leading-relaxed">{m.summary || m.content}</p>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-surface-400">
                    <span className="flex items-center gap-1"><Clock size={9} /> {new Date(m.created_at).toLocaleDateString()}</span>
                    <span>Confidence: {(m.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(m.id)}
                  className="text-surface-300 hover:text-danger transition-colors opacity-0 group-hover:opacity-100 p-1"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
