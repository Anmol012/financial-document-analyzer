import axios from 'axios';
import { config } from './config';
import { toast } from '@/components/ui/use-toast';

const api = axios.create({
  baseURL: config.baseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

api.interceptors.request.use(
  (conf) => {
    const token = localStorage.getItem('token');
    if (token) conf.headers.Authorization = `Bearer ${token}`;
    return conf;
  },
  (error) => {
    toast({ variant: 'destructive', title: 'Request setup failed' });
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const message = error.response?.data?.error || 'Network error';

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${config.baseUrl}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          });
          const newToken = res.data.token;
          localStorage.setItem('token', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch {
          // refresh failed — fall through to logout
        }
      }
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      toast({ variant: 'destructive', title: 'Session expired, please log in' });
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      toast({ variant: 'destructive', title: 'Too many requests, please slow down' });
    } else if (error.response?.status !== 401) {
      toast({ variant: 'destructive', title: message });
    }
    return Promise.reject(error);
  }
);

// ─── Mock data ────────────────────────────────────────────────────────────────

const mockData = {
  documents: {
    documents: [
      { id: 'doc1', name: 'TSLA-Q2-2025-Update.pdf', uploadDate: '2025-10-05T00:00:00Z', status: 'complete', analysisId: 'analysis1' },
      { id: 'doc2', name: 'SampleReport.pdf', uploadDate: '2025-10-04T00:00:00Z', status: 'pending', analysisId: null },
    ],
    total: 2,
    page: 1,
  },
  login: { message: 'Login successful', token: 'fake-jwt-token', refresh_token: 'fake-refresh-token', user: { id: 'user123', username: 'testuser', role: 'Viewer' } },
  register: { message: 'User registered successfully', user: { id: 'user456', username: 'newuser', email: 'new@example.com', role: 'Viewer' } },
  analyze: (id) => ({ message: 'Analysis started', taskId: `task_${id}` }),
  result: {
    analysis: {
      id: 'analysis1',
      documentId: 'doc1',
      results: {
        financialSummary: 'Tesla Q2 2025: Revenue up 15% YoY to $25.5B. Gross margin improved to 18.2%.',
        riskAssessment: { score: 0.45, details: 'Moderate risk due to EV market competition and supply chain pressures.' },
        marketInsights: 'EV market growing at 20% CAGR. Tesla maintains 18% global market share. Increasing competition from BYD and legacy OEMs.',
        recommendations: 'Consider expanding energy storage segment. Monitor gross margin trends. Diversify supply chain.',
        chartsData: {
          revenueTrend: [
            { year: '2022', value: 81.5 },
            { year: '2023', value: 96.8 },
            { year: '2024', value: 110.2 },
            { year: '2025', value: 125.5 },
          ],
          profitMargin: [
            { quarter: 'Q1', value: 17.4 },
            { quarter: 'Q2', value: 18.2 },
            { quarter: 'Q3', value: 18.8 },
            { quarter: 'Q4', value: 19.1 },
          ],
        },
      },
      confidence: 0.92,
      completedAt: '2025-10-05T01:00:00Z',
      status: 'complete',
    },
  },
  upload: (file) => ({
    message: 'Document uploaded',
    document: { id: `doc_${Date.now()}`, name: file.name, uploadDate: new Date().toISOString(), status: 'pending', analysisId: null },
  }),
  history: {
    history: [
      { id: 'analysis1', documentName: 'TSLA-Q2-2025-Update.pdf', completedAt: '2025-10-05T01:00:00Z', status: 'complete' },
    ],
    total: 1,
  },
};

const simulateDelay = (ms = 800) => new Promise((resolve) => setTimeout(resolve, ms));

const validateFile = (file) => {
  if (!file) return 'No file selected';
  if (file.type !== 'application/pdf') return 'Only PDF files are allowed';
  if (file.size > 100 * 1024 * 1024) return 'File size exceeds 100MB';
  return null;
};

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const register = async (data) => {
  if (!data.username || !data.email || !data.password) {
    toast({ variant: 'destructive', title: 'All fields are required' });
    throw new Error('Invalid input');
  }
  if (config.testdata) {
    await simulateDelay();
    return mockData.register;
  }
  const res = await api.post('/auth/register', data);
  return res.data;
};

export const login = async (data) => {
  if (!data.email || !data.password) {
    toast({ variant: 'destructive', title: 'Email and password required' });
    throw new Error('Invalid input');
  }
  if (config.testdata) {
    await simulateDelay();
    localStorage.setItem('token', mockData.login.token);
    localStorage.setItem('refresh_token', mockData.login.refresh_token);
    return mockData.login;
  }
  const res = await api.post('/auth/login', data);
  localStorage.setItem('token', res.data.token);
  if (res.data.refresh_token) {
    localStorage.setItem('refresh_token', res.data.refresh_token);
  }
  return res.data;
};

