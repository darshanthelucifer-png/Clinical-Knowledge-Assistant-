import React, { useState, useEffect } from 'react';
import type { StudyStats } from '../../types';
import { StudyService } from '../../services/api';
import {
  Award,
  Clock,
  TrendingUp,
  RefreshCw,
  Layers,
  GraduationCap,
} from 'lucide-react';

export const StudyStatsView: React.FC = () => {
  const [stats, setStats] = useState<StudyStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await StudyService.getStudyStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load study stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const activeStats = stats || StudyService.getDemoStats();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#090d16',
        padding: '1.5rem',
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
          paddingBottom: '0.75rem',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Medical Student Study Analytics
          </h2>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Real-time mastery tracking across guidelines, quizzes, and spaced-repetition decks
          </span>
        </div>

        <button
          onClick={fetchStats}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.35rem 0.65rem',
            borderRadius: '6px',
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontSize: '0.72rem',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Top 4 Stat Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '0.85rem',
          marginBottom: '1.5rem',
        }}
      >
        {/* Card 1: Quizzes Completed */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8', marginBottom: '0.5rem' }}>
            <Award size={16} />
            <span style={{ fontSize: '0.72rem', fontWeight: 600 }}>Quizzes Finished</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc' }}>
            {activeStats.total_quizzes_completed}
          </div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
            Guideline board reviews
          </span>
        </div>

        {/* Card 2: Average Score */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981', marginBottom: '0.5rem' }}>
            <TrendingUp size={16} />
            <span style={{ fontSize: '0.72rem', fontWeight: 600 }}>Average Score</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399' }}>
            {activeStats.average_quiz_score}%
          </div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
            Target: ≥ 70% passing
          </span>
        </div>

        {/* Card 3: Cards Reviewed */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#a855f7', marginBottom: '0.5rem' }}>
            <Layers size={16} />
            <span style={{ fontSize: '0.72rem', fontWeight: 600 }}>Cards Mastered</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc' }}>
            {activeStats.total_flashcards_reviewed}
          </div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
            SM-2 Spaced Repetition
          </span>
        </div>

        {/* Card 4: Study Time */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#f59e0b', marginBottom: '0.5rem' }}>
            <Clock size={16} />
            <span style={{ fontSize: '0.72rem', fontWeight: 600 }}>Study Time</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc' }}>
            {activeStats.total_study_time_minutes}m
          </div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
            Active retention focus
          </span>
        </div>
      </div>

      {/* Topic Accuracy Breakdown */}
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '1.25rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '1rem' }}>
          <GraduationCap size={16} color="#38bdf8" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Guideline Topic Mastery & Retention
          </h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {activeStats.topics.map((t, idx) => {
            let color = '#34d399';
            if (t.accuracy < 70) color = '#f87171';
            else if (t.accuracy < 85) color = '#fbbf24';

            return (
              <div key={idx}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.76rem',
                    marginBottom: '0.35rem',
                  }}
                >
                  <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{t.topic}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                      {t.total_questions} questions
                    </span>
                    <span style={{ fontWeight: 700, color }}>{t.accuracy}%</span>
                  </div>
                </div>

                <div
                  style={{
                    height: '7px',
                    background: 'rgba(30, 41, 59, 0.6)',
                    borderRadius: '9999px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${t.accuracy}%`,
                      height: '100%',
                      background: color,
                      borderRadius: '9999px',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
