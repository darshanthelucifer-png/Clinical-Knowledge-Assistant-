import React from 'react';
import {
  Activity,
  ShieldCheck,
  GraduationCap,
  Stethoscope,
  Download,
  BookOpen,
  FileText,
  BrainCircuit,
} from 'lucide-react';
import type { UserRole, AppMode } from '../types';

interface HeaderProps {
  role: UserRole;
  onRoleChange: (newRole: UserRole) => void;
  activeMode: AppMode;
  onModeChange: (mode: AppMode) => void;
  onExportMarkdown: () => void;
  username: string;
}

export const Header: React.FC<HeaderProps> = ({
  role,
  onRoleChange,
  activeMode,
  onModeChange,
  onExportMarkdown,
  username,
}) => {
  return (
    <header className="glass-panel" style={{ padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', zIndex: 30 }}>
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, #0284c7, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(2, 132, 199, 0.4)' }}>
          <Activity size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #f8fafc, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              ClinSaarthi AI
            </h1>
            <span style={{ fontSize: '0.65rem', padding: '0.15rem 0.45rem', borderRadius: '9999px', background: 'rgba(6, 182, 212, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', fontWeight: 600 }}>
              v1.0 • RAG & Agentic
            </span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Clinical Knowledge Assistant with Spatial Citations & Multi-Node Fact Verification
          </p>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.6)', padding: '0.25rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', gap: '0.25rem' }}>
        <button
          onClick={() => onModeChange('guideline_qa')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.85rem',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: 'pointer',
            background: activeMode === 'guideline_qa' ? '#0284c7' : 'transparent',
            color: activeMode === 'guideline_qa' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          <BookOpen size={15} />
          Guideline Q&A
        </button>
        <button
          onClick={() => onModeChange('clinical_note_qa')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.85rem',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: 'pointer',
            background: activeMode === 'clinical_note_qa' ? '#0284c7' : 'transparent',
            color: activeMode === 'clinical_note_qa' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          <FileText size={15} />
          Clinical Notes & PII
        </button>
        <button
          onClick={() => onModeChange('study_mode')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.85rem',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: 'pointer',
            background: activeMode === 'study_mode' ? '#0284c7' : 'transparent',
            color: activeMode === 'study_mode' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          <BrainCircuit size={15} />
          Study Mode
        </button>
      </div>

      {/* Role Switcher & Export Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Role Selector Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'var(--bg-input)', padding: '0.35rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          {role === 'clinician' && <Stethoscope size={16} color="#38bdf8" />}
          {role === 'student' && <GraduationCap size={16} color="#10b981" />}
          {role === 'admin' && <ShieldCheck size={16} color="#f59e0b" />}
          <select
            value={role}
            onChange={(e) => onRoleChange(e.target.value as UserRole)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="clinician" style={{ background: '#111827' }}>Role: Clinician (Doctor)</option>
            <option value="student" style={{ background: '#111827' }}>Role: Student (Resident)</option>
            <option value="admin" style={{ background: '#111827' }}>Role: Admin (Compliance)</option>
          </select>
        </div>

        {/* User Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#1e293b', border: '1px solid #38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, color: '#38bdf8' }}>
            {username.slice(0, 2).toUpperCase()}
          </div>
          <span style={{ display: 'none', color: 'var(--text-secondary)' }}>{username}</span>
        </div>

        {/* Export Markdown */}
        <button
          onClick={onExportMarkdown}
          title="Export current consultation as Markdown report with citations & disclaimer"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.45rem 0.85rem',
            borderRadius: '8px',
            background: 'rgba(56, 189, 248, 0.1)',
            color: '#38bdf8',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Download size={14} />
          Export
        </button>
      </div>
    </header>
  );
};
