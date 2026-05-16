import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCases } from '../api';

export default function CaseExplorer() {
  const [cases, setCases] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState({ case_type: '', case_category: '', verdict: '' });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const limit = 30;

  useEffect(() => {
    setLoading(true);
    const params = { skip: page * limit, limit, ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v)) };
    getCases(params).then(res => {
      setCases(res.data.data || []);
      setTotal(res.data.total || 0);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [page, filters]);

  return (
    <div>
      <div className="page-header">
        <h2>Case Explorer</h2>
        <p>Browse and filter {total.toLocaleString()} legal cases</p>
      </div>

      <div className="filters">
        <select className="filter-select" value={filters.case_type}
          onChange={e => { setFilters(f => ({ ...f, case_type: e.target.value })); setPage(0); }}>
          <option value="">All Types</option>
          <option value="appeal">Appeal</option>
          <option value="writ petition">Writ Petition</option>
          <option value="special leave petition">Special Leave Petition</option>
          <option value="contempt petition">Contempt Petition</option>
          <option value="election petition">Election Petition</option>
          <option value="review petition">Review Petition</option>
          <option value="transfer petition">Transfer Petition</option>
        </select>

        <select className="filter-select" value={filters.case_category}
          onChange={e => { setFilters(f => ({ ...f, case_category: e.target.value })); setPage(0); }}>
          <option value="">All Categories</option>
          <option value="civil">Civil</option>
          <option value="criminal">Criminal</option>
        </select>

        <select className="filter-select" value={filters.verdict}
          onChange={e => { setFilters(f => ({ ...f, verdict: e.target.value })); setPage(0); }}>
          <option value="">All Verdicts</option>
          <option value="Accepted">Accepted</option>
          <option value="Rejected">Rejected</option>
          <option value="Other">Other</option>
        </select>
      </div>

      {loading ? (
        <div className="loading">Loading cases...</div>
      ) : (
        <>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Case Title</th>
                  <th>Type</th>
                  <th>Category</th>
                  <th>Verdict</th>
                  <th>Date</th>
                  <th>Words</th>
                </tr>
              </thead>
              <tbody>
                {cases.map(c => (
                  <tr key={c.case_id}>
                    <td>{c.case_id}</td>
                    <td className="case-title" onClick={() => navigate(`/cases/${c.case_id}`)}>
                      {c.case_title || c.case_number || `Case #${c.case_id}`}
                    </td>
                    <td>{c.case_type || '—'}</td>
                    <td>{c.case_category ? <span className={`badge ${c.case_category}`}>{c.case_category}</span> : '—'}</td>
                    <td>{c.verdict ? <span className={`badge ${c.verdict.toLowerCase()}`}>{c.verdict}</span> : '—'}</td>
                    <td>{c.judgment_date || '—'}</td>
                    <td>{c.word_count?.toLocaleString() || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span className="pagination-info">
              Showing {page * limit + 1}–{Math.min((page + 1) * limit, total)} of {total.toLocaleString()}
            </span>
            <div className="pagination-buttons">
              <button className="btn btn-outline btn-sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
                ← Previous
              </button>
              <button className="btn btn-outline btn-sm" disabled={(page + 1) * limit >= total} onClick={() => setPage(p => p + 1)}>
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
