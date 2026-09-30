import React, { useState } from 'react';
import type { Citation } from '../../types';
import {
  FileText,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface PDFSourceCanvasProps {
  activeCitation?: Citation | null;
  documentTitle?: string;
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export const PDFSourceCanvas: React.FC<PDFSourceCanvasProps> = ({
  activeCitation,
  documentTitle = 'ESC/AHA 2026 Atrial Fibrillation Guidelines',
  currentPage = 1,
  totalPages = 18,
  onPageChange,
}) => {
  const [zoom, setZoom] = useState<number>(100);

  const displayPage = activeCitation?.page_number || currentPage;

  const handlePrev = () => {
    if (displayPage > 1 && onPageChange) onPageChange(displayPage - 1);
  };

  const handleNext = () => {
    if (displayPage < totalPages && onPageChange) onPageChange(displayPage + 1);
  };

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
          background: 'rgba(15, 23, 42, 0.6)',
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
              maxWidth: '220px',
            }}
          >
            {activeCitation?.source_title || documentTitle}
          </span>
        </div>

        {/* Page & Zoom Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {/* Page Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <button
              onClick={handlePrev}
              disabled={displayPage <= 1}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                color: 'var(--text-secondary)',
                padding: '0.2rem',
                cursor: displayPage <= 1 ? 'not-allowed' : 'pointer',
              }}
            >
              <ChevronLeft size={14} />
            </button>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', padding: '0 0.2rem' }}>
              p. {displayPage} / {totalPages}
            </span>
            <button
              onClick={handleNext}
              disabled={displayPage >= totalPages}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                color: 'var(--text-secondary)',
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
          background: 'rgba(0, 0, 0, 0.4)',
        }}
      >
        <div
          style={{
            width: `${Math.round(560 * (zoom / 100))}px`,
            minHeight: `${Math.round(760 * (zoom / 100))}px`,
            background: '#ffffff',
            color: '#1e293b',
            padding: '2rem',
            borderRadius: '4px',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)',
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
              fontSize: '0.7rem',
              color: '#64748b',
              fontFamily: 'sans-serif',
            }}
          >
            <span>European Heart Journal (2026) 47, 1024-1068</span>
            <span>CLINICAL PRACTICE GUIDELINES</span>
          </div>

          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem', color: '#0f172a' }}>
            Section 4.2: Direct Oral Anticoagulant (DOAC) Dosing & Renal Function
          </h3>

          {/* 2-Column Mock Layout */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            {/* Column 1 */}
            <div>
              <p style={{ marginBottom: '0.8rem', textAlign: 'justify' }}>
                Oral anticoagulation is strongly recommended for stroke prevention in non-valvular atrial
                fibrillation with a CHA2DS2-VASc score ≥2 in men and ≥3 in women. Direct oral
                anticoagulants (DOACs)—including apixaban, dabigatran, edoxaban, and rivaroxaban—are
                preferred over vitamin K antagonists (warfarin).
              </p>

              {/* Cited Passage Highlight Envelope */}
              <div
                className={activeCitation ? 'citation-highlight-active' : ''}
                style={{
                  padding: '0.5rem',
                  borderRadius: '4px',
                  background: activeCitation ? 'rgba(250, 204, 21, 0.35)' : '#fef08a',
                  border: '1px dashed #ca8a04',
                  marginBottom: '0.8rem',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    top: '-8px',
                    left: '6px',
                    background: '#ca8a04',
                    color: '#ffffff',
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    padding: '0.05rem 0.35rem',
                    borderRadius: '3px',
                    fontFamily: 'sans-serif',
                  }}
                >
                  CITED PASSAGE [{activeCitation?.citation_index || 1}]
                </div>
                <p style={{ fontWeight: 600, color: '#854d0e', marginTop: '4px' }}>
                  {activeCitation?.highlight_text ||
                    'For non-valvular atrial fibrillation, Rivaroxaban 20 mg once daily with the evening meal is recommended for patients with normal renal function (CrCl ≥50 mL/min). In patients with moderate renal impairment (CrCl 15–49 mL/min), reduce dose to 15 mg once daily.'}
                </p>
              </div>

              <p style={{ textAlign: 'justify' }}>
                Routine coagulation monitoring is not required for DOACs. However, annual assessment
                of renal function (creatinine clearance via Cockcroft-Gault) and liver function is
                mandatory in all chronic patients.
              </p>
            </div>

            {/* Column 2 */}
            <div>
              <p style={{ marginBottom: '0.8rem', textAlign: 'justify' }}>
                Dabigatran is dosed at 150 mg twice daily, with a dose reduction to 110 mg twice daily in
                patients aged ≥80 years or those receiving concomitant verapamil. Apixaban is administered
                at 5 mg twice daily, with reduction to 2.5 mg twice daily if any two criteria are met: age
                ≥80 years, body weight ≤60 kg, or serum creatinine ≥1.5 mg/dL.
              </p>

              <div
                style={{
                  border: '1px solid #cbd5e1',
                  borderRadius: '4px',
                  padding: '0.45rem',
                  background: '#f8fafc',
                  marginBottom: '0.8rem',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '0.7rem', marginBottom: '0.2rem', color: '#0f172a' }}>
                  Table 4.1: Renal Dose Reductions
                </div>
                <div style={{ fontSize: '0.66rem', color: '#334155' }}>
                  • CrCl &gt;50 mL/min: Rivaroxaban 20 mg qd<br />
                  • CrCl 15-49 mL/min: Rivaroxaban 15 mg qd<br />
                  • CrCl &lt;15 mL/min: Not recommended
                </div>
              </div>

              <p style={{ textAlign: 'justify' }}>
                In patients with active serious bleeding, DOAC-specific reversal agents (idarucizumab for
                dabigatran, andexanet alfa for apixaban and rivaroxaban) should be initiated without delay.
              </p>
            </div>
          </div>

          {/* Page Footer */}
          <div
            style={{
              position: 'absolute',
              bottom: '1rem',
              left: '2rem',
              right: '2rem',
              display: 'flex',
              justifyContent: 'space-between',
              borderTop: '1px solid #e2e8f0',
              paddingTop: '0.4rem',
              fontSize: '0.68rem',
              color: '#94a3b8',
              fontFamily: 'sans-serif',
            }}
          >
            <span>ESC/AHA Guidelines 2026</span>
            <span>Page {displayPage}</span>
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
