import axios from 'axios';
import { config } from './config';
import { toast } from '@/components/ui/use-toast';

// Initialize Axios instance
const api = axios.create({
  baseURL: config.baseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000, // Add timeout to handle network issues
});

// Request interceptor for JWT authentication
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error || 'Network error';
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      toast({ variant: 'destructive', title: 'Session expired, please log in' });
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      toast({ variant: 'destructive', title: 'Rate limit exceeded' });
    } else {
      toast({ variant: 'destructive', title: message });
    }
    return Promise.reject(error);
  }
);

// Mock data (in-memory store for simulation)
const mockData = {
  documents: {
    documents: [
      { id: 'doc1', name: 'TSLA-Q2-2025-Update.pdf', uploadDate: '2025-10-05T00:00:00Z', status: 'complete', analysisId: 'analysis1' },
      { id: 'doc2', name: 'SampleReport.pdf', uploadDate: '2025-10-04T00:00:00Z', status: 'pending', analysisId: null },
    ],
    total: 2,
    page: 1,
  },
  login: { message: 'Login successful', token: 'fake-jwt-token', user: { id: 'user123', username: 'testuser', role: 'Viewer' } },
  analyze: (id) => ({ message: 'Analysis started', analysisId: `analysis_${id}` }),
  result: {
    analysis: {
      id: 'analysis1',
      documentId: 'doc1',
      results: {
        financialSummary: 'Tesla Q2 2025: Revenue up 15%',
        riskAssessment: { score: 0.75, details: 'Moderate risk due to market volatility' },
        recommendations: 'Buy with caution',
        chartsData: { revenueTrend: [{ year: '2024', value: 100 }, { year: '2025', value: 115 }] },
      },
      confidence: 0.92,
      completedAt: '2025-10-05T01:00:00Z',
    },
  },
  upload: (file) => ({
    message: 'Document uploaded',
    document: { id: `doc_${Date.now()}`, name: file.name, uploadDate: new Date().toISOString(), status: 'pending' },
  }),
  history: { history: [{ id: 'analysis1', documentName: 'TSLA-Q2-2025-Update.pdf', completedAt: '2025-10-05T01:00:00Z', status: 'complete' }], total: 1 },
  export: (id) => ({ message: 'Export generated', url: `mock_export_${id}.pdf` }),
};

// Simulate delay for mock responses
const simulateDelay = (ms = 1000) => new Promise((resolve) => setTimeout(resolve, ms));

// Simulate LLM observability logging
const logLLMCall = (endpoint, payload) => {
  console.log(`[LLM Observability] Called ${endpoint} with payload:`, payload);
  // Placeholder for integration with LangChain or similar
};

// Validate file for upload
const validateFile = (file) => {
  if (!file) return 'No file selected';
  if (file.type !== 'application/pdf') return 'Only PDF files are allowed';
  if (file.size > 100 * 1024 * 1024) return 'File size exceeds 100MB';
  return null;
};

export const login = async (data) => {
  logLLMCall('/auth/login', data);
  if (!data.email || !data.password) {
    toast({ variant: 'destructive', title: 'Email and password required' });
    throw new Error('Invalid input');
  }
  if (config.testdata) {
    await simulateDelay();
    localStorage.setItem('token', mockData.login.token);
    return mockData.login;
  }
  const res = await api.post('/auth/login', data);
  localStorage.setItem('token', res.data.token);
  return res.data;
};

export const logout = () => {
  localStorage.removeItem('token');
  toast({ title: 'Logged out' });
  return { message: 'Logout successful' };
};

