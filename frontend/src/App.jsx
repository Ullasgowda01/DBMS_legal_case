import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CaseExplorer from './pages/CaseExplorer';
import CaseDetail from './pages/CaseDetail';
import JudgeAnalytics from './pages/JudgeAnalytics';
import CitationExplorer from './pages/CitationExplorer';
import SearchPage from './pages/SearchPage';
import './index.css';

function App() {
  return (
    <Router>
      <div className="app">
        <aside className="sidebar">
          <div className="sidebar-logo">
            <div className="logo-icon">⚖️</div>
            <h1>Legal Intelligence<span>Analytics Platform</span></h1>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Overview</div>
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
              <span className="icon">📊</span> Dashboard
            </NavLink>
            <NavLink to="/search" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="icon">🔍</span> Search
            </NavLink>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Explore</div>
            <NavLink to="/cases" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="icon">📁</span> Case Explorer
            </NavLink>
            <NavLink to="/judges" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="icon">👨‍⚖️</span> Judge Analytics
            </NavLink>
            <NavLink to="/citations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="icon">🔗</span> Citation Network
            </NavLink>
          </div>
        </aside>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cases" element={<CaseExplorer />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/judges" element={<JudgeAnalytics />} />
            <Route path="/citations" element={<CitationExplorer />} />
            <Route path="/search" element={<SearchPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
