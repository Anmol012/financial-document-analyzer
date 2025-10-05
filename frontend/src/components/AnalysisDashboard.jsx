import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getAnalysisResult, exportAnalysis } from '../api';
import { toast } from '@/components/ui/use-toast';

const AnalysisDashboard = ({ docId, onClose }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResult();
  }, [docId]);

  const fetchResult = async () => {
    try {
      const data = await getAnalysisResult(docId);
      setAnalysis(data.analysis);
    } catch (err) {
      // Error handled in api.js
    }
    setLoading(false);
  };

  const handleExport = async () => {
    try {
      const data = await exportAnalysis(analysis.id, 'pdf');
      // Simulate download
      const link = document.createElement('a');
      link.href = data.url;
      link.download = `analysis_${analysis.id}.pdf`;
      link.click();
      toast({ title: 'Export downloaded' });
    } catch (err) {
      // Error handled in api.js
    }
  };

  if (loading) return <p>Loading analysis...</p>;

  return (
    <Card className="mt-8">
      <CardHeader className="flex justify-between flex-row items-center">
        <CardTitle>Analysis Dashboard</CardTitle>
        <div className="space-x-2">
          <Button onClick={handleExport}>Export PDF</Button>
          <Button variant="outline" onClick={onClose}>Close</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <section>
          <h3 className="font-semibold">Financial Summary</h3>
          <p>{analysis.results.financialSummary}</p>
        </section>
        <section>
          <h3 className="font-semibold">Risk Assessment</h3>
          <p>Score: {analysis.results.riskAssessment.score}</p>
          <p>{analysis.results.riskAssessment.details}</p>
        </section>
        <section>
          <h3 className="font-semibold">Recommendations</h3>
          <p>{analysis.results.recommendations}</p>
        </section>
        <section>
          <h3 className="font-semibold">Revenue Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analysis.results.chartsData.revenueTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </section>
        <p>Confidence: {analysis.confidence * 100}%</p>
      </CardContent>
    </Card>
  );
};

export default AnalysisDashboard;