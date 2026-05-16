import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { search, advancedSearch } from '../api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('simple');  // simple or advanced
  const [advFilters, setAdvFilters] = useState({
    title: '', judge: '', act: '', citation: '', case_type: '', verdict: '', year_from: '', year_to: ''
  });
  const navigate = useNavigate();

  const doSearch = async () => {
    if (!query && mode === 'simple') return;
    setLoading(true);
    try {
      if (mode === 'simple') {
        const res = await search(query);
        setResults(res.data.results);
      } else {
        const params = Object.fromEntries(Object.entries(advFilters).filter(([_, v]) => v));
        const res = await advancedSearch(params);
        setResults({ cases: res.data.data || [] });
      }
    } catch { setResults(null); }
    setLoading(false);
  };

  return (
    <div>
      <div className="page-header">
        <h2>Search</h2>
        <p>Search across cases, judges, citations, and acts</p>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <button className={`btn ${mode === 'simple' ? 'btn-primary' : 'btn-outline'} btn-sm`}
          onClick={() => setMode('simple')}>Simple Search</button>
        <button className={`btn ${mode === 'advanced' ? 'btn-primary' : 'btn-outline'} btn-sm`}
          onClick={() => setMode('advanced')}>Advanced Search</button>
      </div>

      {mode === 'simple' ? (
        <div className="search-bar">
          <input className="search-input" placeholder="Search cases, judges, citations, acts..."
            value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && doSearch()} />
          <button className="btn btn-primary" onClick={doSearch}>Search</button>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {[['title', 'Case Title'], ['judge', 'Judge Name'], ['act', 'Act Name'], ['citation', 'Citation'],
              ['case_type', 'Case Type'], ['verdict', 'Verdict'], ['year_from', 'Year From'], ['year_to', 'Year To']
            ].map(([key, label]) => (
              <div key={key}>
                <label style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</label>
                <input className="search-input" style={{ width: '100%' }}
                  value={advFilters[key]} onChange={e => setAdvFilters(f => ({ ...f, [key]: e.target.value }))}
                  placeholder={label} />
              </div>
            ))}
          </div>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={doSearch}>Search</button>
        </div>
      )}

      {loading && <div className="loading">Searching...</div>}

      {results && !loading && (
        <div>
          {results.cases && results.cases.length > 0 && (
            <div className="card" style={{ marginBottom: 24, padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border)' }}>
                <span className="card-title">Cases ({results.cases.length})</span>
              </div>
              <table className="data-table">
                <thead>
                  <tr><th>Title</th><th>Type</th><th>Verdict</th><th>Date</th></tr>
                </thead>
                <tbody>
                  {results.cases.map(c => (
                    <tr key={c.case_id}>
                      <td className="case-title" onClick={() => navigate(`/cases/${c.case_id}`)}>
                        {c.case_title || c.case_number || `Case #${c.case_id}`}
                      </td>
                      <td>{c.case_type || '—'}</td>
                      <td>{c.verdict ? <span className={`badge ${c.verdict.toLowerCase()}`}>{c.verdict}</span> : '—'}</td>
                      <td>{c.judgment_date || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {results.judges && results.judges.length > 0 && (
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header"><span className="card-title">Judges ({results.judges.length})</span></div>
              {results.judges.map(j => (
                <span key={j.judge_id} className="tag" style={{ margin: 4, display: 'inline-block', padding: '6px 12px',
                  background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
                  borderRadius: 6, fontSize: 13, color: '#10b981' }}>
                  👨‍⚖️ {j.judge_name}
                </span>
              ))}
            </div>
          )}

          {results.citations && results.citations.length > 0 && (
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header"><span className="card-title">Citations ({results.citations.length})</span></div>
              {results.citations.map(c => (
                <span key={c.citation_id} className="tag" style={{ margin: 4, display: 'inline-block', padding: '6px 12px',
                  background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)',
                  borderRadius: 6, fontSize: 13, color: '#8b5cf6' }}>
                  [{c.citation_type}] {c.citation_text}
                </span>
              ))}
            </div>
          )}

          {results.acts && results.acts.length > 0 && (
            <div className="card">
              <div className="card-header"><span className="card-title">Acts ({results.acts.length})</span></div>
              {results.acts.map(a => (
                <span key={a.act_id} className="tag" style={{ margin: 4, display: 'inline-block', padding: '6px 12px',
                  background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)',
                  borderRadius: 6, fontSize: 13, color: '#f59e0b' }}>
                  📜 {a.act_name}
                </span>
              ))}
            </div>
          )}

          {Object.values(results).every(arr => !arr || arr.length === 0) && (
            <div className="empty-state"><div className="icon">🔍</div><p>No results found</p></div>
          )}
        </div>
      )}
    </div>
  );
}
