import React, { useState, useEffect, useRef } from 'react';
import type { Message, Citation, AppMode, DocumentSummary } from '../../types';
import { MessageItem } from './MessageItem';
import {
  Send,
  Sparkles,
  Bot,
  Brain,
  ShieldCheck,
  RefreshCw,
  Search,
  FileText,
  BookOpen,
  Layers,
  Upload,
  Loader2,
} from 'lucide-react';

interface ChatPanelProps {
  messages: Message[];
  isStreaming: boolean;
  streamingStatus?: string;
  activeMode?: AppMode;
  activeNoteTitle?: string;
  documents?: DocumentSummary[];
  selectedDocumentId?: string | null;
  onSelectDocument?: (documentId: string | null) => void;
  onUploadGuideline?: (file: File) => Promise<void>;
  onSendMessage: (query: string, useAgentic: boolean) => void;
  onClearChat: () => void;
  activeCitation?: Citation | null;
  onSelectCitation: (citation: Citation) => void;
}

const NOTE_PRESETS = [
  'Does this patient qualify for DOAC therapy under current AF guidelines?',
  "Is the prescribed Rivaroxaban 15 mg dosage appropriate for this patient's CrCl 38 mL/min?",
  'Summarize discharge instructions and drug safety warnings for this patient.',
];

const DOMAIN_PRESETS: Record<
  string,
  { label: string; specialty: string; color: string; presets: string[] }
> = {
  diabetes: {
    label: 'ADA Type 2 Diabetes Management',
    specialty: 'Endocrinology',
    color: '#10b981',
    presets: [
      'When should SGLT2 inhibitors or GLP-1 RAs be initiated for cardiorenal protection in T2D?',
      'What are the eGFR thresholds and dosing guidelines for Metformin in renal impairment?',
      'What is the emergency Rule of 15 protocol for acute hypoglycemia?',
      'What is the recommended basal insulin starting dose and titration schedule?',
    ],
  },
  afib: {
    label: 'AHA/ACC/HRS Atrial Fibrillation',
    specialty: 'Cardiology',
    color: '#0284c7',
    presets: [
      'What is the recommended first-line anticoagulant for non-valvular AF?',
      'What is the dose of Rivaroxaban in renal impairment (CrCl 15-49 mL/min)?',
      'What is the CHA2DS2-VASc score threshold to initiate oral anticoagulation?',
      'What are the mandatory anticoagulation durations before and after elective cardioversion?',
    ],
  },
  hypertension: {
    label: 'ACC/AHA High Blood Pressure',
    specialty: 'Cardiovascular',
    color: '#f59e0b',
    presets: [
      'What is the BP threshold to initiate dual-combination antihypertensive therapy?',
      'What is the target blood pressure for adults with confirmed hypertension?',
      'What is the recommended fourth-line agent for resistant hypertension?',
      'What is the recommended initial BP reduction goal in a hypertensive emergency?',
    ],
  },
  copd: {
    label: 'GOLD Strategy for COPD',
    specialty: 'Pulmonology',
    color: '#8b5cf6',
    presets: [
      'What spirometry FEV1/FVC ratio confirms a persistent airflow limitation in COPD?',
      'When should an Inhaled Corticosteroid (ICS) be added to LABA+LAMA therapy?',
      'What is the target oxygen saturation SpO2 during acute COPD exacerbations?',
      'What is the recommended systemic corticosteroid course for acute COPD exacerbations?',
    ],
  },
  pneumonia: {
    label: 'IDSA/ATS Community-Acquired Pneumonia',
    specialty: 'Infectious Disease',
    color: '#ec4899',
    presets: [
      'What is the CURB-65 triage score threshold for outpatient vs hospital admission in CAP?',
      'What is the recommended empiric first-line outpatient regimen for CAP without comorbidities?',
      'When should empiric coverage for MRSA and Pseudomonas aeruginosa be added in CAP?',
      'What are the diagnostic criteria confirming community-acquired pneumonia?',
    ],
  },
  all: {
    label: 'All Guidelines (Cross-Domain Search)',
    specialty: 'Cross-Domain RAG',
    color: '#38bdf8',
    presets: [
      'What is the recommended first-line anticoagulant for non-valvular AF?',
      'When should SGLT2 inhibitors or GLP-1 RAs be initiated for cardiorenal protection?',
      'What is the target blood pressure for adults with confirmed hypertension?',
      'What is the CURB-65 triage score threshold for outpatient vs hospital admission in CAP?',
    ],
  },
};

