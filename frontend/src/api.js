import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Cases
export const getCases = (params = {}) => api.get('/cases', { params });
export const getCase = (id) => api.get(`/cases/${id}`);
export const createCase = (data) => api.post('/cases', null, { params: data });

// Judges
export const getJudges = (params = {}) => api.get('/judges', { params });
export const getJudge = (id) => api.get(`/judges/${id}`);
export const getJudgeAnalytics = (id) => api.get(`/judges/${id}/analytics`);

// Citations
export const getCitations = (params = {}) => api.get('/citations', { params });
export const getCitationGraph = (params = {}) => api.get('/citations/graph', { params });
export const getCaseCitations = (id) => api.get(`/citations/cases/${id}`);

// Analytics
export const getDashboard = () => api.get('/analytics/dashboard');
export const getJudgeAnalyticsAll = (params = {}) => api.get('/analytics/judges', { params });
export const getActAnalytics = (params = {}) => api.get('/analytics/acts', { params });
export const getCitationAnalytics = () => api.get('/analytics/citations');
export const getVerdictAnalytics = () => api.get('/analytics/verdicts');
export const getTimelineAnalytics = () => api.get('/analytics/timeline');
export const getCaseTypeAnalytics = () => api.get('/analytics/case-types');

// Search
export const search = (q, searchType = 'all') => api.get('/search', { params: { q, search_type: searchType } });
export const advancedSearch = (params) => api.get('/search/cases/advanced', { params });

export default api;
