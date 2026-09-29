import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Send, Loader2, Database, BookOpen, Brain, Wrench,
  ChevronRight, BarChart3, Table2, Code, Clock,
  MessageSquare, Plus, PanelRightOpen, PanelRightClose
} from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api';

interface ChatMsg {
  id?: number;
  role: string;
  content: string;
  metadata_json?: any;
  // Rich response data
  intent?: string;
  evidence?: { type: string; source: string; detail?: string }[];
  knowledge?: { title: string; category: string; similarity: number }[];
  memory?: { summary: string; type: string; score: number }[];
  tool_calls?: { tool: string; input_summary: string; output_summary: string; execution_time_ms: number; status: string }[];
  visualizations?: { type: string; title: string; x?: string; y?: string; data?: any[]; columns?: string[] }[];
  suggested_questions?: string[];
  request_id?: string;
}

export default function ChatPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(id ? parseInt(id) : null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(true);
  const [selectedMsg, setSelectedMsg] = useState<ChatMsg | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    api.getConversations().then(setConversations).catch(() => {});
  }, [conversationId]);

  useEffect(() => {
    if (id) {
      api.getConversation(parseInt(id)).then(data => {
        setConversationId(data.id);
        setMessages(data.messages.map((m: any) => ({
          ...m,
          role: m.role,
          content: m.content,
        })));
      }).catch(() => {});
    }
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const msg = input.trim();
    if (!msg || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const response = await api.sendMessage(msg, conversationId || undefined);
      setConversationId(response.conversation_id);

      const assistantMsg: ChatMsg = {
        id: response.message_id,
        role: 'assistant',
        content: response.answer,
        intent: response.intent,
        evidence: response.evidence,
        knowledge: response.knowledge,
        memory: response.memory,
        tool_calls: response.tool_calls,
        visualizations: response.visualizations,
        suggested_questions: response.suggested_questions,
        request_id: response.request_id,
      };

      setMessages(prev => [...prev, assistantMsg]);
      setSelectedMsg(assistantMsg);

      if (!id) navigate(`/chat/${response.conversation_id}`, { replace: true });
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setSelectedMsg(null);
    navigate('/chat');
  };

  return (
    <div className="flex h-full">
      {/* Conversation Sidebar */}
      <div className="w-56 border-r border-surface-200 bg-white flex flex-col shrink-0">
        <div className="p-3 border-b border-surface-100">
          <button
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Plus size={14} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {conversations.map((c: any) => (
            <button
              key={c.id}
              onClick={() => navigate(`/chat/${c.id}`)}
              className={`w-full text-left px-3 py-2.5 text-xs hover:bg-surface-50 transition-colors ${
                conversationId === c.id ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-500' : 'text-surface-600'
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageSquare size={12} className="shrink-0" />
                <span className="truncate">{c.title}</span>
              </div>
              <span className="text-[10px] text-surface-400 ml-5">{c.message_count} msgs</span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="text-xs text-surface-400 text-center p-4">No conversations yet</p>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-100 to-accent/10 flex items-center justify-center mb-4">
                <BarChart3 size={28} className="text-primary-500" />
              </div>
              <h2 className="text-xl font-semibold text-surface-800">Business Data Assistant</h2>
              <p className="text-sm text-surface-500 mt-2 max-w-md">
                Ask questions about your business data. I'll analyze it with evidence-backed insights.
              </p>
              <div className="grid grid-cols-2 gap-2 mt-6 max-w-lg">
                {[
                  'Which region generated the highest revenue last quarter?',
                  'Show me the revenue trend for the last 12 months',
                  'What does active customer mean?',
                  'Which customer segment contributes the most?',
                ].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(q); inputRef.current?.focus(); }}
                    className="text-left text-xs text-surface-600 bg-white border border-surface-200 rounded-lg px-3 py-2.5 hover:border-primary-300 hover:bg-primary-50/50 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 animate-fade-in ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role !== 'user' && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5">
                  AI
                </div>
              )}
              <div className={`max-w-2xl ${msg.role === 'user' ? 'order-first' : ''}`}>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-primary-500 text-white rounded-br-md'
                    : 'bg-white border border-surface-200 text-surface-800 rounded-bl-md shadow-sm'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>

                {/* Visualization */}
                {msg.visualizations?.map((viz, vi) => (
                  <div key={vi} className="mt-3 bg-white border border-surface-200 rounded-xl p-4 shadow-sm">
                    <h4 className="text-xs font-semibold text-surface-700 mb-3">{viz.title}</h4>
                    {viz.data && viz.data.length > 0 && (
                      <ResponsiveContainer width="100%" height={200}>
                        {viz.type === 'line' ? (
                          <LineChart data={viz.data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey={viz.x} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                            <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                            <Tooltip contentStyle={{ borderRadius: 8, fontSize: 11 }} />
                            <Line type="monotone" dataKey={viz.y} stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} />
                          </LineChart>
                        ) : (
                          <BarChart data={viz.data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey={viz.x} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                            <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                            <Tooltip contentStyle={{ borderRadius: 8, fontSize: 11 }} />
                            <Bar dataKey={viz.y} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        )}
                      </ResponsiveContainer>
                    )}
                    {/* Data table */}
                    {viz.data && viz.columns && (
                      <details className="mt-3">
                        <summary className="text-[11px] text-surface-500 cursor-pointer hover:text-primary-500 flex items-center gap-1">
                          <Table2 size={12} /> View data table ({viz.data.length} rows)
                        </summary>
                        <div className="mt-2 overflow-x-auto max-h-48">
                          <table className="w-full text-xs">
                            <thead><tr className="border-b border-surface-200">
                              {viz.columns.map(c => <th key={c} className="text-left py-1.5 px-2 text-surface-500 font-medium">{c}</th>)}
                            </tr></thead>
                            <tbody>
                              {viz.data.slice(0, 20).map((row: any, ri: number) => (
                                <tr key={ri} className="border-b border-surface-50">
                                  {viz.columns!.map(c => <td key={c} className="py-1.5 px-2 text-surface-700">{typeof row[c] === 'number' ? row[c].toLocaleString() : row[c]}</td>)}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    )}
                  </div>
                ))}

                {/* Evidence badges */}
                {msg.role === 'assistant' && (msg.evidence?.length || msg.tool_calls?.length || msg.knowledge?.length || msg.memory?.length) ? (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {msg.evidence?.map((e, ei) => (
                      <span key={ei} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-primary-50 text-primary-700 text-[10px] font-medium">
                        <Database size={10} /> {e.source}
                      </span>
                    ))}
                    {msg.knowledge?.filter(k => k.similarity > 0.3).map((k, ki) => (
                      <span key={ki} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-success/10 text-success text-[10px] font-medium">
                        <BookOpen size={10} /> {k.title}
                      </span>
                    ))}
                    {msg.memory?.filter(m => m.score > 0.3).map((m, mi) => (
                      <span key={mi} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-accent/10 text-accent text-[10px] font-medium">
                        <Brain size={10} /> {m.summary?.substring(0, 40)}...
                      </span>
                    ))}
                    {msg.intent && (
                      <button
                        onClick={() => setSelectedMsg(msg)}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-100 text-surface-600 text-[10px] font-medium hover:bg-surface-200 transition-colors"
                      >
                        <Wrench size={10} /> View details
                      </button>
                    )}
                  </div>
                ) : null}

                {/* Suggested follow-ups */}
                {msg.suggested_questions && msg.suggested_questions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {msg.suggested_questions.map((q, qi) => (
                      <button
                        key={qi}
                        onClick={() => { setInput(q); inputRef.current?.focus(); }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-surface-200 text-[11px] text-surface-600 hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50/50 transition-all"
                      >
                        <ChevronRight size={10} /> {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-surface-200 flex items-center justify-center text-surface-600 text-xs font-bold shrink-0 mt-0.5">
                  {api.getUser()?.name?.charAt(0) || 'U'}
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent flex items-center justify-center text-white text-xs font-bold shrink-0">
                AI
              </div>
              <div className="bg-white border border-surface-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-primary-400 rounded-full typing-dot" />
                  <div className="w-2 h-2 bg-primary-400 rounded-full typing-dot" />
                  <div className="w-2 h-2 bg-primary-400 rounded-full typing-dot" />
                  <span className="text-xs text-surface-400 ml-2">Analyzing your question...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-surface-200 bg-white p-4">
          <div className="max-w-3xl mx-auto flex gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a business question..."
                rows={1}
                className="w-full resize-none px-4 py-2.5 bg-surface-50 border border-surface-200 rounded-xl text-sm text-surface-800 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500/50 transition-all"
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Evidence/Context Panel */}
      {showPanel && selectedMsg && (
        <div className="w-72 border-l border-surface-200 bg-white overflow-y-auto shrink-0 animate-slide-in">
          <div className="p-4 border-b border-surface-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-surface-800">Context & Evidence</h3>
            <button onClick={() => setShowPanel(false)} className="text-surface-400 hover:text-surface-600">
              <PanelRightClose size={16} />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Intent */}
            {selectedMsg.intent && (
              <div>
                <h4 className="text-[11px] font-medium text-surface-500 uppercase tracking-wider mb-1.5">Intent</h4>
                <span className="px-2 py-1 bg-primary-50 text-primary-700 rounded-md text-xs font-medium">
                  {selectedMsg.intent}
                </span>
              </div>
            )}

            {/* Evidence */}
            {selectedMsg.evidence && selectedMsg.evidence.length > 0 && (
              <div>
                <h4 className="text-[11px] font-medium text-surface-500 uppercase tracking-wider mb-1.5">Data Sources</h4>
                {selectedMsg.evidence.map((e, i) => (
                  <div key={i} className="flex items-start gap-2 py-1.5">
                    <Database size={12} className="text-primary-500 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-surface-700">{e.source}</p>
                      {e.detail && <p className="text-[10px] text-surface-500">{e.detail}</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Knowledge */}
            {selectedMsg.knowledge && selectedMsg.knowledge.length > 0 && (
              <div>
                <h4 className="text-[11px] font-medium text-surface-500 uppercase tracking-wider mb-1.5">Knowledge Used</h4>
                {selectedMsg.knowledge.map((k, i) => (
                  <div key={i} className="py-1.5 border-b border-surface-50 last:border-0">
                    <p className="text-xs font-medium text-surface-700">{k.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-surface-400">{k.category}</span>
                      <span className="text-[10px] text-success">{(k.similarity * 100).toFixed(0)}% match</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Memory */}
            {selectedMsg.memory && selectedMsg.memory.length > 0 && (
              <div>
                <h4 className="text-[11px] font-medium text-surface-500 uppercase tracking-wider mb-1.5">Memory Retrieved</h4>
                {selectedMsg.memory.map((m, i) => (
                  <div key={i} className="py-1.5 border-b border-surface-50 last:border-0">
                    <p className="text-xs text-surface-700">{m.summary}</p>
                    <span className="text-[10px] text-accent">{m.type} • score: {m.score.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Tool Calls */}
            {selectedMsg.tool_calls && selectedMsg.tool_calls.length > 0 && (
              <div>
                <h4 className="text-[11px] font-medium text-surface-500 uppercase tracking-wider mb-1.5">Tool Calls</h4>
                {selectedMsg.tool_calls.map((tc, i) => (
                  <div key={i} className="py-2 border-b border-surface-50 last:border-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-surface-700 flex items-center gap-1">
                        <Wrench size={10} /> {tc.tool}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${tc.status === 'success' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                        {tc.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 mt-1 text-[10px] text-surface-400">
                      <Clock size={9} /> {tc.execution_time_ms.toFixed(0)}ms
                    </div>
                    <details className="mt-1">
                      <summary className="text-[10px] text-surface-400 cursor-pointer hover:text-primary-500">
                        <Code size={9} className="inline" /> SQL / Input
                      </summary>
                      <pre className="mt-1 text-[10px] bg-surface-50 p-2 rounded-md overflow-x-auto text-surface-600 whitespace-pre-wrap">
                        {tc.input_summary}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            )}

            {/* Request ID */}
            {selectedMsg.request_id && (
              <div className="pt-2 border-t border-surface-100">
                <span className="text-[10px] text-surface-400">Request: {selectedMsg.request_id}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toggle panel button if hidden */}
      {!showPanel && (
        <button
          onClick={() => setShowPanel(true)}
          className="absolute right-2 top-2 p-2 bg-white border border-surface-200 rounded-lg text-surface-500 hover:text-primary-500 shadow-sm"
        >
          <PanelRightOpen size={16} />
        </button>
      )}
    </div>
  );
}
