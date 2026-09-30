import React, { useState } from 'react';
import type { Citation, AppMode } from '../../types';
import { PDFSourceCanvas } from './PDFSourceCanvas';
import { NoteDiffViewer } from './NoteDiffViewer';
import { FileText, ShieldAlert } from 'lucide-react';

interface SourceViewerProps {
  activeCitation?: Citation | null;
  activeMode: AppMode;
  documentTitle?: string;
  onSelectNoteForQA?: (noteId: string, noteTitle: string) => void;
}

export const SourceViewer: React.FC<SourceViewerProps> = ({
  activeCitation,
  activeMode,
  documentTitle,
  onSelectNoteForQA,
}) => {
  const [tab, setTab] = useState<'pdf' | 'notes'>(activeMode === 'clinical_note_qa' ? 'notes' : 'pdf');

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#090d16',
        borderLeft: '1px solid var(--border-subtle)',
      }}
    >
      {/* Tab Switcher Header */}
      <div
        style={{
          padding: '0.4rem 1rem',
          display: 'flex',
          gap: '0.5rem',
          background: 'rgba(15, 23, 42, 0.8)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <button
          onClick={() => setTab('pdf')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '6px',
            border: 'none',
            fontSize: '0.76rem',
            fontWeight: 600,
            cursor: 'pointer',
            background: tab === 'pdf' ? '#0284c7' : 'transparent',
            color: tab === 'pdf' ? '#ffffff' : 'var(--text-muted)',
            transition: 'all 0.2s',
          }}
        >
          <FileText size={14} />
          Guideline PDF Viewer
        </button>

        <button
          onClick={() => setTab('notes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '6px',
            border: 'none',
            fontSize: '0.76rem',
            fontWeight: 600,
            cursor: 'pointer',
            background: tab === 'notes' ? '#0284c7' : 'transparent',
            color: tab === 'notes' ? '#ffffff' : 'var(--text-muted)',
            transition: 'all 0.2s',
          }}
        >
          <ShieldAlert size={14} />
          PII Redaction Diff
        </button>
      </div>

      {/* Main Viewer Body */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {tab === 'pdf' ? (
          <PDFSourceCanvas
            activeCitation={activeCitation}
            documentTitle={documentTitle}
          />
        ) : (
          <NoteDiffViewer onSelectNoteForQA={onSelectNoteForQA} />
        )}
      </div>
    </div>
  );
};
