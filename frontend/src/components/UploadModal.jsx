import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { uploadDocument } from '../api';
import { toast } from '@/components/ui/use-toast';

const UploadModal = ({ open, onClose, onSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    // Simulate progress
    const interval = setInterval(() => setProgress((p) => Math.min(p + 10, 100)), 200);

    try {
      const data = await uploadDocument(formData);
      onSuccess(data);
      clearInterval(interval);
      setProgress(100);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Upload failed' });
      clearInterval(interval);
    }
    setUploading(false);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Label htmlFor="file">Select PDF</Label>
          <Input id="file" type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
          {uploading && <Progress value={progress} />}
          <Button onClick={handleUpload} disabled={uploading || !file}>
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UploadModal;