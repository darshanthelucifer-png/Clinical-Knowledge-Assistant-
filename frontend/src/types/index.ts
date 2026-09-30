/**
 * ==============================================================================
 * ClinSaarthi AI - Frontend TypeScript Domain Interfaces
 * ==============================================================================
 * Defines the strict type contracts for Messages, Citations, Spatial Bounding Boxes,
 * Drug Verification Results, Clinical Notes, and SSE Event Payloads.
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
