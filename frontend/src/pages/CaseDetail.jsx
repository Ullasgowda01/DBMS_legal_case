import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCase } from '../api';

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCase(id).then(res => {
      setCaseData(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading">Loading case details...</div>;
  if (!caseData) return <div className="empty-state"><p>Case not found</p></div>;

  const c = caseData;

  return (
    <div>
      <div className="detail-header">
        <span className="back-btn" onClick={() => navigate(-1)}>←</span>
        <div>
          <h2>{c.case_title || c.case_number || `Case #${c.case_id}`}</h2>
          <div className="detail-meta">
            {c.case_number && <span>📋 {c.case_number}</span>}
            {c.court_name && <span>🏛️ {c.court_name}</span>}
            {c.judgment_date && <span>📅 {c.judgment_date}</span>}
            {c.case_type && <span>📁 {c.case_type}</span>}
            {c.verdict && <span className={`badge ${c.verdict.toLowerCase()}`}>{c.verdict}</span>}
          </div>
        </div>
      </div>

      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card blue">
          <div className="stat-label">Bench Strength</div>
          <div className="stat-value">{c.bench_strength || 0}</div>
          <div className="stat-detail">{c.bench_type || 'Unknown'} bench</div>
        </div>
        <div className="stat-card green">
          <div className="stat-label">Word Count</div>
          <div className="stat-value">{(c.word_count || 0).toLocaleString()}</div>
          <div className="stat-detail">Judgment length</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-label">Citations</div>
          <div className="stat-value">{(c.citations || []).length}</div>
          <div className="stat-detail">Legal references</div>
        </div>
      </div>

      <div className="detail-sections">
        <div className="detail-section">
          <h4>Judges ({(c.judges || []).length})</h4>
          {(c.judges || []).length > 0 ? (
            c.judges.map((j, i) => (
              <span key={i} className="tag">👨‍⚖️ {j.judge_name}</span>
            ))
          ) : <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No judges extracted</p>}
        </div>

        <div className="detail-section">
          <h4>Parties ({(c.parties || []).length})</h4>
          {(c.parties || []).length > 0 ? (
            c.parties.map((p, i) => (
              <span key={i} className="tag" style={{
                background: p.role === 'petitioner' ? 'rgba(59,130,246,0.1)' : 'rgba(239,68,68,0.1)',
                borderColor: p.role === 'petitioner' ? 'rgba(59,130,246,0.2)' : 'rgba(239,68,68,0.2)',
                color: p.role === 'petitioner' ? '#3b82f6' : '#ef4444',
              }}>
                {p.role}: {p.party_name}
              </span>
            ))
          ) : <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No parties extracted</p>}
        </div>

        <div className="detail-section">
          <h4>Citations ({(c.citations || []).length})</h4>
          {(c.citations || []).length > 0 ? (
            c.citations.map((ct, i) => (
              <span key={i} className="tag" style={{
                background: 'rgba(139,92,246,0.1)',
                borderColor: 'rgba(139,92,246,0.2)',
                color: '#8b5cf6',
              }}>
                [{ct.citation_type}] {ct.citation_text}
              </span>
            ))
          ) : <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No citations found</p>}
        </div>

        <div className="detail-section">
          <h4>Summary</h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7 }}>
            {c.summary || 'No summary available for this case.'}
          </p>
        </div>
      </div>
    </div>
  );
}
