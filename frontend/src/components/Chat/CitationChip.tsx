import type { Citation } from '../../types';
import { ExternalLink } from 'lucide-react';

interface CitationChipProps {
  citation: Citation;
  isActive: boolean;
  onClick: (citation: Citation) => void;
}

export const CitationChip: React.FC<CitationChipProps> = ({
  citation,
  isActive,
  onClick,
}) => {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick(citation);
      }}
      title={`Source: ${citation.source_title} (Page ${citation.page_number})\nSection: ${citation.section_title || 'General'}\nQuote: "${citation.highlight_text.slice(0, 100)}..."`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.2rem',
        padding: '0.1rem 0.45rem',
        margin: '0 0.2rem',
        borderRadius: '6px',
        fontSize: '0.78rem',
        fontWeight: 700,
        cursor: 'pointer',
        border: isActive
          ? '1px solid #38bdf8'
          : '1px solid rgba(56, 189, 248, 0.4)',
        background: isActive
          ? 'rgba(56, 189, 248, 0.3)'
          : 'rgba(56, 189, 248, 0.12)',
        color: '#38bdf8',
        boxShadow: isActive ? '0 0 10px rgba(56, 189, 248, 0.5)' : 'none',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        verticalAlign: 'baseline',
      }}
    >
      <span>[{citation.citation_index}]</span>
      <ExternalLink size={10} style={{ opacity: 0.8 }} />
    </button>
  );
};
