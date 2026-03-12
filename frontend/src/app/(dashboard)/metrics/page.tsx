'use client';

import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Target, BarChart2, ShieldCheck, Play, Download } from 'lucide-react';
import { getMetrics, exportReport } from '@/lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend, Area, AreaChart } from 'recharts';

export default function MetricsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => getMetrics(50, 0),
  });

  const summary = data?.summary;
  const evaluations = data?.evaluations || [];
  const queries = data?.queries || [];

  // Chart data
  const confidenceData = queries.slice(0, 20).reverse().map((q, i) => ({
    name: `Q${i + 1}`,
    confidence: (q.confidence_score || 0) * 100,
  }));

  const comparisonData = evaluations.length > 0 ? [
    { metric: 'ROUGE-L', RAG: +(summary?.avg_rouge_l || 0).toFixed(3), Baseline: +(evaluations[0]?.baseline_rouge || 0).toFixed(3) },
    { metric: 'BLEU-4', RAG: +(summary?.avg_bleu_4 || 0).toFixed(3), Baseline: +(evaluations[0]?.baseline_bleu || 0).toFixed(3) },
    { metric: 'Faith.', RAG: +(summary?.avg_faithfulness || 0).toFixed(3), Baseline: +(evaluations[0]?.baseline_faithfulness || 0).toFixed(3) },
  ] : [];

  const handleExport = async () => {
    try {
      const blob = await exportReport();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'groundedai_eval_report.pdf'; a.click();
      URL.revokeObjectURL(url);
    } catch { /* silently fail */ }
  };

  const statCards = [
    { label: 'Total Queries', icon: MessageSquare, value: summary?.total_queries || 0, color: '#6C63FF' },
    { label: 'Avg Confidence', icon: Target, value: `${((summary?.avg_confidence || 0) * 100).toFixed(1)}%`, color: '#6C63FF' },
    { label: 'Avg ROUGE-L', icon: BarChart2, value: (summary?.avg_rouge_l || 0).toFixed(4), color: '#3B82F6' },
    { label: 'Hallucination Δ', icon: ShieldCheck, value: `${((summary?.avg_hallucination_delta || 0) * 100).toFixed(1)}%`, color: '#10B981' },
  ];

  return (
    <div style={{ padding: '32px 40px', overflow: 'auto', flex: 1 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#E6EDF3', margin: 0 }}>Evaluation Metrics</h1>
          <p style={{ fontSize: 14, color: '#8B949E', marginTop: 4 }}>RAG performance vs baseline LLM</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={handleExport} style={{
            padding: '10px 18px', background: 'transparent',
            border: '1px solid #30363D', borderRadius: 10,
            color: '#E6EDF3', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <Download size={16} /> Export PDF
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} style={{
              backdropFilter: 'blur(16px)', background: 'rgba(22,27,34,0.75)',
              border: '1px solid rgba(48,54,61,0.6)', borderRadius: 18, padding: 20,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <Icon size={18} style={{ color: card.color }} />
                <span style={{ fontSize: 12, color: '#8B949E', fontWeight: 600 }}>{card.label}</span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#E6EDF3' }}>{card.value}</div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        {/* Confidence Over Time */}
        <div style={{
          backdropFilter: 'blur(16px)', background: 'rgba(22,27,34,0.75)',
          border: '1px solid rgba(48,54,61,0.6)', borderRadius: 18, padding: 20,
        }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#E6EDF3', marginBottom: 16 }}>Confidence Score Over Time</h3>
          {confidenceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={confidenceData}>
                <defs>
                  <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6C63FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6C63FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" />
                <XAxis dataKey="name" stroke="#484F58" fontSize={11} />
                <YAxis stroke="#484F58" fontSize={11} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: '#161B22', border: '1px solid #21262D', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="confidence" stroke="#6C63FF" fill="url(#confGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#484F58', fontSize: 13 }}>
              No query data yet
            </div>
          )}
        </div>

        {/* RAG vs Baseline */}
        <div style={{
          backdropFilter: 'blur(16px)', background: 'rgba(22,27,34,0.75)',
          border: '1px solid rgba(48,54,61,0.6)', borderRadius: 18, padding: 20,
        }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#E6EDF3', marginBottom: 16 }}>RAG vs Baseline</h3>
          {comparisonData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" />
                <XAxis dataKey="metric" stroke="#484F58" fontSize={11} />
                <YAxis stroke="#484F58" fontSize={11} domain={[0, 1]} />
                <Tooltip contentStyle={{ background: '#161B22', border: '1px solid #21262D', borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="RAG" fill="#6C63FF" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Baseline" fill="#484F58" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#484F58', fontSize: 13 }}>
              Run evaluations to see comparison
            </div>
          )}
        </div>
      </div>

      {/* Evaluations Table */}
      <div style={{ background: '#161B22', borderRadius: 18, overflow: 'hidden', border: '1px solid #21262D' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #21262D' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#E6EDF3', margin: 0 }}>Recent Evaluations</h3>
        </div>
        {evaluations.length === 0 ? (
          <div style={{ padding: '40px 24px', textAlign: 'center', color: '#484F58', fontSize: 13 }}>
            No evaluations yet. Run an evaluation to see results.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 800 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #21262D' }}>
                  {['Query ID', 'ROUGE-L', 'BLEU-4', 'Faithfulness', 'P@5', 'R@5', 'MRR', 'Hall. Δ', 'Date'].map((h) => (
                    <th key={h} style={{ padding: '10px 14px', fontSize: 10, fontWeight: 600, color: '#8B949E', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'left' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {evaluations.slice(0, 20).map((ev) => (
                  <tr key={ev.id} style={{ borderBottom: '1px solid #21262D' }}>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#8B949E', fontFamily: "'JetBrains Mono', monospace" }}>
                      {ev.query_id?.slice(0, 8)}...
                    </td>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#E6EDF3' }}>{(ev.rouge_l || 0).toFixed(3)}</td>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#E6EDF3' }}>{(ev.bleu_4 || 0).toFixed(3)}</td>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#E6EDF3' }}>{(ev.faithfulness || 0).toFixed(3)}</td>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#E6EDF3' }}>{(ev.precision_k || 0).toFixed(3)}</td>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#E6EDF3' }}>{(ev.recall_k || 0).toFixed(3)}</td>
                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#E6EDF3' }}>{(ev.mrr || 0).toFixed(3)}</td>
                    <td style={{
                      padding: '10px 14px', fontSize: 12, fontWeight: 600,
                      color: (ev.hallucination_delta || 0) > 0 ? '#10B981' : '#EF4444',
                    }}>
                      {(ev.hallucination_delta || 0) > 0 ? '+' : ''}{((ev.hallucination_delta || 0) * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '10px 14px', fontSize: 11, color: '#8B949E' }}>
                      {new Date(ev.evaluated_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
