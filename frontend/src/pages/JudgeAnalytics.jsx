import { useState, useEffect } from 'react';
import { getJudgeAnalyticsAll } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function JudgeAnalytics() {
  const [judges, setJudges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getJudgeAnalyticsAll({ limit: 30 }).then(res => {
      setJudges(res.data.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading judge analytics...</div>;

  const top15 = judges.slice(0, 15);

  return (
    <div>
      <div className="page-header">
        <h2>Judge Analytics</h2>
        <p>Activity, verdicts, and influence analysis for {judges.length} judges</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-label">Total Judges</div>
          <div className="stat-value">{judges.length}</div>
        </div>
        <div className="stat-card green">
          <div className="stat-label">Most Active</div>
          <div className="stat-value" style={{ fontSize: 18 }}>{judges[0]?.judge_name || '—'}</div>
          <div className="stat-detail">{judges[0]?.total_cases || 0} cases</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-label">Avg Judgment Length</div>
          <div className="stat-value">
            {judges.length > 0 ? Math.round(judges.reduce((s, j) => s + j.avg_judgment_length, 0) / judges.length).toLocaleString() : 0}
          </div>
          <div className="stat-detail">words per judgment</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">Top 15 Judges by Case Count</span>
        </div>
        <div style={{ height: 500 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={top15} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
              <XAxis type="number" stroke="#5c6478" fontSize={12} />
              <YAxis dataKey="judge_name" type="category" width={160} stroke="#5c6478" fontSize={11} />
              <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', borderRadius: '8px' }} />
              <Legend />
              <Bar dataKey="accepted" name="Accepted" stackId="a" fill="#10b981" />
              <Bar dataKey="rejected" name="Rejected" stackId="a" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Judge Name</th>
              <th>Total Cases</th>
              <th>Accepted</th>
              <th>Rejected</th>
              <th>Avg Length</th>
            </tr>
          </thead>
          <tbody>
            {judges.map((j, i) => (
              <tr key={j.judge_id}>
                <td>{i + 1}</td>
                <td style={{ color: 'var(--accent-cyan)', fontWeight: 500 }}>{j.judge_name}</td>
                <td>{j.total_cases}</td>
                <td><span className="badge accepted">{j.accepted}</span></td>
                <td><span className="badge rejected">{j.rejected}</span></td>
                <td>{j.avg_judgment_length?.toLocaleString() || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