export const logout = async () => {
  if (!config.testdata) {
    try {
      await api.post('/auth/logout');
    } catch {
      // best-effort
    }
  }
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  toast({ title: 'Logged out' });
  return { message: 'Logout successful' };
};

// ─── Documents ────────────────────────────────────────────────────────────────

export const getDocuments = async (params = {}) => {
  if (config.testdata) {
    await simulateDelay();
    const { search } = params;
    let filteredDocs = mockData.documents.documents;
    if (search) {
      filteredDocs = filteredDocs.filter((doc) => doc.name.toLowerCase().includes(search.toLowerCase()));
    }
    return { ...mockData.documents, documents: filteredDocs, total: filteredDocs.length };
  }
  const res = await api.get('/documents', { params });
  return res.data;
};

export const uploadDocument = async (formData) => {
  const file = formData.get('file');
  const validationError = validateFile(file);
  if (validationError) {
    toast({ variant: 'destructive', title: validationError });
    throw new Error(validationError);
  }
  if (config.testdata) {
    await simulateDelay();
    const newDoc = mockData.upload(file);
    mockData.documents.documents.unshift(newDoc.document);
    mockData.documents.total += 1;
    return newDoc;
  }
  const res = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const analyzeDocument = async (id, options = {}) => {
  if (!id) {
    toast({ variant: 'destructive', title: 'Document ID required' });
    throw new Error('Invalid document ID');
  }
  if (config.testdata) {
    await simulateDelay();
    const doc = mockData.documents.documents.find((d) => d.id === id);
    if (!doc) throw new Error('Document not found');
    doc.status = 'analyzing';
    setTimeout(() => {
      doc.status = 'complete';
      doc.analysisId = 'analysis1';
    }, 3000);
    return mockData.analyze(id);
  }
  const res = await api.post(`/documents/${id}/analyze`, { options });
  return res.data;
};

export const getDocumentStatus = async (id) => {
  if (!id) throw new Error('Invalid document ID');
  if (config.testdata) {
    await simulateDelay(300);
    const doc = mockData.documents.documents.find((d) => d.id === id);
    return { status: doc?.status || 'pending', analysisId: doc?.analysisId || null };
  }
  const res = await api.get(`/documents/${id}/status`);
  return res.data;
};

export const getAnalysisResult = async (id) => {
  if (!id) {
    toast({ variant: 'destructive', title: 'Document ID required' });
    throw new Error('Invalid document ID');
  }
  if (config.testdata) {
    await simulateDelay();
    const doc = mockData.documents.documents.find((d) => d.id === id);
    if (!doc || doc.status !== 'complete') throw new Error('Analysis not ready');
    return mockData.result;
  }
  const res = await api.get(`/documents/${id}/result`);
  return res.data;
};

export const deleteDocument = async (id) => {
  if (!id) {
    toast({ variant: 'destructive', title: 'Document ID required' });
    throw new Error('Invalid document ID');
  }
  if (config.testdata) {
    await simulateDelay();
    const idx = mockData.documents.documents.findIndex((d) => d.id === id);
    if (idx === -1) throw new Error('Document not found');
    mockData.documents.documents.splice(idx, 1);
    mockData.documents.total -= 1;
    toast({ title: 'Document deleted' });
    return { message: 'Document deleted' };
  }
  const res = await api.delete(`/documents/${id}`);
  toast({ title: 'Document deleted' });
  return res.data;
};

// ─── Analysis ─────────────────────────────────────────────────────────────────

export const getHistory = async (params = {}) => {
  if (config.testdata) {
    await simulateDelay();
    const { documentId } = params;
    let filtered = mockData.history.history;
    if (documentId) filtered = filtered.filter((h) => h.id === `analysis_${documentId}`);
    return { ...mockData.history, history: filtered, total: filtered.length };
  }
  const res = await api.get('/analysis/history', { params });
  return res.data;
};

export const exportAnalysis = async (id, format = 'pdf') => {
  if (!id) {
    toast({ variant: 'destructive', title: 'Analysis ID required' });
    throw new Error('Invalid analysis ID');
  }
  if (!['pdf', 'csv'].includes(format)) {
    toast({ variant: 'destructive', title: 'Invalid export format' });
    throw new Error('Invalid format');
  }
  if (config.testdata) {
    await simulateDelay();
    // Create a minimal placeholder blob in test mode
    const content = format === 'csv'
      ? 'Document Name,Confidence,Financial Summary\nTSLA-Q2-2025-Update.pdf,92%,Revenue up 15%'
      : '%PDF-1.4 mock pdf content';
    const blob = new Blob([content], { type: format === 'pdf' ? 'application/pdf' : 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    return { url, filename: `analysis_${id}.${format}` };
  }
  const res = await api.get(`/analysis/${id}/export`, {
    params: { format },
    responseType: 'blob',
  });
  const mimeType = format === 'pdf' ? 'application/pdf' : 'text/csv';
  const blob = new Blob([res.data], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  return { url, filename: `analysis_${id}.${format}` };
};
