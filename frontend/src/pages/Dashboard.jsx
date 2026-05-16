import { useState, useEffect } from 'react';
import { getDashboard, getTimelineAnalytics, getVerdictAnalytics, getCaseTypeAnalytics } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, Legend } from 'recharts';

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#06b6d4'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [verdicts, setVerdicts] = useState([]);
  const [caseTypes, setCaseTypes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getDashboard(),
      getTimelineAnalytics(),
      getVerdictAnalytics(),
      getCaseTypeAnalytics(),
    ]).then(([d, t, v, ct]) => {
      setStats(d.data);
      setTimeline(t.data.data || []);
      setVerdicts(v.data.data || []);
      setCaseTypes(ct.data.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (!stats) return <div className="empty-state"><div className="icon">📊</div><p>Unable to load dashboard data. Make sure the API is running.</p></div>;

  const verdictPie = [
    { name: 'Accepted', value: stats.accepted_cases },
    { name: 'Rejected', value: stats.rejected_cases },
    { name: 'Other', value: stats.other_cases },
  ].filter(d => d.value > 0);

  const typeData = caseTypes.slice(0, 8);

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Legal Case Intelligence — Overview & Analytics</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-label">Total Cases</div>
          <div className="stat-value">{(stats.total_cases || 0).toLocaleString()}</div>
          <div className="stat-detail">Supreme Court of India</div>
        </div>
        <div className="stat-card green">
          <div className="stat-label">Judges</div>
          <div className="stat-value">{(stats.total_judges || 0).toLocaleString()}</div>
          <div className="stat-detail">Unique judges extracted</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-label">Citations</div>
          <div className="stat-value">{(stats.total_citations || 0).toLocaleString()}</div>
          <div className="stat-detail">AIR, SCC, SCR references</div>
        </div>
        <div className="stat-card amber">
          <div className="stat-label">Acts Referenced</div>
          <div className="stat-value">{(stats.total_acts || 0).toLocaleString()}</div>
          <div className="stat-detail">Laws and statutes cited</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Cases Over Time</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
                <XAxis dataKey="year" stroke="#5c6478" fontSize={12} />
                <YAxis stroke="#5c6478" fontSize={12} />
                <Tooltip
                  contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', borderRadius: '8px' }}
                  labelStyle={{ color: '#e8ecf4' }}
                />
                <Area type="monotone" dataKey="total" stroke="#3b82f6" fill="rgba(59,130,246,0.15)" strokeWidth={2} />
                <Area type="monotone" dataKey="accepted" stroke="#10b981" fill="rgba(16,185,129,0.1)" strokeWidth={1.5} />
                <Area type="monotone" dataKey="rejected" stroke="#ef4444" fill="rgba(239,68,68,0.1)" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Verdict Distribution</span>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={verdictPie} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                  dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {verdictPie.map((_, i) => (
                    <Cell key={i} fill={[COLORS[0], COLORS[1], COLORS[2]][i]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Case Type Distribution</span>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={typeData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
              <XAxis type="number" stroke="#5c6478" fontSize={12} />
              <YAxis dataKey="case_type" type="category" width={140} stroke="#5c6478" fontSize={12} />
              <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', borderRadius: '8px' }} />
              <Bar dataKey="total" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
