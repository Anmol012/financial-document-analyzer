import { useState, useEffect } from 'react';
import DocumentTable from '../components/DocumentTable';
import UploadModal from '../components/UploadModal';
import AnalysisDashboard from '../components/AnalysisDashboard';
import { Button } from '@/components/ui/button';
import { getDocuments } from '../api';
import { toast } from '@/components/ui/use-toast';

const Dashboard = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000);  // Poll for status updates
    return () => clearInterval(interval);
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data.documents);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed to load documents' });
    }
    setLoading(false);
  };

  const handleUploadSuccess = (newDoc) => {
    setDocuments([...documents, newDoc.document]);
    setShowUpload(false);
    toast({ title: 'Document uploaded' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between">
        <h2 className="text-xl font-semibold">Documents</h2>
        <Button onClick={() => setShowUpload(true)}>Add Document</Button>
      </div>
      {loading ? <p>Loading...</p> : <DocumentTable documents={documents} onAnalyze={fetchDocuments} onViewResult={setSelectedDoc} />}
      <UploadModal open={showUpload} onClose={() => setShowUpload(false)} onSuccess={handleUploadSuccess} />
      {selectedDoc && <AnalysisDashboard docId={selectedDoc} onClose={() => setSelectedDoc(null)} />}
    </div>
  );
};

export default Dashboard;