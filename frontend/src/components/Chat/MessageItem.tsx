import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message, Citation } from '../../types';
import { CitationChip } from './CitationChip';
import { VerificationPanel } from './VerificationPanel';
import { ConfidenceMeter } from './ConfidenceMeter';
import { User, Activity, AlertCircle } from 'lucide-react';

interface MessageItemProps {
  message: Message;
  activeCitation?: Citation | null;
  onSelectCitation: (citation: Citation) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  activeCitation,
  onSelectCitation,
}) => {
  const isUser = message.role === 'user';

  // Helper to replace [1], [2] in text with interactive CitationChips
  const renderContentWithCitations = (text: string) => {
    if (isUser || !message.citations || message.citations.length === 0) {
      return (
        <div className="prose-clinical">
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
      );
    }

    // Split text by citation brackets e.g. [1], [2]
    const parts = text.split(/(\[\d+\])/g);

    return (
      <div className="prose-clinical">
        {parts.map((part, idx) => {
          const match = part.match(/^\[(\d+)\]$/);
          if (match) {
            const citIndex = parseInt(match[1], 10);
            const citation = message.citations?.find((c) => c.citation_index === citIndex);
            if (citation) {
              const isActive =
                activeCitation?.citation_index === citation.citation_index &&
                activeCitation?.page_number === citation.page_number;
              return (
                <CitationChip
                  key={idx}
                  citation={citation}
                  isActive={isActive}
                  onClick={onSelectCitation}
                />
              );
            }
          }
          return <ReactMarkdown key={idx} components={{ p: 'span' }}>{part}</ReactMarkdown>;
        })}
      </div>
    );
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '0.85rem',
        padding: '1rem',
        borderRadius: '12px',
        background: isUser ? 'rgba(30, 41, 59, 0.45)' : 'rgba(17, 24, 39, 0.75)',
        border: isUser ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid var(--border-subtle)',
        marginBottom: '1rem',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '34px',
          height: '34px',
          borderRadius: '10px',
          background: isUser
            ? 'linear-gradient(135deg, #475569, #334155)'
            : 'linear-gradient(135deg, #0284c7, #38bdf8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: isUser ? 'none' : '0 0 12px rgba(56, 189, 248, 0.3)',
        }}
      >
        {isUser ? <User size={18} color="#f8fafc" /> : <Activity size={18} color="#ffffff" />}
      </div>

      {/* Content Body */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Role & Telemetry Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.45rem',
            gap: '0.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: isUser ? '#cbd5e1' : '#38bdf8' }}>
              {isUser ? 'Clinician Consultation' : 'ClinSaarthi AI Guidance'}
            </span>
            {message.streaming && (
              <span
                style={{
                  fontSize: '0.68rem',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '9999px',
                  background: 'rgba(56, 189, 248, 0.2)',
                  color: '#38bdf8',
                  animation: 'pulseGlow 2s infinite',
                }}
              >
                Streaming SSE...
              </span>
            )}
          </div>

          {!isUser && (message.confidence_score !== undefined && message.confidence_score !== null || message.is_not_found) && (
            <ConfidenceMeter
              score={message.confidence_score}
              isNotFound={message.is_not_found}
            />
          )}
        </div>

        {/* Message Text with Citation Replacement */}
        <div style={{ color: 'var(--text-primary)' }}>
          {renderContentWithCitations(message.content)}
        </div>

        {/* Verification Panel */}
        {!isUser && message.verifications && message.verifications.length > 0 && (
          <VerificationPanel verifications={message.verifications} />
        )}

        {/* Medical Disclaimer Banner */}
        {!isUser && (
          <div
            style={{
              marginTop: '0.85rem',
              padding: '0.55rem 0.85rem',
              borderRadius: '8px',
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.5rem',
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
              lineHeight: 1.4,
            }}
          >
            <AlertCircle size={14} color="#94a3b8" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>
              {message.disclaimer ||
                'MANDATORY CLINICAL DISCLAIMER: ClinSaarthi AI is an automated decision-support reference intended strictly for qualified clinicians and supervised medical students. Always verify recommendations against primary literature and patient clinical presentation.'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
