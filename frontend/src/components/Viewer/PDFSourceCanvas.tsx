import React, { useState } from 'react';
import type { Citation } from '../../types';
import {
  FileText,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import {
  GUIDELINE_PAGE_DATA,
  detectGuidelineDomain,
} from './guidelinePageData';

interface PDFSourceCanvasProps {
  activeCitation?: Citation | null;
  documentTitle?: string;
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export const PDFSourceCanvas: React.FC<PDFSourceCanvasProps> = ({
  activeCitation,
  documentTitle = '2026 AHA/ACC/HRS Guideline for the Management of Atrial Fibrillation',
  currentPage: propPage,
  totalPages: propTotalPages,
  onPageChange,
}) => {
  const [internalPage, setInternalPage] = useState<number>(1);
  const [zoom, setZoom] = useState<number>(100);

  // Auto-detect domain
  const effectiveTitle = activeCitation?.source_title || documentTitle;
  const domain = detectGuidelineDomain(effectiveTitle);
  const guideline = GUIDELINE_PAGE_DATA[domain] || GUIDELINE_PAGE_DATA.afib;

  const totalPages = propTotalPages || guideline.totalPages || 4;
  const displayPage = activeCitation?.page_number || propPage || internalPage;

  const handlePageChange = (newPage: number) => {
    setInternalPage(newPage);
    if (onPageChange) onPageChange(newPage);
  };

  const handlePrev = () => {
    if (displayPage > 1) handlePageChange(displayPage - 1);
  };

  const handleNext = () => {
    if (displayPage < totalPages) handlePageChange(displayPage + 1);
  };

  const pageData = guideline.pages[displayPage] || guideline.pages[1];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#090d16',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Viewer Header / Toolbar */}
      <div
        style={{
          padding: '0.65rem 1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(15, 23, 42, 0.75)',
          fontSize: '0.78rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden' }}>
          <FileText size={16} color="#38bdf8" />
          <span
            style={{
              fontWeight: 600,
              color: 'var(--text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: '240px',
            }}
            title={effectiveTitle}
          >
            {guideline.shortTitle || effectiveTitle}
          </span>
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              padding: '0.12rem 0.45rem',
              borderRadius: '9999px',
              background: 'rgba(2, 132, 199, 0.2)',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.3)',
            }}
          >
            {guideline.specialty}
          </span>
        </div>

        {/* Page & Zoom Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {/* Page Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <button
              onClick={handlePrev}
              disabled={displayPage <= 1}
              title="Previous Page"
              style={{
                background: 'transparent',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                color: displayPage <= 1 ? 'var(--text-muted)' : 'var(--text-secondary)',
                padding: '0.2rem',
                cursor: displayPage <= 1 ? 'not-allowed' : 'pointer',
              }}
            >
              <ChevronLeft size={14} />
            </button>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', padding: '0 0.3rem', fontWeight: 600 }}>
              p. {displayPage} / {totalPages}
            </span>
            <button
              onClick={handleNext}
              disabled={displayPage >= totalPages}
              title="Next Page"
              style={{
                background: 'transparent',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                color: displayPage >= totalPages ? 'var(--text-muted)' : 'var(--text-secondary)',
                padding: '0.2rem',
                cursor: displayPage >= totalPages ? 'not-allowed' : 'pointer',
              }}
            >
              <ChevronRight size={14} />
            </button>
          </div>

          <div style={{ width: '1px', height: '14px', background: 'var(--border-subtle)' }} />

          {/* Zoom Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <button
              onClick={() => setZoom(Math.max(75, zoom - 15))}
              title="Zoom Out"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <ZoomOut size={14} />
            </button>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{zoom}%</span>
            <button
              onClick={() => setZoom(Math.min(150, zoom + 15))}
              title="Zoom In"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <ZoomIn size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Paper Representation */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'auto',
          padding: '1.5rem',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          background: 'rgba(0, 0, 0, 0.45)',
        }}
      >
        <div
          style={{
            width: `${Math.round(580 * (zoom / 100))}px`,
            minHeight: `${Math.round(780 * (zoom / 100))}px`,
            background: '#ffffff',
            color: '#1e293b',
            padding: '2.2rem',
            borderRadius: '4px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.7)',
            position: 'relative',
            fontSize: `${0.82 * (zoom / 100)}rem`,
            lineHeight: 1.5,
            fontFamily: 'serif',
          }}
        >
          {/* PDF Page Header */}
          <div
            style={{
              borderBottom: '1px solid #cbd5e1',
              paddingBottom: '0.4rem',
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.68rem',
              color: '#64748b',
              fontFamily: 'sans-serif',
            }}
          >
            <span>{pageData.headerJournal}</span>
            <span style={{ fontWeight: 600, color: '#0369a1' }}>CLINICAL PRACTICE GUIDELINE</span>
          </div>

          <h3
            style={{
              fontSize: '0.96rem',
              fontWeight: 700,
              marginBottom: '0.75rem',
              color: '#0f172a',
              fontFamily: 'sans-serif',
              borderLeft: '3px solid #0284c7',
              paddingLeft: '0.5rem',
            }}
          >
            {activeCitation && activeCitation.section_title
              ? activeCitation.section_title
              : pageData.sectionTitle}
          </h3>

          {/* 2-Column Standard A4 Layout */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            {/* Column 1 */}
            <div>
              {pageData.col1Paragraphs.map((para, idx) => (
                <p key={idx} style={{ marginBottom: '0.75rem', textAlign: 'justify' }}>
                  {para}
                </p>
              ))}

              {/* Cited Passage Highlight Envelope if active */}
              {activeCitation && (
                <div
                  className="citation-highlight-active"
                  style={{
                    padding: '0.55rem',
                    borderRadius: '4px',
                    background: 'rgba(250, 204, 21, 0.25)',
                    border: '1.5px dashed #ca8a04',
                    marginBottom: '0.75rem',
                    position: 'relative',
                    boxShadow: '0 0 15px rgba(250, 204, 21, 0.3)',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      top: '-9px',
                      left: '8px',
                      background: '#ca8a04',
                      color: '#ffffff',
                      fontSize: '0.62rem',
                      fontWeight: 700,
                      padding: '0.05rem 0.4rem',
                      borderRadius: '3px',
                      fontFamily: 'sans-serif',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.2rem',
                    }}
                  >
                    <ShieldCheck size={10} />
                    CITED PASSAGE [{activeCitation.citation_index}] (p. {activeCitation.page_number})
                  </div>
                  <p
                    style={{
                      fontWeight: 600,
                      color: '#713f12',
                      marginTop: '4px',
                      lineHeight: 1.45,
                    }}
                  >
                    "{activeCitation.highlight_text}"
                  </p>
                </div>
              )}
            </div>

            {/* Column 2 */}
            <div>
              {pageData.col2Paragraphs.map((para, idx) => (
                <p key={idx} style={{ marginBottom: '0.75rem', textAlign: 'justify', whiteSpace: 'pre-line' }}>
                  {para}
                </p>
              ))}

              {/* Optional Table */}
              {pageData.table && (
                <div
                  style={{
                    border: '1px solid #94a3b8',
                    borderRadius: '4px',
                    padding: '0.55rem',
                    background: '#f8fafc',
                    marginBottom: '0.75rem',
                  }}
                >
                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: '0.7rem',
                      marginBottom: '0.35rem',
                      color: '#0f172a',
                      fontFamily: 'sans-serif',
                      borderBottom: '1px solid #cbd5e1',
                      paddingBottom: '0.2rem',
                    }}
                  >
                    {pageData.table.title}
                  </div>
                  <div style={{ fontSize: '0.66rem', color: '#334155', fontFamily: 'sans-serif' }}>
                    {pageData.table.rows.map((r, i) => (
                      <div
                        key={i}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          padding: '0.15rem 0',
                          borderBottom: i < pageData.table!.rows.length - 1 ? '1px dotted #e2e8f0' : 'none',
                        }}
                      >
                        <span style={{ fontWeight: 600, color: '#1e293b' }}>{r.label}:</span>
                        <span style={{ color: '#475569', textAlign: 'right', marginLeft: '0.5rem' }}>{r.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Page Footer */}
          <div
            style={{
              position: 'absolute',
              bottom: '1rem',
              left: '2.2rem',
              right: '2.2rem',
              display: 'flex',
              justifyContent: 'space-between',
              borderTop: '1px solid #e2e8f0',
              paddingTop: '0.4rem',
              fontSize: '0.68rem',
              color: '#94a3b8',
              fontFamily: 'sans-serif',
            }}
          >
            <span>{guideline.shortTitle}</span>
            <span>Evidence Grade: Class I, Level A</span>
            <span>Page {displayPage} of {totalPages}</span>
          </div>
        </div>
      </div>

      {/* Active Citation Quote Drawer */}
      {activeCitation && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: 'rgba(15, 23, 42, 0.95)',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.65rem',
          }}
        >
          <div
            style={{
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: '6px',
              flexShrink: 0,
            }}
          >
            [{activeCitation.citation_index}]
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {activeCitation.source_title}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>•</span>
              <span style={{ color: '#38bdf8' }}>Page {activeCitation.page_number}</span>
              {activeCitation.section_title && (
                <>
                  <span style={{ color: 'var(--text-muted)' }}>•</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{activeCitation.section_title}</span>
                </>
              )}
            </div>
            <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: 1.4 }}>
              "{activeCitation.highlight_text}"
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
