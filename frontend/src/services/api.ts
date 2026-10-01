/**
 * ==============================================================================
 * ClinSaarthi AI - REST API Service Client
 * ==============================================================================
 * Connects frontend components to Django REST Framework backend endpoints:
 * Auth, Guidelines, Clinical Notes, Quizzes, Flashcards, and Study Analytics.
 * ==============================================================================
 */

import type {
  DocumentSummary,
  NoteSummary,
  UserRole,
  Quiz,
  QuizSubmissionResult,
  FlashcardSet,
  StudyStats,
} from '../types';

const TOKEN_KEY = 'clinsaarthi_access_token';
const ROLE_KEY = 'clinsaarthi_active_role';

export const AuthService = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  getStoredRole(): UserRole {
    return (localStorage.getItem(ROLE_KEY) as UserRole) || 'clinician';
  },

  setStoredRole(role: UserRole) {
    localStorage.setItem(ROLE_KEY, role);
  },

  async login(username: string, password: string): Promise<{ access: string; user: any }> {
    const res = await fetch('/api/v1/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    this.setToken(data.access);
    return data;
  },

  async getCurrentUser(token: string): Promise<any> {
    const res = await fetch('/api/v1/auth/me/', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch user profile');
    return res.json();
  },
};

export const GuidelineService = {
  async getDocuments(): Promise<DocumentSummary[]> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/documents/', { headers });
      if (!res.ok) return this.getDemoDocuments();
      const data = await res.json();
      return Array.isArray(data) ? data : data.results || [];
    } catch {
      return this.getDemoDocuments();
    }
  },

  getDemoDocuments(): DocumentSummary[] {
    return [
      {
        id: 'afib-2026-guideline',
        title: 'ESC/AHA 2026 Clinical Guideline for Atrial Fibrillation',
        file_name: 'sample_afib_guideline.pdf',
        total_pages: 18,
        total_chunks: 42,
        status: 'INDEXED',
        uploaded_at: '2026-09-30T10:00:00Z',
      },
    ];
  },
};

export const NotesService = {
  async getNotes(): Promise<NoteSummary[]> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/notes/', { headers });
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : data.results || [];
    } catch {
      return [];
    }
  },
};