function getDocDomain(doc?: DocumentSummary | null): string {
  if (!doc) return 'all';
  const text = (doc.title + ' ' + (doc.file_name || '')).toLowerCase();
  if (text.includes('diabet') || text.includes('ada') || text.includes('endocrin')) return 'diabetes';
  if (text.includes('fibril') || text.includes('afib') || text.includes('arrhythmia')) return 'afib';
  if (text.includes('hypertens') || text.includes('blood pressure') || text.includes('htn')) return 'hypertension';
  if (text.includes('copd') || text.includes('gold') || text.includes('pulmon')) return 'copd';
  if (text.includes('pneumon') || text.includes('cap') || text.includes('infect')) return 'pneumonia';
  return 'all';
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isStreaming,
  streamingStatus,
  activeMode = 'guideline_qa',
  activeNoteTitle,
  documents = [],
  selectedDocumentId,
  onSelectDocument,
  onUploadGuideline,
  onSendMessage,
  onClearChat,
  activeCitation,
  onSelectCitation,
}) => {
  const [input, setInput] = useState('');
  const [useAgentic, setUseAgentic] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Find currently selected document
  const selectedDoc = documents.find((d) => d.id === selectedDocumentId) || null;
  const activeDomain = selectedDoc ? getDocDomain(selectedDoc) : 'all';
  const domainConfig = DOMAIN_PRESETS[activeDomain] || DOMAIN_PRESETS.all;

  const presets = activeMode === 'clinical_note_qa' ? NOTE_PRESETS : domainConfig.presets;

  // Auto-scroll to bottom when new messages or streaming tokens arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingStatus]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSendMessage(trimmed, useAgentic);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !onUploadGuideline) return;
    try {
      setIsUploading(true);
      await onUploadGuideline(file);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'var(--bg-main)',
        position: 'relative',
      }}
    >
      {/* Top Action Bar */}
      <div
        style={{
          padding: '0.65rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(15, 23, 42, 0.4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem' }}>
          <Bot size={15} color="#38bdf8" />
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            Clinical Consultation Thread
          </span>
          <span style={{ color: 'var(--text-muted)' }}>({messages.length} messages)</span>
          {activeMode === 'clinical_note_qa' && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                marginLeft: '0.4rem',
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#34d399',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '0.15rem 0.5rem',
                borderRadius: '9999px',
                fontSize: '0.7rem',
                fontWeight: 600,
              }}
            >
              <FileText size={11} />
              {activeNoteTitle || 'Patient Note Active'}
            </span>
          )}
        </div>

        <button
          onClick={onClearChat}
          title="Reset conversation thread"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            padding: '0.25rem 0.6rem',
            borderRadius: '6px',
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontSize: '0.72rem',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={12} />
          Clear Chat
        </button>
      </div>

      {/* Guideline Selector & Multi-PDF Scope Bar */}
      {activeMode === 'guideline_qa' && (
        <div
          style={{
            padding: '0.55rem 1.25rem',
            background: 'rgba(15, 23, 42, 0.75)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '280px' }}>
            <BookOpen size={15} color="#38bdf8" />
            <span style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
              Guideline Scope:
            </span>
            <select
              value={selectedDocumentId || ''}
              onChange={(e) => onSelectDocument && onSelectDocument(e.target.value || null)}
              style={{
                flex: 1,
                background: 'rgba(30, 41, 59, 0.85)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                borderRadius: '6px',
                color: '#f8fafc',
                padding: '0.3rem 0.6rem',
                fontSize: '0.76rem',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="">📚 All Certified Clinical Guidelines ({documents.length} Indexed PDFs)</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  📄 {doc.title} ({doc.total_pages} pgs, {doc.total_chunks} chunks)
                </option>
              ))}
            </select>
          </div>

          {/* Specialty Badge & Upload PDF Action */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                padding: '0.2rem 0.55rem',
                borderRadius: '9999px',
                background: `${domainConfig.color}22`,
                color: domainConfig.color,
                border: `1px solid ${domainConfig.color}44`,
                fontSize: '0.7rem',
                fontWeight: 600,
              }}
            >
              <Layers size={11} />
              {domainConfig.specialty}
            </span>

            {onUploadGuideline && (
              <label
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.25rem 0.6rem',
                  borderRadius: '6px',
                  background: 'rgba(2, 132, 199, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  color: '#38bdf8',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: isUploading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                }}
                title="Upload additional medical practice guideline PDF"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  style={{ display: 'none' }}
                  disabled={isUploading}
                  onChange={handlePdfUpload}
                />
                {isUploading ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
                <span>{isUploading ? 'Ingesting PDF...' : 'Upload PDF'}</span>
              </label>
            )}
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              margin: 'auto',
              textAlign: 'center',
              maxWidth: '540px',
              padding: '1.5rem 1rem',
            }}
          >
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.2), rgba(99, 102, 241, 0.2))',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem auto',
                boxShadow: '0 0 20px rgba(56, 189, 248, 0.2)',
              }}
            >
              <Sparkles size={28} color="#38bdf8" />
            </div>

            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem', color: '#f8fafc' }}>
              {activeMode === 'clinical_note_qa'
                ? 'Clinical Note & Guideline Analysis'
                : selectedDoc
                ? selectedDoc.title
                : 'Welcome to ClinSaarthi AI'}
            </h2>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              {activeMode === 'clinical_note_qa'
                ? `Query ${activeNoteTitle ? `"${activeNoteTitle}"` : 'patient clinical notes'} grounded directly against verified clinical guidelines. Bounding boxes & PII audit trails are fully retained.`
                : selectedDoc
                ? `Grounded clinical retrieval scoped strictly to this guideline (${selectedDoc.total_pages} pages, ${selectedDoc.total_chunks} vectorized chunks). Citations link to exact PyMuPDF bounding coordinates.`
                : `Query across ${documents.length || 5} certified multi-column clinical practice guidelines with zero hallucinations. Every claim is grounded, cited to exact page coordinates, and fact-verified via RxNorm.`}
            </p>

            {/* Quick Suggestion Pills */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                  {activeMode === 'clinical_note_qa'
                    ? 'Try patient-guideline comparison questions:'
                    : selectedDoc
                    ? `High-yield clinical questions for ${domainConfig.label}:`
                    : 'Try clinical questions across all guidelines:'}
                </span>
                <span
                  style={{
                    fontSize: '0.68rem',
                    color: domainConfig.color,
                    fontWeight: 600,
                  }}
                >
                  {domainConfig.specialty}
                </span>
              </div>

              {presets.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(q, useAgentic)}
                  style={{
                    padding: '0.6rem 0.85rem',
                    borderRadius: '8px',
                    background: 'rgba(30, 41, 59, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    color: '#e2e8f0',
                    fontSize: '0.78rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#38bdf8';
                    e.currentTarget.style.background = 'rgba(56, 189, 248, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                    e.currentTarget.style.background = 'rgba(30, 41, 59, 0.6)';
                  }}
                >
                  <Search size={13} style={{ display: 'inline', marginRight: '6px', color: '#38bdf8' }} />
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                activeCitation={activeCitation}
                onSelectCitation={onSelectCitation}
              />
            ))}
          </>
        )}

        {/* Live Streaming Stage Pill */}
        {isStreaming && streamingStatus && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.45rem 0.85rem',
              borderRadius: '9999px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              color: '#38bdf8',
              fontSize: '0.75rem',
              fontWeight: 600,
              width: 'fit-content',
              marginBottom: '1rem',
              animation: 'pulseGlow 2s infinite',
            }}
          >
            <Brain size={14} className="animate-spin" />
            <span>{streamingStatus}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Footer */}
      <div
        style={{
          padding: '0.85rem 1.25rem',
          borderTop: '1px solid var(--border-subtle)',
          background: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Verification Toggle Pill */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.74rem',
              color: useAgentic ? '#38bdf8' : 'var(--text-muted)',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <input
              type="checkbox"
              checked={useAgentic}
              onChange={(e) => setUseAgentic(e.target.checked)}
              style={{ accentColor: '#0284c7' }}
            />
            <ShieldCheck size={14} />
            <span style={{ fontWeight: 600 }}>LangGraph Multi-Node Verification Agent</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
              (RxNorm + openFDA cross-check)
            </span>
          </label>

          {selectedDoc && (
            <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
              Scoped to: <strong style={{ color: '#38bdf8' }}>{selectedDoc.file_name}</strong>
            </span>
          )}
        </div>

        {/* Form Container */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.65rem' }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              activeMode === 'clinical_note_qa'
                ? 'Ask about this patient note against guidelines (e.g. Is Rivaroxaban 15 mg appropriate for CrCl 38 mL/min?)...'
                : selectedDoc
                ? `Ask clinical question about ${domainConfig.label} (e.g. dosing, contraindications, protocols)...`
                : 'Ask a clinical question across all medical guidelines (e.g. Rivaroxaban dosing, Metformin eGFR cutoffs)...'
            }
            rows={2}
            style={{
              flex: 1,
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '0.65rem 0.85rem',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              fontFamily: 'var(--font-sans)',
              resize: 'none',
              outline: 'none',
            }}
          />

          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '10px',
              border: 'none',
              background: !input.trim() || isStreaming ? 'rgba(56, 189, 248, 0.2)' : '#0284c7',
              color: '#ffffff',
              cursor: !input.trim() || isStreaming ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              alignSelf: 'flex-end',
              boxShadow: input.trim() && !isStreaming ? '0 0 12px rgba(2, 132, 199, 0.4)' : 'none',
              transition: 'all 0.2s',
            }}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
