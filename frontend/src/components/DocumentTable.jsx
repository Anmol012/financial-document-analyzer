import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { analyzeDocument, getAnalysisResult, deleteDocument } from '../api';
import { toast } from '@/components/ui/use-toast';
import { useState } from 'react';

const DocumentTable = ({ documents, onAnalyze, onViewResult }) => {
  const [analyzingIds, setAnalyzingIds] = useState([]);

  const handleAnalyze = async (id) => {
    setAnalyzingIds([...analyzingIds, id]);
    try {
      await analyzeDocument(id, {});
      toast({ title: 'Analysis started' });
      onAnalyze();
    } catch (err) {
      // Error handled in api.js
    }
    setAnalyzingIds(analyzingIds.filter(i => i !== id));
  };

  const handleViewResult = async (id, status) => {
    if (status !== 'complete') return;
    try {
      await getAnalysisResult(id);
      onViewResult(id);
    } catch (err) {
      // Error handled in api.js
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteDocument(id);
      onAnalyze(); // Refresh
    } catch (err) {
      // Error handled in api.js
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Upload Date</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <TableRow key={doc.id}>
            <TableCell>{doc.name}</TableCell>
            <TableCell>{new Date(doc.uploadDate).toLocaleDateString()}</TableCell>
            <TableCell>{doc.status}</TableCell>
            <TableCell className="space-x-2">
              <Button onClick={() => handleAnalyze(doc.id)} disabled={analyzingIds.includes(doc.id) || doc.status !== 'pending'}>
                {analyzingIds.includes(doc.id) ? 'Analyzing...' : 'Analyze'}
              </Button>
              <Button onClick={() => handleViewResult(doc.id, doc.status)} disabled={doc.status !== 'complete'}>Get Result</Button>
              <Button variant="destructive" onClick={() => handleDelete(doc.id)}>Delete</Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default DocumentTable;