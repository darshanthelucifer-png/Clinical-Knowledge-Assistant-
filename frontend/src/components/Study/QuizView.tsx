import React, { useState } from 'react';
import type { Quiz, QuizSubmissionResult, Citation } from '../../types';
import { StudyService } from '../../services/api';
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Award,
  Sparkles,
  Loader2,
} from 'lucide-react';

interface QuizViewProps {
  quiz: Quiz;
  onSelectCitation?: (citation: Citation) => void;
  onRegenerateQuiz?: () => void;
}

export const QuizView: React.FC<QuizViewProps> = ({
  quiz,
  onSelectCitation,
  onRegenerateQuiz,
}) => {
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionResult, setSubmissionResult] = useState<QuizSubmissionResult | null>(null);

  const questions = quiz.questions || [];
  const currentQ = questions[currentIdx];

  const handleSelectOption = (qId: string, optIdx: number) => {
    if (isSubmitted) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [qId]: optIdx,
    }));
  };

  const handleSubmitQuiz = async () => {
    setIsSubmitting(true);
    try {
      const res = await StudyService.submitQuiz(quiz.id, {
        answers: selectedAnswers,
        time_spent_seconds: 90,
      });
      setSubmissionResult(res);
      setIsSubmitted(true);
    } catch (err) {
      console.error('Quiz submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedAnswers({});
    setIsSubmitted(false);
    setSubmissionResult(null);
    setCurrentIdx(0);
  };

  const handleCitationClick = (ref: string, pageNum?: number) => {
    if (onSelectCitation) {
      onSelectCitation({
        citation_index: 1,
        inline_tag: '[Guideline]',
        source_title: quiz.title,
        page_number: pageNum || 1,
        section_title: ref,
        highlight_text: currentQ?.explanation || '',
      });
    }
  };

  if (!currentQ) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No questions available for this quiz.
      </div>
    );
  }

  const answeredCount = Object.keys(selectedAnswers).length;
  const progressPercent = Math.round(((currentIdx + 1) / questions.length) * 100);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#090d16',
        overflowY: 'auto',
        padding: '1.5rem',
      }}
    >
      {/* Quiz Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
          paddingBottom: '0.75rem',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            {quiz.title}
          </h2>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Topic: <span style={{ color: '#38bdf8' }}>{quiz.topic || 'Cardiology'}</span> • Difficulty:{' '}
            <span style={{ color: '#f59e0b', fontWeight: 600 }}>{quiz.difficulty}</span>
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {onRegenerateQuiz && (
            <button
              onClick={onRegenerateQuiz}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.35rem 0.65rem',
                borderRadius: '6px',
                background: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
                fontSize: '0.72rem',
                cursor: 'pointer',
              }}
            >
              <Sparkles size={13} />
              New Quiz
            </button>
          )}

          <button
            onClick={handleReset}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.65rem',
              borderRadius: '6px',
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              fontSize: '0.72rem',
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={13} />
            Reset
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            marginBottom: '0.35rem',
          }}
        >
          <span>
            Question {currentIdx + 1} of {questions.length}
          </span>
          <span>{answeredCount} Answered</span>
        </div>
        <div
          style={{
            height: '6px',
            background: 'rgba(30, 41, 59, 0.6)',
            borderRadius: '9999px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progressPercent}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #0284c7, #38bdf8)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Main Question Card */}
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '1.25rem',
          marginBottom: '1rem',
          backdropFilter: 'blur(8px)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.65rem',
            marginBottom: '1.25rem',
          }}
        >
          <div
            style={{
              padding: '0.2rem 0.5rem',
              borderRadius: '6px',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              fontSize: '0.75rem',
              fontWeight: 700,
              marginTop: '0.1rem',
            }}
          >
            Q{currentIdx + 1}
          </div>
          <p
            style={{
              fontSize: '0.88rem',
              color: '#f1f5f9',
              lineHeight: 1.6,
              margin: 0,
              fontWeight: 500,
            }}
          >
            {currentQ.question_text}
          </p>
        </div>

        {/* Options List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {currentQ.options.map((optText, optIdx) => {
            const isSelected = selectedAnswers[currentQ.id] === optIdx;
            const isCorrect = currentQ.correct_option_index === optIdx;

            let borderColor = 'var(--border-subtle)';
            let bgColor = 'rgba(30, 41, 59, 0.4)';
            let textColor = '#e2e8f0';

            if (isSubmitted) {
              if (isCorrect) {
                borderColor = 'rgba(16, 185, 129, 0.6)';
                bgColor = 'rgba(16, 185, 129, 0.15)';
                textColor = '#34d399';
              } else if (isSelected) {
                borderColor = 'rgba(239, 68, 68, 0.6)';
                bgColor = 'rgba(239, 68, 68, 0.15)';
                textColor = '#f87171';
              }
            } else if (isSelected) {
              borderColor = '#0284c7';
              bgColor = 'rgba(2, 132, 199, 0.2)';
              textColor = '#38bdf8';
            }

            const letter = String.fromCharCode(65 + optIdx);

            return (
              <button
                key={optIdx}
                onClick={() => handleSelectOption(currentQ.id, optIdx)}
                disabled={isSubmitted}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: bgColor,
                  border: `1px solid ${borderColor}`,
                  color: textColor,
                  fontSize: '0.82rem',
                  textAlign: 'left',
                  cursor: isSubmitted ? 'default' : 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <span
                  style={{
                    width: '22px',
                    height: '22px',
                    borderRadius: '50%',
                    background: isSelected ? '#0284c7' : 'rgba(255, 255, 255, 0.08)',
                    color: isSelected ? '#ffffff' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                  }}
                >
                  {letter}
                </span>

                <span style={{ flex: 1 }}>{optText}</span>

                {isSubmitted && isCorrect && <CheckCircle2 size={16} color="#10b981" />}
                {isSubmitted && isSelected && !isCorrect && <XCircle size={16} color="#ef4444" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Post-Submission Grounded Explanation Card */}
      {isSubmitted && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '10px',
            padding: '1rem',
            marginBottom: '1rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38bdf8', fontSize: '0.76rem', fontWeight: 600 }}>
              <HelpCircle size={14} />
              Guideline-Grounded Rationale
            </div>

            <button
              onClick={() => handleCitationClick(currentQ.source_reference, currentQ.page_number)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                padding: '0.2rem 0.55rem',
                borderRadius: '6px',
                background: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                color: '#38bdf8',
                fontSize: '0.7rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <BookOpen size={12} />
              {currentQ.source_reference} (P. {currentQ.page_number || 1})
            </button>
          </div>

          <p style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.6, margin: 0 }}>
            {currentQ.explanation}
          </p>
        </div>
      )}

      {/* Bottom Navigation & Submit Bar */}
      <div
        style={{
          marginTop: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: '0.75rem',
        }}
      >
        <button
          onClick={() => setCurrentIdx((p) => Math.max(0, p - 1))}
          disabled={currentIdx === 0}
          style={{
            padding: '0.45rem 0.85rem',
            borderRadius: '6px',
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: currentIdx === 0 ? 'rgba(255,255,255,0.2)' : 'var(--text-secondary)',
            fontSize: '0.76rem',
            cursor: currentIdx === 0 ? 'not-allowed' : 'pointer',
          }}
        >
          Previous
        </button>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {currentIdx < questions.length - 1 ? (
            <button
              onClick={() => setCurrentIdx((p) => Math.min(questions.length - 1, p + 1))}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.45rem 1rem',
                borderRadius: '6px',
                background: '#0284c7',
                border: 'none',
                color: '#ffffff',
                fontSize: '0.76rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Next <ArrowRight size={13} />
            </button>
          ) : !isSubmitted ? (
            <button
              onClick={handleSubmitQuiz}
              disabled={isSubmitting || answeredCount === 0}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.45rem 1.1rem',
                borderRadius: '6px',
                background: answeredCount === 0 ? 'rgba(16, 185, 129, 0.2)' : '#10b981',
                border: 'none',
                color: '#ffffff',
                fontSize: '0.76rem',
                fontWeight: 600,
                cursor: answeredCount === 0 || isSubmitting ? 'not-allowed' : 'pointer',
                boxShadow: answeredCount > 0 ? '0 0 12px rgba(16, 185, 129, 0.4)' : 'none',
              }}
            >
              {isSubmitting ? <Loader2 size={13} className="animate-spin" /> : <Award size={13} />}
              Submit & Grade Quiz
            </button>
          ) : null}
        </div>
      </div>

      {/* Final Score Modal / Banner if Submitted */}
      {isSubmitted && submissionResult && (
        <div
          style={{
            marginTop: '1.25rem',
            padding: '1.25rem',
            borderRadius: '10px',
            background:
              submissionResult.passed
                ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 78, 59, 0.3))'
                : 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(127, 29, 29, 0.3))',
            border: `1px solid ${submissionResult.passed ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <Award size={20} color={submissionResult.passed ? '#10b981' : '#ef4444'} />
              <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                {submissionResult.passed ? 'Clinical Mastery Passed!' : 'Review Recommended'}
              </span>
            </div>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', margin: 0 }}>
              You answered {submissionResult.correct_answers} of {submissionResult.total_questions} questions correctly.
            </p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '1.75rem', fontWeight: 800, color: submissionResult.passed ? '#34d399' : '#f87171' }}>
              {submissionResult.score_percentage}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
