import React, { useState, useEffect } from 'react';
import type { Quiz, FlashcardSet, Citation } from '../../types';
import { StudyService } from '../../services/api';
import { QuizView } from './QuizView';
import { FlashcardView } from './FlashcardView';
import { StudyStatsView } from './StudyStatsView';
import {
  GraduationCap,
  Layers,
  BarChart3,
  Sparkles,
  Loader2,
} from 'lucide-react';

interface StudyModeViewProps {
  onSelectCitation?: (citation: Citation) => void;
}

export const StudyModeView: React.FC<StudyModeViewProps> = ({ onSelectCitation }) => {
  const [activeTab, setActiveTab] = useState<'quizzes' | 'flashcards' | 'stats'>('quizzes');
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [flashcardSets, setFlashcardSets] = useState<FlashcardSet[]>([]);
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null);
  const [activeDeck, setActiveDeck] = useState<FlashcardSet | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [qList, fList] = await Promise.all([
        StudyService.getQuizzes(),
        StudyService.getFlashcardSets(),
      ]);
      setQuizzes(qList);
      if (qList.length > 0) setActiveQuiz(qList[0]);

      setFlashcardSets(fList);
      if (fList.length > 0) setActiveDeck(fList[0]);
    } catch (err) {
      console.error('Failed to load study data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuiz = async () => {
    setIsGenerating(true);
    try {
      const newQuiz = await StudyService.generateQuiz({
        topic: 'Atrial Fibrillation Guidelines',
        difficulty: 'MEDIUM',
        count: 5,
      });
      setQuizzes((prev) => [newQuiz, ...prev]);
      setActiveQuiz(newQuiz);
      setActiveTab('quizzes');
    } catch (err) {
      console.error('Failed to generate quiz:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    setIsGenerating(true);
    try {
      const newDeck = await StudyService.generateFlashcards({
        topic: 'Cardiology Pharmacotherapy',
        count: 6,
      });
      setFlashcardSets((prev) => [newDeck, ...prev]);
      setActiveDeck(newDeck);
      setActiveTab('flashcards');
    } catch (err) {
      console.error('Failed to generate flashcards:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          background: '#090d16',
          color: '#38bdf8',
          fontSize: '0.85rem',
          gap: '0.5rem',
        }}
      >
        <Loader2 size={18} className="animate-spin" />
        <span>Loading Medical Study Center...</span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#090d16',
        overflow: 'hidden',
      }}
    >
      {/* Study Navigation Bar */}
      <div
        style={{
          padding: '0.5rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(15, 23, 42, 0.7)',
        }}
      >
        {/* Sub-tab pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <button
            onClick={() => setActiveTab('quizzes')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              border: 'none',
              background: activeTab === 'quizzes' ? '#0284c7' : 'transparent',
              color: activeTab === 'quizzes' ? '#ffffff' : 'var(--text-muted)',
              fontSize: '0.76rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <GraduationCap size={14} />
            Guideline Quizzes
          </button>

          <button
            onClick={() => setActiveTab('flashcards')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              border: 'none',
              background: activeTab === 'flashcards' ? '#0284c7' : 'transparent',
              color: activeTab === 'flashcards' ? '#ffffff' : 'var(--text-muted)',
              fontSize: '0.76rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <Layers size={14} />
            Flashcard SRS
          </button>

          <button
            onClick={() => setActiveTab('stats')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              border: 'none',
              background: activeTab === 'stats' ? '#0284c7' : 'transparent',
              color: activeTab === 'stats' ? '#ffffff' : 'var(--text-muted)',
              fontSize: '0.76rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <BarChart3 size={14} />
            Analytics
          </button>
        </div>

        {/* Generate & Select Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {activeTab === 'quizzes' && (
            <>
              {quizzes.length > 0 && (
                <select
                  value={activeQuiz?.id || ''}
                  onChange={(e) => {
                    const found = quizzes.find((q) => q.id === e.target.value);
                    if (found) setActiveQuiz(found);
                  }}
                  style={{
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid var(--border-subtle)',
                    color: '#e2e8f0',
                    fontSize: '0.72rem',
                    borderRadius: '6px',
                    padding: '0.3rem 0.5rem',
                    outline: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {quizzes.map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.title.length > 30 ? `${q.title.slice(0, 30)}...` : q.title}
                    </option>
                  ))}
                </select>
              )}

              <button
                onClick={handleGenerateQuiz}
                disabled={isGenerating}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  color: '#38bdf8',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                }}
              >
                {isGenerating ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                Generate Quiz
              </button>
            </>
          )}

          {activeTab === 'flashcards' && (
            <>
              {flashcardSets.length > 0 && (
                <select
                  value={activeDeck?.id || ''}
                  onChange={(e) => {
                    const found = flashcardSets.find((d) => d.id === e.target.value);
                    if (found) setActiveDeck(found);
                  }}
                  style={{
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid var(--border-subtle)',
                    color: '#e2e8f0',
                    fontSize: '0.72rem',
                    borderRadius: '6px',
                    padding: '0.3rem 0.5rem',
                    outline: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {flashcardSets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title.length > 30 ? `${d.title.slice(0, 30)}...` : d.title}
                    </option>
                  ))}
                </select>
              )}

              <button
                onClick={handleGenerateFlashcards}
                disabled={isGenerating}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#34d399',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                }}
              >
                {isGenerating ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                Generate Deck
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Tab Body */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {activeTab === 'quizzes' && (
          <QuizView
            quiz={activeQuiz || StudyService.getDemoQuiz()}
            onSelectCitation={onSelectCitation}
            onRegenerateQuiz={handleGenerateQuiz}
          />
        )}

        {activeTab === 'flashcards' && (
          <FlashcardView
            deck={activeDeck || StudyService.getDemoFlashcards()}
            onSelectCitation={onSelectCitation}
            onRegenerateDeck={handleGenerateFlashcards}
          />
        )}

        {activeTab === 'stats' && <StudyStatsView />}
      </div>
    </div>
  );
};
