import React, { useState } from 'react';
import type { FlashcardSet, Citation } from '../../types';
import { StudyService } from '../../services/api';
import {
  RotateCcw,
  Sparkles,
  BookOpen,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Calendar,
  Layers,
} from 'lucide-react';

interface FlashcardViewProps {
  deck: FlashcardSet;
  onSelectCitation?: (citation: Citation) => void;
  onRegenerateDeck?: () => void;
}

export const FlashcardView: React.FC<FlashcardViewProps> = ({
  deck,
  onSelectCitation,
  onRegenerateDeck,
}) => {
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [reviewedCards, setReviewedCards] = useState<Record<string, string>>({});
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  const cards = deck.cards || [];
  const currentCard = cards[currentIdx];

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleRateSRS = async (rating: 'again' | 'hard' | 'good' | 'easy') => {
    if (!currentCard) return;

    try {
      await StudyService.reviewFlashcard(currentCard.id, rating);
    } catch (err) {
      console.error('Failed to apply SRS rating:', err);
    }

    setReviewedCards((prev) => ({
      ...prev,
      [currentCard.id]: rating,
    }));

    setIsFlipped(false);

    if (currentIdx < cards.length - 1) {
      setCurrentIdx((prev) => prev + 1);
    } else {
      setIsCompleted(true);
    }
  };

  const handleCitationClick = (ref: string, pageNum?: number) => {
    if (onSelectCitation && currentCard) {
      onSelectCitation({
        citation_index: 1,
        inline_tag: '[Card Citation]',
        source_title: deck.title,
        page_number: pageNum || 1,
        section_title: ref,
        highlight_text: currentCard.back,
      });
    }
  };

  const handleRestart = () => {
    setCurrentIdx(0);
    setIsFlipped(false);
    setIsCompleted(false);
  };

  if (!currentCard) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No flashcards available in this deck.
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
        padding: '1.5rem',
        overflowY: 'auto',
      }}
    >
      {/* Header Bar */}
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
            {deck.title}
          </h2>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            SuperMemo SM-2 Spaced Repetition • {cards.length} High-Yield Clinical Cards
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {onRegenerateDeck && (
            <button
              onClick={onRegenerateDeck}
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
              New Deck
            </button>
          )}

          <button
            onClick={handleRestart}
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
            Restart
          </button>
        </div>
      </div>

      {/* Progress & Deck Status */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.74rem',
          color: 'var(--text-muted)',
          marginBottom: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Layers size={14} color="#38bdf8" />
          <span>
            Card {currentIdx + 1} of {cards.length} ({Object.keys(reviewedCards).length} rated)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Calendar size={13} />
          <span>Next Interval: {currentCard.interval_days || 1} day(s)</span>
        </div>
      </div>

      {/* Interactive 3D Flip Card Container */}
      {!isCompleted ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '340px' }}>
          <div
            onClick={handleFlip}
            style={{
              flex: 1,
              perspective: '1000px',
              cursor: 'pointer',
              minHeight: '280px',
              position: 'relative',
              borderRadius: '16px',
              transition: 'all 0.4s ease',
            }}
          >
            <div
              style={{
                width: '100%',
                height: '100%',
                position: 'relative',
                transformStyle: 'preserve-3d',
                transform: isFlipped ? 'rotateY(180deg)' : 'none',
                transition: 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            >
              {/* Card Front */}
              <div
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  backfaceVisibility: 'hidden',
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.8))',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  borderRadius: '16px',
                  padding: '2rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                }}
              >
                <div>
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '9999px',
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      marginBottom: '1.25rem',
                    }}
                  >
                    <span>{currentCard.key_concept || 'Clinical Vignette'}</span>
                  </div>

                  <h3
                    style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      color: '#f8fafc',
                      lineHeight: 1.6,
                      margin: 0,
                    }}
                  >
                    {currentCard.front}
                  </h3>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.72rem',
                    color: 'var(--text-muted)',
                    borderTop: '1px solid var(--border-subtle)',
                    paddingTop: '0.75rem',
                  }}
                >
                  <span>Click anywhere to reveal guideline recommendation</span>
                  <span style={{ color: '#38bdf8' }}>Flip Card ➔</span>
                </div>
              </div>

              {/* Card Back */}
              <div
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  backfaceVisibility: 'hidden',
                  transform: 'rotateY(180deg)',
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(6, 78, 59, 0.25))',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  borderRadius: '16px',
                  padding: '2rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
                }}
              >
                <div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '1rem',
                    }}
                  >
                    <span
                      style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#34d399',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                      }}
                    >
                      Guideline Recommendation
                    </span>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCitationClick(currentCard.source_reference, currentCard.page_number);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '6px',
                        background: 'rgba(56, 189, 248, 0.15)',
                        border: '1px solid rgba(56, 189, 248, 0.3)',
                        color: '#38bdf8',
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      <BookOpen size={11} />
                      {currentCard.source_reference} (P. {currentCard.page_number || 1})
                    </button>
                  </div>

                  <p
                    style={{
                      fontSize: '0.92rem',
                      color: '#e2e8f0',
                      lineHeight: 1.65,
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {currentCard.back}
                  </p>
                </div>

                <div
                  style={{
                    fontSize: '0.72rem',
                    color: 'var(--text-muted)',
                    borderTop: '1px solid var(--border-subtle)',
                    paddingTop: '0.75rem',
                  }}
                >
                  Rate your recall difficulty below to update Spaced Repetition scheduling:
                </div>
              </div>
            </div>
          </div>

          {/* SuperMemo SM-2 Rating Controls */}
          {isFlipped ? (
            <div
              style={{
                marginTop: '1.25rem',
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '0.65rem',
              }}
            >
              <button
                onClick={() => handleRateSRS('again')}
                style={{
                  padding: '0.65rem 0.5rem',
                  borderRadius: '10px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#f87171',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                🔴 Again (&lt;1d)
              </button>

              <button
                onClick={() => handleRateSRS('hard')}
                style={{
                  padding: '0.65rem 0.5rem',
                  borderRadius: '10px',
                  background: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  color: '#fbbf24',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                🟠 Hard (2d)
              </button>

              <button
                onClick={() => handleRateSRS('good')}
                style={{
                  padding: '0.65rem 0.5rem',
                  borderRadius: '10px',
                  background: 'rgba(2, 132, 199, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  color: '#38bdf8',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                🔵 Good (4d)
              </button>

              <button
                onClick={() => handleRateSRS('easy')}
                style={{
                  padding: '0.65rem 0.5rem',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#34d399',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                🟢 Easy (7d)
              </button>
            </div>
          ) : (
            <div
              style={{
                marginTop: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <button
                onClick={() => setCurrentIdx((p) => Math.max(0, p - 1))}
                disabled={currentIdx === 0}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.45rem 0.85rem',
                  borderRadius: '8px',
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  color: currentIdx === 0 ? 'rgba(255,255,255,0.2)' : 'var(--text-secondary)',
                  fontSize: '0.74rem',
                  cursor: currentIdx === 0 ? 'not-allowed' : 'pointer',
                }}
              >
                <ArrowLeft size={13} /> Prev
              </button>

              <button
                onClick={handleFlip}
                style={{
                  padding: '0.5rem 1.25rem',
                  borderRadius: '8px',
                  background: '#0284c7',
                  border: 'none',
                  color: '#ffffff',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 0 12px rgba(2, 132, 199, 0.4)',
                }}
              >
                Reveal Answer (Space / Click)
              </button>

              <button
                onClick={() => setCurrentIdx((p) => Math.min(cards.length - 1, p + 1))}
                disabled={currentIdx === cards.length - 1}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.45rem 0.85rem',
                  borderRadius: '8px',
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  color: currentIdx === cards.length - 1 ? 'rgba(255,255,255,0.2)' : 'var(--text-secondary)',
                  fontSize: '0.74rem',
                  cursor: currentIdx === cards.length - 1 ? 'not-allowed' : 'pointer',
                }}
              >
                Next <ArrowRight size={13} />
              </button>
            </div>
          )}
        </div>
      ) : (
        /* Deck Completed Celebration Card */
        <div
          style={{
            margin: 'auto',
            textAlign: 'center',
            maxWidth: '420px',
            padding: '2.5rem 1.5rem',
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: '16px',
          }}
        >
          <div
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '20px',
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem auto',
            }}
          >
            <CheckCircle2 size={32} color="#10b981" />
          </div>

          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
            Deck Completed!
          </h2>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1.5rem' }}>
            You reviewed all {cards.length} clinical flashcards in this session. Spaced repetition intervals have
            been automatically calculated according to your recall ratings.
          </p>

          <button
            onClick={handleRestart}
            style={{
              padding: '0.6rem 1.25rem',
              borderRadius: '8px',
              background: '#0284c7',
              border: 'none',
              color: '#ffffff',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 0 12px rgba(2, 132, 199, 0.4)',
            }}
          >
            Review Deck Again
          </button>
        </div>
      )}
    </div>
  );
};
