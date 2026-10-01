/**
 * ==============================================================================
 * ClinSaarthi AI - Frontend TypeScript Domain Interfaces
 * ==============================================================================
 * Defines the strict type contracts for Messages, Citations, Spatial Bounding Boxes,
 * Drug Verification Results, Clinical Notes, Study Mode (Quizzes & Flashcards),
 * and SSE Event Payloads.
 * ==============================================================================
 */

export type UserRole = 'clinician' | 'student' | 'admin';

export type AppMode = 'guideline_qa' | 'clinical_note_qa' | 'study_mode';

export interface BoundingBox {
  x0?: number;
  y0?: number;
  x1?: number;
  y1?: number;
  page_width?: number;
  page_height?: number;
}

export interface Citation {
  id?: string;
  citation_index: number;
  inline_tag: string; // e.g. "[1]"
  source_title: string;
  page_number: number;
  section_title?: string;
  highlight_text: string;
  bounding_box?: BoundingBox;
}

export type VerificationStatus = 'VERIFIED' | 'UNSUPPORTED' | 'CONFLICT';

export interface VerificationResult {
  id?: string;
  drug_name: string;
  dosage?: string;
  unit?: string;
  route?: string;
  frequency?: string;
  status: VerificationStatus;
  nli_score?: number;
  explanation: string;
  rxnorm_cui?: string;
  openfda_match?: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  confidence_score?: number;
  is_not_found?: boolean;
  disclaimer?: string;
  citations?: Citation[];
  verifications?: VerificationResult[];
  created_at?: string;
  streaming?: boolean;
}

export interface DocumentSummary {
  id: string;
  title: string;
  file_name: string;
  total_pages: number;
  total_chunks: number;
  status: 'PENDING' | 'INDEXED' | 'FAILED';
  uploaded_at: string;
}

export interface NoteSummary {
  id: string;
  title: string;
  original_length: number;
  masked_length: number;
  detected_entities_count: number;
  pii_mapping?: Record<string, string>;
  raw_content?: string;
  masked_content?: string;
  created_at: string;
}

// ------------------------------------------------------------------------------
// Study Mode Contracts (Quizzes, Flashcards, Spaced Repetition, Analytics)
// ------------------------------------------------------------------------------

export interface QuizQuestion {
  id: string;
  question_text: string;
  options: string[];
  correct_option_index: number;
  explanation: string;
  source_reference: string;
  page_number?: number;
}

export interface Quiz {
  id: string;
  title: string;
  topic: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  questions_count: number;
  questions: QuizQuestion[];
  created_at: string;
}

export interface QuestionResult {
  question_id: string;
  question_text: string;
  selected_option_index?: number;
  selected_option_text: string;
  correct_option_index: number;
  correct_option_text: string;
  is_correct: boolean;
  explanation: string;
  source_reference: string;
  page_number?: number;
}

export interface QuizSubmissionResult {
  session_id: string;
  quiz_id: string;
  quiz_title: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  passed: boolean;
  time_spent_seconds: number;
  results: QuestionResult[];
}

export interface Flashcard {
  id: string;
  front: string;
  back: string;
  key_concept: string;
  source_reference: string;
  page_number?: number;
  ease_factor?: number;
  interval_days?: number;
  repetitions?: number;
  last_reviewed?: string;
  next_review?: string;
}

export interface FlashcardSet {
  id: string;
  title: string;
  topic: string;
  cards_count: number;
  cards: Flashcard[];
  created_at: string;
}

export interface TopicAccuracy {
  topic: string;
  accuracy: number;
  total_questions: number;
}

export interface StudyStats {
  total_quizzes_completed: number;
  average_quiz_score: number;
  total_flashcards_reviewed: number;
  total_study_time_minutes: number;
  topics: TopicAccuracy[];
}

// ------------------------------------------------------------------------------
// SSE Stream Event Payloads
// ------------------------------------------------------------------------------

export interface SSEStatusEvent {
  type: 'status';
  stage: 'understanding' | 'retrieving' | 'generating' | 'verifying';
  message: string;
}

export interface SSETokenEvent {
  type: 'token';
  content: string;
}

export interface SSECitationsEvent {
  type: 'citations';
  citations: Citation[];
}

export interface SSEVerificationsEvent {
  type: 'verifications';
  verifications: VerificationResult[];
}

export interface SSEDoneEvent {
  type: 'done';
  conversation_id: string;
  message_id: string;
  is_not_found: boolean;
  confidence_score: number;
  citations: Citation[];
  verifications?: VerificationResult[];
  disclaimer: string;
}

export type SSEPayload =
  | SSEStatusEvent
  | SSETokenEvent
  | SSECitationsEvent
  | SSEVerificationsEvent
  | SSEDoneEvent;
