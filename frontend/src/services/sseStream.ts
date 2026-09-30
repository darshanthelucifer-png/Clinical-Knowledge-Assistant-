/**
 * ==============================================================================
 * ClinSaarthi AI - Server-Sent Events (SSE) Stream Consumer
 * ==============================================================================
 * Consumes chunked text/event-stream payloads from Django backend:
 * data: {"type": "status" | "token" | "citations" | "verifications" | "done", ...}\n\n
 *
 * Python/React Concepts Demonstrated:
 * 1. Web Streams API: Uses ReadableStreamDefaultReader to parse real-time incoming
 *    TCP buffers without waiting for full response closure.
 * 2. Event Slicing: Buffers partial chunks across frames to reliably handle
 *    arbitrary TCP packet fragmentation.
 * ==============================================================================
 */

import type { Citation, VerificationResult, SSEDoneEvent } from '../types';

export interface StreamCallbacks {
  onStatus?: (message: string, stage: string) => void;
  onToken?: (token: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onVerifications?: (verifications: VerificationResult[]) => void;
  onDone?: (doneData: SSEDoneEvent) => void;
  onError?: (err: Error) => void;
}

export interface StreamParams {
  question: string;
  token?: string | null;
  documentIds?: string[];
  noteId?: string | null;
  agentic?: boolean;
  conversationId?: string | null;
  signal?: AbortSignal;
  callbacks: StreamCallbacks;
}

export async function streamClinicalQA({
  question,
  token,
  documentIds = [],
  noteId = null,
  agentic = false,
  conversationId = null,
  signal,
  callbacks,
}: StreamParams): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const payload: Record<string, any> = {
    question,
    stream: true,
    agentic,
    document_ids: documentIds,
    conversation_id: conversationId,
  };

  if (noteId) {
    payload.note_id = noteId;
  }

  try {
    const response = await fetch('/api/v1/qa/ask/', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Server returned HTTP ${response.status}: ${errText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null, cannot stream SSE.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || ''; // Keep partial frame in buffer

      for (const frame of frames) {
        const trimmed = frame.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;

        const jsonStr = trimmed.slice(5).trim();
        try {
          const data = JSON.parse(jsonStr);

          switch (data.type) {
            case 'status':
              callbacks.onStatus?.(data.message, data.stage);
              break;
            case 'token':
              callbacks.onToken?.(data.content);
              break;
            case 'citations':
              callbacks.onCitations?.(data.citations);
              break;
            case 'verifications':
              callbacks.onVerifications?.(data.verifications);
              break;
            case 'done':
              callbacks.onDone?.(data);
              break;
            default:
              break;
          }
        } catch (parseErr) {
          console.warn('[SSE Parser] Failed to parse JSON frame:', jsonStr, parseErr);
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      console.log('[SSE Stream] Stream aborted by user.');
      return;
    }
    console.error('[SSE Stream] Error:', err);
    callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
  }
}
