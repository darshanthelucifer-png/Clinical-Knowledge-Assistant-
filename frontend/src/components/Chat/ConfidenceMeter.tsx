import React from 'react';
import { ShieldCheck, AlertTriangle, XCircle } from 'lucide-react';

interface ConfidenceMeterProps {
  score?: number;
  isNotFound?: boolean;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  score = 0,
  isNotFound = false,
}) => {
  if (isNotFound) {
    return (
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.25rem 0.65rem',
          borderRadius: '9999px',
          background: 'rgba(239, 68, 68, 0.15)',
          color: '#f87171',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          fontSize: '0.75rem',
          fontWeight: 600,
        }}
      >
        <XCircle size={14} />
        <span>Confidence Gate Refusal (Out of Guidelines)</span>
      </div>
    );
  }

  const percent = Math.min(100, Math.round(score * 100));

  let color = '#10b981'; // Green
  let label = 'High Evidence Grounding';
  let Icon = ShieldCheck;

  if (percent < 50) {
    color = '#f43f5e'; // Red
    label = 'Low Confidence';
    Icon = AlertTriangle;
  } else if (percent < 75) {
    color = '#f59e0b'; // Amber
    label = 'Moderate Evidence Grounding';
    Icon = ShieldCheck;
  }

  return (
    <div
      title={`Aggregated Rerank/Faithfulness Score: ${(score).toFixed(2)} (${percent}%)`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.2rem 0.65rem',
        borderRadius: '9999px',
        background: 'rgba(15, 23, 42, 0.7)',
        border: `1px solid ${color}40`,
        fontSize: '0.73rem',
        color: '#f8fafc',
      }}
    >
      <Icon size={14} color={color} />
      <span style={{ color, fontWeight: 600 }}>{percent}%</span>
      <span style={{ color: 'var(--text-muted)' }}>•</span>
      <span style={{ color: 'var(--text-secondary)' }}>{label}</span>

      {/* Mini Bar */}
      <div
        style={{
          width: '42px',
          height: '5px',
          borderRadius: '3px',
          background: 'rgba(255, 255, 255, 0.1)',
          overflow: 'hidden',
          marginLeft: '0.2rem',
        }}
      >
        <div
          style={{
            width: `${percent}%`,
            height: '100%',
            background: color,
            transition: 'width 0.5s ease-out',
          }}
        />
      </div>
    </div>
  );
};
