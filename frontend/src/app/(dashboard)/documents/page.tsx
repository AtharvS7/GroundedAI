'use client';

import { useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, UploadCloud, FileText, File, Trash2, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import { getDocuments, uploadDocument, deleteDocument } from '@/lib/api';
import { formatFileSize, formatDate } from '@/lib/utils';
import type { Document } from '@/types';

const typeIcons: Record<string, string> = { pdf: '📄', docx: '📝', txt: '📃' };

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const [isDragging, setIsDragging] = useState(false);

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: getDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  });

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((file) => uploadMutation.mutate(file));
  }, [uploadMutation]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const statusBadge = (status: string) => {
    const styles: Record<string, { color: string; bg: string }> = {
      indexed: { color: '#10B981', bg: 'rgba(16,185,129,0.1)' },
      processing: { color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' },
      failed: { color: '#EF4444', bg: 'rgba(239,68,68,0.1)' },
    };
    const s = styles[status] || styles.failed;
    return (
      <span style={{
        fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 999,
        color: s.color, background: s.bg, textTransform: 'capitalize',
        display: 'inline-flex', alignItems: 'center', gap: 4,
      }}>
        {status === 'processing' && <span style={{ display: 'inline-block', width: 10, height: 10, border: '2px solid', borderColor: `${s.color} transparent transparent transparent`, borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />}
        {status}
      </span>
    );
  };

  return (
    <div style={{ padding: '32px 40px', overflow: 'auto', flex: 1 }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#E6EDF3', margin: 0 }}>Documents</h1>
          <p style={{ fontSize: 14, color: '#8B949E', marginTop: 4 }}>Manage your indexed document library</p>
        </div>
        <label style={{
          padding: '10px 20px', background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
          borderRadius: 10, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, transition: 'all 0.18s',
        }}>
          <Upload size={16} /> Upload Document
          <input type="file" accept=".pdf,.docx,.txt" multiple hidden onChange={(e) => handleFiles(e.target.files)} />
        </label>
      </div>

      {/* Upload Zone */}
      <div
        onDragEnter={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragging ? '#6C63FF' : '#30363D'}`,
          borderRadius: 18, padding: '40px 24px', textAlign: 'center', marginBottom: 24,
          background: isDragging ? 'rgba(108,99,255,0.05)' : 'transparent',
          transition: 'all 0.2s', cursor: 'pointer',
        }}
        onClick={() => document.querySelector<HTMLInputElement>('input[type="file"]')?.click()}
      >
        <UploadCloud size={32} style={{ color: '#6C63FF', marginBottom: 12 }} />
        <div style={{ fontSize: 15, fontWeight: 600, color: '#E6EDF3' }}>Drag and drop files here</div>
        <div style={{ fontSize: 13, color: '#8B949E', marginTop: 4 }}>or click to browse</div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 12 }}>
          {['PDF', 'DOCX', 'TXT'].map((t) => (
            <span key={t} style={{
              fontSize: 11, padding: '3px 10px', borderRadius: 999, background: '#161B22',
              color: '#8B949E', border: '1px solid #21262D',
            }}>{t}</span>
          ))}
        </div>
        <div style={{ fontSize: 12, color: '#484F58', marginTop: 8 }}>Max 50MB per file</div>
      </div>

      {/* Upload progress */}
      {uploadMutation.isPending && (
        <div style={{
          padding: '12px 16px', background: 'rgba(108,99,255,0.1)',
          border: '1px solid rgba(108,99,255,0.3)', borderRadius: 10, marginBottom: 16,
          fontSize: 13, color: '#6C63FF', display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ width: 14, height: 14, border: '2px solid', borderColor: '#6C63FF transparent transparent transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />
          Uploading and indexing document...
        </div>
      )}

      {/* Document Table */}
      <div style={{ background: '#161B22', borderRadius: 18, overflow: 'hidden', border: '1px solid #21262D' }}>
        {documents.length === 0 ? (
          <div style={{ padding: '60px 24px', textAlign: 'center' }}>
            <FileText size={48} style={{ color: '#484F58', marginBottom: 16 }} />
            <div style={{ fontSize: 15, fontWeight: 600, color: '#E6EDF3' }}>No documents yet</div>
            <div style={{ fontSize: 13, color: '#8B949E', marginTop: 4 }}>Upload your first document to get started</div>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #21262D' }}>
                {['File', 'Type', 'Size', 'Uploaded', 'Chunks', 'Status', ''].map((h) => (
                  <th key={h} style={{ padding: '12px 16px', fontSize: 11, fontWeight: 600, color: '#8B949E', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {documents.map((doc: Document) => (
                <motion.tr key={doc.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  style={{ borderBottom: '1px solid #21262D', transition: 'background 0.15s' }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#1C2128'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                >
                  <td style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 18 }}>{typeIcons[doc.file_type] || '📄'}</span>
                    <span style={{ fontSize: 13, fontWeight: 500, color: '#E6EDF3' }}>{doc.filename}</span>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: 12, color: '#8B949E', textTransform: 'uppercase' }}>{doc.file_type}</td>
                  <td style={{ padding: '14px 16px', fontSize: 12, color: '#8B949E' }}>{formatFileSize(doc.file_size_bytes)}</td>
                  <td style={{ padding: '14px 16px', fontSize: 12, color: '#8B949E' }}>{formatDate(doc.uploaded_at)}</td>
                  <td style={{ padding: '14px 16px', fontSize: 12, color: '#8B949E' }}>{doc.chunk_count}</td>
                  <td style={{ padding: '14px 16px' }}>{statusBadge(doc.status)}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <button
                      onClick={() => deleteMutation.mutate(doc.id)}
                      style={{ background: 'none', border: 'none', color: '#8B949E', cursor: 'pointer', padding: 4, borderRadius: 6 }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = '#EF4444'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = '#8B949E'; }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
