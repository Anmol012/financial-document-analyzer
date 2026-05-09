import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { getAnalysisResult, getDocumentStatus, exportAnalysis } from '../api';
import { toast } from '@/components/ui/use-toast';

const POLL_INTERVAL = 3000;

const AnalysisDashboard = ({ docId, onClose }) => {
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState('loading');
  const pollRef = useRef(null);

  useEffect(() => {
    checkAndFetch();
    return () => clearInterval(pollRef.current);
  }, [docId]);

  const checkAndFetch = async () => {
    try {
      const statusData = await getDocumentStatus(docId);

      if (statusData.status === 'complete') {
        clearInterval(pollRef.current);
        const data = await getAnalysisResult(docId);
        setAnalysis(data.analysis);
        setStatus('complete');
      } else if (statusData.status === 'failed') {
        clearInterval(pollRef.current);
        setStatus('failed');
      } else {
        setStatus('analyzing');
        if (!pollRef.current) {
          pollRef.current = setInterval(checkAndFetch, POLL_INTERVAL);
        }
      }
    } catch {
      clearInterval(pollRef.current);
      setStatus('error');
    }
  };

  const handleExport = async (format) => {
    try {
      const { url, filename } = await exportAnalysis(analysis.id, format);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast({ title: `${format.toUpperCase()} downloaded` });
    } catch {
      // error already shown by api.js
    }
  };

  if (status === 'loading') {
    return (
      <Card className="mt-8">
        <CardContent className="p-6 text-center text-muted-foreground">Checking status...</CardContent>
      </Card>
    );
  }

  if (status === 'analyzing') {
    return (
      <Card className="mt-8">
        <CardContent className="p-6 text-center">
          <p className="text-muted-foreground animate-pulse">Analysis in progress — checking every 3 seconds...</p>
          <Button variant="outline" className="mt-4" onClick={onClose}>Close</Button>
        </CardContent>
      </Card>
    );
  }

  if (status === 'failed' || status === 'error') {
    return (
      <Card className="mt-8">
        <CardContent className="p-6 text-center text-destructive">
          <p>Analysis failed. Please try again.</p>
          <Button variant="outline" className="mt-4" onClick={onClose}>Close</Button>
        </CardContent>
      </Card>
    );
  }

  if (!analysis) return null;

  const results = analysis.results || {};
  const riskAssessment = results.riskAssessment || {};
  const chartsData = results.chartsData || {};
  const revenueTrend = chartsData.revenueTrend || [];
  const profitMargin = chartsData.profitMargin || [];
  const riskScore = typeof riskAssessment.score === 'number' ? riskAssessment.score : 0;
  const riskPercent = Math.round(riskScore * 100);

  const riskColor =
    riskScore < 0.33 ? 'text-green-600' :
    riskScore < 0.66 ? 'text-yellow-600' :
    'text-red-600';

  return (
    <Card className="mt-8">
      <CardHeader className="flex justify-between flex-row items-center flex-wrap gap-2">
        <CardTitle>Analysis Dashboard</CardTitle>
        <div className="flex gap-2 flex-wrap">
          <Button size="sm" onClick={() => handleExport('pdf')}>Export PDF</Button>
          <Button size="sm" variant="outline" onClick={() => handleExport('csv')}>Export CSV</Button>
          <Button size="sm" variant="ghost" onClick={onClose}>Close</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-8">

        {/* Confidence */}
        <p className="text-sm text-muted-foreground">
          Confidence: <span className="font-semibold">{Math.round(analysis.confidence * 100)}%</span>
        </p>

        {/* Financial Summary */}
        <section>
          <h3 className="font-semibold text-lg mb-2">Financial Summary</h3>
          <p className="text-sm leading-relaxed">{results.financialSummary || 'No summary available.'}</p>
        </section>

        {/* Risk Assessment */}
        <section>
          <h3 className="font-semibold text-lg mb-2">Risk Assessment</h3>
          <p className={`text-2xl font-bold ${riskColor}`}>{riskPercent}% <span className="text-sm font-normal text-muted-foreground">(0 = low risk, 100 = high risk)</span></p>
          {riskAssessment.details && (
            <p className="text-sm mt-2 leading-relaxed">{riskAssessment.details}</p>
          )}
        </section>

        {/* Market Insights */}
        {results.marketInsights && (
          <section>
            <h3 className="font-semibold text-lg mb-2">Market Insights</h3>
            <p className="text-sm leading-relaxed">{results.marketInsights}</p>
          </section>
        )}

        {/* Recommendations */}
        <section>
          <h3 className="font-semibold text-lg mb-2">Recommendations</h3>
          <p className="text-sm leading-relaxed">{results.recommendations || 'No recommendations available.'}</p>
        </section>

        {/* Revenue Trend Chart */}
        {revenueTrend.length > 0 && (
          <section>
            <h3 className="font-semibold text-lg mb-4">Revenue Trend</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={revenueTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} name="Revenue" />
              </LineChart>
            </ResponsiveContainer>
          </section>
        )}

        {/* Profit Margin Chart */}
        {profitMargin.length > 0 && (
          <section>
            <h3 className="font-semibold text-lg mb-4">Profit Margin (%)</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={profitMargin}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="quarter" />
                <YAxis unit="%" />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="value" fill="#22c55e" name="Margin" />
              </BarChart>
            </ResponsiveContainer>
          </section>
        )}

      </CardContent>
    </Card>
  );
};

export default AnalysisDashboard;