export const StudyService = {
  async getQuizzes(): Promise<Quiz[]> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/study/quizzes/', { headers });
      if (!res.ok) return [this.getDemoQuiz()];
      const data = await res.json();
      return Array.isArray(data) ? data : data.results || [this.getDemoQuiz()];
    } catch {
      return [this.getDemoQuiz()];
    }
  },

  async generateQuiz(params: {
    document_id?: string;
    topic?: string;
    difficulty?: string;
    count?: number;
  }): Promise<Quiz> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/study/quizzes/generate/', {
        method: 'POST',
        headers,
        body: JSON.stringify(params),
      });
      if (!res.ok) return this.getDemoQuiz();
      return await res.json();
    } catch {
      return this.getDemoQuiz();
    }
  },

  async submitQuiz(
    quizId: string,
    payload: { answers: Record<string, number>; time_spent_seconds?: number }
  ): Promise<QuizSubmissionResult> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch(`/api/v1/study/quizzes/${quizId}/submit/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      if (!res.ok) return this.calculateDemoSubmission(payload.answers);
      return await res.json();
    } catch {
      return this.calculateDemoSubmission(payload.answers);
    }
  },

  async getFlashcardSets(): Promise<FlashcardSet[]> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/study/flashcards/', { headers });
      if (!res.ok) return [this.getDemoFlashcards()];
      const data = await res.json();
      return Array.isArray(data) ? data : data.results || [this.getDemoFlashcards()];
    } catch {
      return [this.getDemoFlashcards()];
    }
  },

  async generateFlashcards(params: {
    document_id?: string;
    topic?: string;
    count?: number;
  }): Promise<FlashcardSet> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/study/flashcards/generate/', {
        method: 'POST',
        headers,
        body: JSON.stringify(params),
      });
      if (!res.ok) return this.getDemoFlashcards();
      return await res.json();
    } catch {
      return this.getDemoFlashcards();
    }
  },

  async reviewFlashcard(
    cardId: string,
    rating: 'again' | 'hard' | 'good' | 'easy'
  ): Promise<any> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch(`/api/v1/study/flashcards/cards/${cardId}/review/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ rating }),
      });
      if (!res.ok) return { card_id: cardId, rating, repetitions: 1, interval_days: 1 };
      return await res.json();
    } catch {
      return { card_id: cardId, rating, repetitions: 1, interval_days: 1 };
    }
  },

  async getStudyStats(): Promise<StudyStats> {
    const token = AuthService.getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch('/api/v1/study/stats/', { headers });
      if (!res.ok) return this.getDemoStats();
      return await res.json();
    } catch {
      return this.getDemoStats();
    }
  },

  // Fallback demo data for offline simulation
  getDemoQuiz(): Quiz {
    return {
      id: 'demo-quiz-afib-1',
      title: 'ESC/AHA 2026 AFib Guidelines - Board Review Quiz',
      topic: 'Atrial Fibrillation & Anticoagulation',
      difficulty: 'MEDIUM',
      questions_count: 5,
      created_at: new Date().toISOString(),
      questions: [
        {
          id: 'q-demo-1',
          question_text:
            'A 71-year-old male with non-valvular atrial fibrillation has a CrCl of 38 mL/min. If Rivaroxaban is initiated for stroke prevention, what is the guideline-recommended dose?',
          options: [
            '20 mg once daily with the evening meal',
            '15 mg once daily with the evening meal',
            '10 mg twice daily orally',
            'Rivaroxaban is contraindicated at this CrCl',
          ],
          correct_option_index: 1,
          explanation:
            'According to Section 4.2 of the ESC/AHA 2026 Guidelines, for patients with moderate renal impairment (CrCl 15–49 mL/min), Rivaroxaban dose must be reduced from 20 mg to 15 mg once daily with food.',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 4.2',
          page_number: 1,
        },
        {
          id: 'q-demo-2',
          question_text:
            'Under current ESC/AHA Atrial Fibrillation Guidelines, what is the CHA2DS2-VASc score threshold at which oral anticoagulation is strongly recommended for male patients?',
          options: ['Score ≥ 1', 'Score ≥ 2', 'Score ≥ 3', 'Score ≥ 4'],
          correct_option_index: 1,
          explanation:
            'Oral anticoagulation is strongly recommended (Class I) for male patients with a CHA2DS2-VASc score ≥ 2, and in female patients with a score ≥ 3.',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 3.1',
          page_number: 2,
        },
        {
          id: 'q-demo-3',
          question_text:
            'An 82-year-old woman weighing 55 kg with non-valvular AF has serum creatinine 1.2 mg/dL. What is the recommended dosage of Apixaban?',
          options: [
            '5 mg twice daily orally',
            '2.5 mg twice daily orally',
            '2.5 mg once daily orally',
            'Switch to Warfarin (target INR 2.0-3.0)',
          ],
          correct_option_index: 1,
          explanation:
            'Apixaban dose reduction to 2.5 mg BID is indicated if at least two criteria are met: Age ≥ 80 years, Weight ≤ 60 kg, Serum Creatinine ≥ 1.5 mg/dL. This patient meets two criteria (age 82 and weight 55 kg).',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 4.2',
          page_number: 1,
        },
        {
          id: 'q-demo-4',
          question_text:
            'Which medication is preferred as first-line rate control monotherapy in a patient with paroxysmal AF and preserved left ventricular ejection fraction (LVEF 55%)?',
          options: [
            'Digoxin 0.25 mg daily',
            'Amiodarone 200 mg daily',
            'Metoprolol succinate 50-100 mg once daily',
            'Flecainide 100 mg twice daily',
          ],
          correct_option_index: 2,
          explanation:
            'Beta-blockers (e.g. Metoprolol, Bisoprolol) or non-dihydropyridine calcium channel blockers (Diltiazem, Verapamil) are first-line for rate control with preserved LVEF.',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 5.1',
          page_number: 2,
        },
        {
          id: 'q-demo-5',
          question_text:
            'In which clinical scenario is Direct Oral Anticoagulant (DOAC) therapy strictly contraindicated, mandating the use of Vitamin K Antagonists (Warfarin)?',
          options: [
            'Previous history of non-fatal ischemic stroke',
            'Moderate-to-severe mitral stenosis or mechanical prosthetic heart valves',
            'Age older than 85 years with hypertension',
            'Concomitant type 2 diabetes mellitus',
          ],
          correct_option_index: 1,
          explanation:
            'DOACs are contraindicated in patients with mechanical prosthetic heart valves or moderate-to-severe mitral stenosis. Warfarin remains mandatory.',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 4.1',
          page_number: 1,
        },
      ],
    };
  },

  getDemoFlashcards(): FlashcardSet {
    return {
      id: 'demo-deck-1',
      title: 'Cardiology High-Yield Spaced Repetition Deck',
      topic: 'Atrial Fibrillation Guidelines',
      cards_count: 6,
      created_at: new Date().toISOString(),
      cards: [
        {
          id: 'fc-1',
          front: 'DOAC Renal Dosing: What is the Rivaroxaban dose adjustment threshold and regimen?',
          back: 'Standard dose is 20 mg once daily with food. For moderate renal impairment (CrCl 15–49 mL/min), reduce dose to 15 mg once daily with the evening meal. Avoid if CrCl < 15 mL/min.',
          key_concept: 'Renal Clearance & DOAC Dosing',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 4.2',
          page_number: 1,
          interval_days: 1,
          ease_factor: 2.5,
          repetitions: 0,
        },
        {
          id: 'fc-2',
          front: "Apixaban '2 of 3' Rule: What three clinical criteria dictate a dose reduction to 2.5 mg BID?",
          back: 'Reduce to 2.5 mg twice daily if patient meets at least TWO of: (1) Age ≥ 80 years, (2) Body weight ≤ 60 kg, (3) Serum creatinine ≥ 1.5 mg/dL.',
          key_concept: 'Apixaban Dose Reduction',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 4.2',
          page_number: 1,
          interval_days: 1,
          ease_factor: 2.5,
          repetitions: 0,
        },
        {
          id: 'fc-3',
          front: 'CHA2DS2-VASc Criteria: What are the component risk factors and thresholds for anticoagulation?',
          back: 'C: CHF (1), H: HTN (1), A2: Age ≥75 (2), D: Diabetes (1), S2: Stroke/TIA (2), V: Vascular Disease (1), A: Age 65-74 (1), Sc: Sex Category Female (1).\nThreshold: Score ≥ 2 in males, ≥ 3 in females indicates oral anticoagulation.',
          key_concept: 'Stroke Risk Stratification',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 3.1',
          page_number: 2,
          interval_days: 2,
          ease_factor: 2.6,
          repetitions: 1,
        },
        {
          id: 'fc-4',
          front: 'Acute Rate Control in AF: What is first-line pharmacotherapy and resting heart rate target?',
          back: 'First-line agents: Beta-blockers (Metoprolol, Bisoprolol) or non-DHP CCBs (Diltiazem, Verapamil). Target lenient rate control: resting heart rate < 110 bpm. Avoid CCBs in HFrEF (LVEF ≤ 40%).',
          key_concept: 'Rate Control Pharmacotherapy',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 5.1',
          page_number: 2,
          interval_days: 1,
          ease_factor: 2.5,
          repetitions: 0,
        },
        {
          id: 'fc-5',
          front: 'Valvular vs Non-Valvular AF: When is Warfarin mandatory over DOACs?',
          back: 'DOACs are contraindicated in mechanical prosthetic heart valves or moderate-to-severe rheumatic mitral stenosis. Warfarin (target INR 2.0–3.0 or 2.5–3.5 depending on valve position) is mandatory.',
          key_concept: 'Valvular Contraindications',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 4.1',
          page_number: 1,
          interval_days: 4,
          ease_factor: 2.7,
          repetitions: 2,
        },
        {
          id: 'fc-6',
          front: 'Antithrombotic Management Post-PCI in AF: What is the recommended strategy?',
          back: 'Dual Therapy (DOAC + Clopidogrel 75 mg once daily) is preferred over Triple Therapy. Triple therapy (DOAC + Aspirin + P2Y12 inhibitor) should be limited to ≤ 1 week post-PCI to minimize fatal bleeding.',
          key_concept: 'Post-PCI Dual Pathway Therapy',
          source_reference: 'ESC/AHA 2026 AF Guidelines - Section 6.3',
          page_number: 2,
          interval_days: 1,
          ease_factor: 2.5,
          repetitions: 0,
        },
      ],
    };
  },

  getDemoStats(): StudyStats {
    return {
      total_quizzes_completed: 6,
      average_quiz_score: 84.5,
      total_flashcards_reviewed: 42,
      total_study_time_minutes: 38,
      topics: [
        { topic: 'Anticoagulation & DOAC Dosing', accuracy: 90.0, total_questions: 10 },
        { topic: 'CHA2DS2-VASc Risk Stratification', accuracy: 85.0, total_questions: 8 },
        { topic: 'Rate vs Rhythm Control Strategies', accuracy: 80.0, total_questions: 10 },
        { topic: 'Valvular Heart Disease Contraindications', accuracy: 83.3, total_questions: 6 },
      ],
    };
  },

  calculateDemoSubmission(answers: Record<string, number>): QuizSubmissionResult {
    const demoQuiz = this.getDemoQuiz();
    let correct = 0;
    const results = demoQuiz.questions.map((q) => {
      const selected = answers[q.id];
      const isCorrect = selected === q.correct_option_index;
      if (isCorrect) correct += 1;
      return {
        question_id: q.id,
        question_text: q.question_text,
        selected_option_index: selected,
        selected_option_text: selected !== undefined ? q.options[selected] : 'None',
        correct_option_index: q.correct_option_index,
        correct_option_text: q.options[q.correct_option_index],
        is_correct: isCorrect,
        explanation: q.explanation,
        source_reference: q.source_reference,
        page_number: q.page_number,
      };
    });

    const score = Math.round((correct / demoQuiz.questions.length) * 100);
    return {
      session_id: `session-${Date.now()}`,
      quiz_id: demoQuiz.id,
      quiz_title: demoQuiz.title,
      total_questions: demoQuiz.questions.length,
      correct_answers: correct,
      score_percentage: score,
      passed: score >= 70,
      time_spent_seconds: 60,
      results,
    };
  },
};
