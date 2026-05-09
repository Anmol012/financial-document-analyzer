import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { analyzeDocument, deleteDocument } from '../api';
import { toast } from '@/components/ui/use-toast';
import { useState } from 'react';

const STATUS_LABEL = {
  pending: 'Pending',
  analyzing: 'Analyzing…',
  complete: 'Complete',
  failed: 'Failed',
};

const DocumentTable = ({ documents, onAnalyze, onViewResult }) => {
  const [loadingIds, setLoadingIds] = useState([]);

  const setLoading = (id, on) =>
    setLoadingIds((prev) => on ? [...prev, id] : prev.filter((i) => i !== id));

  const handleAnalyze = async (id) => {
    setLoading(id, true);
    try {
      await analyzeDocument(id, {});
      toast({ title: 'Analysis started — status will update automatically' });
      onAnalyze();
    } catch {
      // error already shown by api.js
    }
    setLoading(id, false);
  };

  const handleViewResult = (id, status) => {
    if (status !== 'complete') return;
    onViewResult(id);
  };

  const handleDelete = async (id) => {
    setLoading(id, true);
    try {
      await deleteDocument(id);
      onAnalyze(); // refresh list
    } catch {
      // error already shown by api.js
    }
    setLoading(id, false);
  };

  const canAnalyze = (doc) => ['pending', 'failed'].includes(doc.status);

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
        {documents.length === 0 && (
          <TableRow>
            <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
              No documents found. Upload a PDF to get started.
            </TableCell>
          </TableRow>
        )}
        {documents.map((doc) => {
          const busy = loadingIds.includes(doc.id);
          return (
            <TableRow key={doc.id}>
              <TableCell className="font-medium">{doc.name}</TableCell>
              <TableCell>{new Date(doc.uploadDate).toLocaleDateString()}</TableCell>
              <TableCell>
                <span className={
                  doc.status === 'complete' ? 'text-green-600 font-medium' :
                  doc.status === 'failed' ? 'text-red-500' :
                  doc.status === 'analyzing' ? 'text-yellow-600 animate-pulse' :
                  'text-muted-foreground'
                }>
                  {STATUS_LABEL[doc.status] || doc.status}
                </span>
              </TableCell>
              <TableCell className="space-x-2">
                <Button
                  size="sm"
                  onClick={() => handleAnalyze(doc.id)}
                  disabled={busy || !canAnalyze(doc)}
                >
                  {busy && canAnalyze(doc) ? 'Starting…' : 'Analyze'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleViewResult(doc.id, doc.status)}
                  disabled={doc.status !== 'complete'}
                >
                  View Result
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleDelete(doc.id)}
                  disabled={busy}
                >
                  Delete
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

export default DocumentTable;