export const getDocuments = async (params = {}) => {
  logLLMCall('/documents', params);
  if (config.testdata) {
    await simulateDelay();
    const { search } = params;
    let filteredDocs = mockData.documents.documents;
    if (search) {
      filteredDocs = filteredDocs.filter(doc => doc.name.toLowerCase().includes(search.toLowerCase()));
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
  logLLMCall('/documents/upload', { fileName: file.name });
  if (config.testdata) {
    await simulateDelay();
    const newDoc = mockData.upload(file);
    mockData.documents.documents.push(newDoc.document);
    mockData.documents.total += 1;
    return newDoc;
  }
  const res = await api.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  return res.data;
};

export const analyzeDocument = async (id, options = {}) => {
  logLLMCall(`/documents/${id}/analyze`, options);
  if (!id) {
    toast({ variant: 'destructive', title: 'Document ID required' });
    throw new Error('Invalid document ID');
  }
  if (config.testdata) {
    await simulateDelay();
    const docExists = mockData.documents.documents.find(doc => doc.id === id);
    if (!docExists) {
      toast({ variant: 'destructive', title: 'Document not found' });
      throw new Error('Document not found');
    }
    if (docExists.status !== 'pending') {
      toast({ variant: 'destructive', title: 'Document already analyzed or in progress' });
      throw new Error('Invalid document status');
    }
    // Simulate status update (use structured clone for thread safety)
    mockData.documents.documents = structuredClone(mockData.documents.documents).map(doc =>
      doc.id === id ? { ...doc, status: 'analyzing' } : doc
    );
    setTimeout(() => {
      mockData.documents.documents = structuredClone(mockData.documents.documents).map(doc =>
        doc.id === id ? { ...doc, status: 'complete', analysisId: `analysis_${id}` } : doc
      );
    }, 3000); // Simulate async completion
    return mockData.analyze(id);
  }
  const res = await api.post(`/documents/${id}/analyze`, options);
  return res.data;
};

export const getAnalysisResult = async (id) => {
  logLLMCall(`/documents/${id}/result`, {});
  if (!id) {
    toast({ variant: 'destructive', title: 'Document ID required' });
    throw new Error('Invalid document ID');
  }
  if (config.testdata) {
    await simulateDelay();
    const doc = mockData.documents.documents.find(d => d.id === id);
    if (!doc || doc.status !== 'complete') {
      toast({ variant: 'destructive', title: 'Analysis not complete or document not found' });
      throw new Error('Analysis not ready');
    }
    return mockData.result;
  }
  const res = await api.get(`/documents/${id}/result`);
  return res.data;
};

export const deleteDocument = async (id) => {
  logLLMCall(`/documents/${id}`, {});
  if (!id) {
    toast({ variant: 'destructive', title: 'Document ID required' });
    throw new Error('Invalid document ID');
  }
  if (config.testdata) {
    await simulateDelay();
    const docIndex = mockData.documents.documents.findIndex(doc => doc.id === id);
    if (docIndex === -1) {
      toast({ variant: 'destructive', title: 'Document not found' });
      throw new Error('Document not found');
    }
    mockData.documents.documents.splice(docIndex, 1);
    mockData.documents.total -= 1;
    // Remove related history
    mockData.history.history = mockData.history.history.filter(h => h.id !== `analysis_${id}`);
    mockData.history.total = mockData.history.history.length;
    toast({ title: 'Document deleted' });
    return { message: 'Document deleted' };
  }
  const res = await api.delete(`/documents/${id}`);
  return res.data;
};

export const getHistory = async (params = {}) => {
  logLLMCall('/analysis/history', params);
  if (config.testdata) {
    await simulateDelay();
    const { documentId } = params;
    let filteredHistory = mockData.history.history;
    if (documentId) {
      filteredHistory = filteredHistory.filter(h => h.id === `analysis_${documentId}`);
    }
    return { ...mockData.history, history: filteredHistory, total: filteredHistory.length };
  }
  const res = await api.get('/analysis/history', { params });
  return res.data;
};

export const exportAnalysis = async (id, format = 'pdf') => {
  logLLMCall(`/analysis/${id}/export`, { format });
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
    const doc = mockData.documents.documents.find(d => d.analysisId === id);
    if (!doc || doc.status !== 'complete') {
      toast({ variant: 'destructive', title: 'Analysis not found or incomplete' });
      throw new Error('Analysis not ready');
    }
    return mockData.export(id);
  }
  const res = await api.get(`/analysis/${id}/export`, { params: { format } });
  return res.data;
};