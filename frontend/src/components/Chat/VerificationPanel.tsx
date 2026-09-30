import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  AlertOctagon,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Shield,
} from 'lucide-react';
import type { VerificationResult } from '../../types';

interface VerificationPanelProps {
  verifications: VerificationResult[];
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({ verifications }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!verifications || verifications.length === 0) {
    return null;
  }

  const conflictCount = verifications.filter((v) => v.status === 'CONFLICT').length;
  const verifiedCount = verifications.filter((v) => v.status === 'VERIFIED').length;
  const unsupportedCount = verifications.filter((v) => v.status === 'UNSUPPORTED').length;

  return (
    <div
      style={{
        marginTop: '0.85rem',
        borderRadius: '10px',
        border: conflictCount > 0 ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid var(--border-subtle)',
        background: 'rgba(15, 23, 42, 0.55)',
        overflow: 'hidden',
      }}
    >
      {/* Header Bar */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          padding: '0.65rem 0.95rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: conflictCount > 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(30, 41, 59, 0.5)',
          border: 'none',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          fontSize: '0.8rem',
          fontWeight: 600,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {conflictCount > 0 ? (
            <ShieldAlert size={16} color="#ef4444" />
          ) : (
            <Shield size={16} color="#10b981" />
          )}
          <span>Pharmaceutical Verification Audit Trail</span>
          <div style={{ display: 'flex', gap: '0.35rem', marginLeft: '0.5rem' }}>
            {verifiedCount > 0 && (
              <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '0.1rem 0.45rem', borderRadius: '4px', fontSize: '0.7rem' }}>
                {verifiedCount} Verified
              </span>
            )}
            {conflictCount > 0 && (
              <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', padding: '0.1rem 0.45rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700 }}>
                {conflictCount} Conflict!
              </span>
            )}
            {unsupportedCount > 0 && (
              <span style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', padding: '0.1rem 0.45rem', borderRadius: '4px', fontSize: '0.7rem' }}>
                {unsupportedCount} Unsupported
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-muted)' }}>
          <span style={{ fontSize: '0.72rem' }}>{isOpen ? 'Collapse' : 'Inspect'}</span>
          {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {/* Expanded Table & Audit Trail */}
      {isOpen && (
        <div style={{ padding: '0.75rem', fontSize: '0.78rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.4rem' }}>
                <th style={{ padding: '0.4rem' }}>Medication</th>
                <th style={{ padding: '0.4rem' }}>Claimed Dosage</th>
                <th style={{ padding: '0.4rem' }}>Status</th>
                <th style={{ padding: '0.4rem' }}>RxNorm (NIH)</th>
                <th style={{ padding: '0.4rem' }}>openFDA</th>
                <th style={{ padding: '0.4rem' }}>Verification Rationale</th>
              </tr>
            </thead>
            <tbody>
              {verifications.map((v, i) => {
                const isConflict = v.status === 'CONFLICT';
                const isVerified = v.status === 'VERIFIED';

                let statusBadge = (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#fbbf24', fontWeight: 600 }}>
                    <HelpCircle size={13} /> Unsupported
                  </span>
                );

                if (isVerified) {
                  statusBadge = (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontWeight: 600 }}>
                      <CheckCircle2 size={13} /> Verified
                    </span>
                  );
                } else if (isConflict) {
                  statusBadge = (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#f87171', fontWeight: 700 }}>
                      <AlertOctagon size={13} /> Conflict
                    </span>
                  );
                }

                return (
                  <tr
                    key={i}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      background: isConflict ? 'rgba(239, 68, 68, 0.08)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '0.5rem 0.4rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {v.drug_name}
                    </td>
                    <td style={{ padding: '0.5rem 0.4rem', color: 'var(--text-secondary)' }}>
                      {v.dosage ? `${v.dosage} ${v.unit || 'mg'}` : 'Not specified'}
                      {v.frequency && <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>{v.frequency}</span>}
                    </td>
                    <td style={{ padding: '0.5rem 0.4rem' }}>{statusBadge}</td>
                    <td style={{ padding: '0.5rem 0.4rem' }}>
                      {v.rxnorm_cui ? (
                        <a
                          href={`https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm=${v.rxnorm_cui}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.2rem',
                            color: '#38bdf8',
                            textDecoration: 'none',
                            background: 'rgba(56, 189, 248, 0.1)',
                            padding: '0.1rem 0.35rem',
                            borderRadius: '4px',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.72rem',
                          }}
                        >
                          CUI:{v.rxnorm_cui}
                          <ExternalLink size={10} />
                        </a>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Standardized</span>
                      )}
                    </td>
                    <td style={{ padding: '0.5rem 0.4rem' }}>
                      {v.openfda_match ? (
                        <span style={{ color: '#10b981', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.72rem' }}>
                          <CheckCircle2 size={12} /> FDA Labeled
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Referenced</span>
                      )}
                    </td>
                    <td style={{ padding: '0.5rem 0.4rem', color: isConflict ? '#fca5a5' : 'var(--text-secondary)', fontSize: '0.72rem', maxWidth: '320px' }}>
                      {v.explanation}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
