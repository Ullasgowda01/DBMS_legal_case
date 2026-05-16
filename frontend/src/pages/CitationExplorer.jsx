import { useState, useEffect } from 'react';
import { getCitationAnalytics, getCitations } from '../api';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function CitationExplorer() {
  const [analytics, setAnalytics] = useState(null);
  const [citations, setCitations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCitationAnalytics(),
      getCitations({ limit: 50 }),
    ]).then(([a, c]) => {
      setAnalytics(a.data);
      setCitations(c.data.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading citation data...</div>;

  const typeData = (analytics?.citation_types || []).map(t => ({
    name: t.type || 'Other',
    value: t.total,
    unique: t.unique_cases,
  }));

  return (
    <div>
      <div className="page-header">
        <h2>Citation Network</h2>
        <p>Explore {(analytics?.total_citations || 0).toLocaleString()} legal citations across AIR, SCC, SCR</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-label">Total Citations</div>
          <div className="stat-value">{(analytics?.total_citations || 0).toLocaleString()}</div>
        </div>
        {typeData.map((t, i) => (
          <div key={t.name} className={`stat-card ${['green', 'purple', 'amber'][i] || 'blue'}`}>
            <div className="stat-label">{t.name} Citations</div>
            <div className="stat-value">{t.value.toLocaleString()}</div>
            <div className="stat-detail">{t.unique} unique cases</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Citation Type Distribution</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={typeData} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                  dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Citations by Type</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
                <XAxis dataKey="name" stroke="#5c6478" fontSize={12} />
                <YAxis stroke="#5c6478" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', borderRadius: '8px' }} />
                <Bar dataKey="value" name="Total" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="unique" name="Unique Cases" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <span className="card-title">Recent Citations</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Citation Text</th>
              <th>Type</th>
              <th>Case ID</th>
            </tr>
          </thead>
          <tbody>
            {citations.map(c => (
              <tr key={c.citation_id}>
                <td>{c.citation_id}</td>
                <td style={{ color: 'var(--accent-purple)', fontWeight: 500 }}>{c.citation_text}</td>
                <td><span className="badge" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>{c.citation_type}</span></td>
                <td>{c.case_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
