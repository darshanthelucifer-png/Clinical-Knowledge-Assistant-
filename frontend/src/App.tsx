import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SplitPane } from './components/SplitPane';
import { ChatPanel } from './components/Chat/ChatPanel';
import { SourceViewer } from './components/Viewer/SourceViewer';
import { StudyModeView } from './components/Study/StudyModeView';
import { useAuth } from './hooks/useAuth';
import type { Message, Citation, AppMode, DocumentSummary, VerificationResult } from './types';
import { streamClinicalQA } from './services/sseStream';
import { GuidelineService } from './services/api';

export const App: React.FC = () => {
  const { role, switchRole, username, token } = useAuth();
  const [activeMode, setActiveMode] = useState<AppMode>('guideline_qa');
  const [activeNoteId, setActiveNoteId] = useState<string | null>('sample-note-1');
  const [activeNoteTitle, setActiveNoteTitle] = useState<string | null>('Cardiology Discharge Note');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  // Multi-Guideline Document Management State
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  // Fetch all available indexed clinical guideline documents on load
  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const docs = await GuidelineService.getDocuments();
        setDocuments(docs);
      } catch (err) {
        console.error('Failed to load clinical guideline documents:', err);
      }
    };
    fetchDocs();
  }, [token]);

  const handleSelectNoteForQA = (noteId: string, noteTitle: string) => {
    setActiveMode('clinical_note_qa');
    setActiveNoteId(noteId);
    setActiveNoteTitle(noteTitle);
  };

  const handleUploadGuideline = async (file: File) => {
    try {
      const newDoc = await GuidelineService.uploadDocument(file);
      setDocuments((prev) => [newDoc, ...prev]);
      setSelectedDocumentId(newDoc.id);
    } catch (err: any) {
      alert(`Guideline upload error: ${err.message || err}`);
    }
  };

  // Find currently selected document object
  const selectedDoc = documents.find((d) => d.id === selectedDocumentId) || null;

  // Send message and stream answer via SSE
  const handleSendMessage = async (query: string, useAgentic: boolean) => {
    if (isStreaming) return;

    // 1. Add User Question to Chat
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };

    // 2. Add Assistant Skeleton
    const assistantId = `asst-${Date.now()}`;
    const initialAssistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);
    setStreamingStatus(
      activeMode === 'clinical_note_qa'
        ? 'Retrieving patient clinical context and matching against clinical guidelines...'
        : selectedDoc
        ? `Scoping dense & BM25 retrieval strictly to "${selectedDoc.title}"...`
        : 'Analyzing clinical query across all certified clinical practice guidelines...'
    );

    let accumulatedTokens = '';

    await streamClinicalQA({
      question: query,
      token,
      agentic: useAgentic,
      documentIds: selectedDocumentId ? [selectedDocumentId] : [],
      noteId: activeMode === 'clinical_note_qa' ? activeNoteId : null,
      callbacks: {
        onStatus: (msg) => {
          setStreamingStatus(msg);
        },
        onToken: (tokenText) => {
          accumulatedTokens += tokenText;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: accumulatedTokens } : m
            )
          );
        },
        onCitations: (citations) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, citations } : m))
          );
          if (citations.length > 0 && !activeCitation) {
            setActiveCitation(citations[0]);
          }
        },
        onVerifications: (verifications) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, verifications } : m))
          );
        },
        onDone: (doneData) => {
          setIsStreaming(false);
          setStreamingStatus('');
          const hasScore = doneData.confidence_score !== null && doneData.confidence_score !== undefined;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: accumulatedTokens || (doneData.is_not_found ? m.content : accumulatedTokens),
                    confidence_score: hasScore ? doneData.confidence_score : undefined,
                    is_not_found: doneData.is_not_found,
                    citations: doneData.citations || [],
                    verifications: doneData.verifications || [],
                    disclaimer: doneData.disclaimer,
                    streaming: false,
                  }
                : m
            )
          );
        },
        onError: (err) => {
          setIsStreaming(false);
          setStreamingStatus('');
          const errDetail = err?.message || 'Server connection error';
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: `⚠️ **Connection Error**: Unable to complete clinical query (${errDetail}). Please ensure the ClinSaarthi backend service is running.`,
                    confidence_score: undefined,
                    is_not_found: true,
                    citations: [],
                    verifications: [],
                    disclaimer:
                      'ClinSaarthi AI is an automated decision-support system. System connectivity issue.',
                    streaming: false,
                  }
                : m
            )
          );
        },
      },
    });
  };

  const handleClearChat = () => {
    setMessages([]);
    setActiveCitation(null);
  };

  const handleExportMarkdown = () => {
    if (messages.length === 0) {
      alert('Consultation is empty. Please ask questions before exporting.');
      return;
    }

    const lines = [
      '# ClinSaarthi AI Consultation Export',
      `**Export Date**: ${new Date().toUTCString()}`,
      `**Consulting Clinician**: ${username}`,
      `**Active Role**: ${role.toUpperCase()}`,
      `**Guideline Scope**: ${selectedDoc ? selectedDoc.title : 'All Active Guidelines (Cross-Domain)'}`,
      `**Clinical Mode**: ${activeMode === 'clinical_note_qa' ? 'Clinical Note & Guideline Analysis' : 'Guideline Q&A'}`,
      '\n---\n',
    ];

    for (const msg of messages) {
      const header =
        msg.role === 'user' ? '### 🧑‍⚕️ Clinician Query' : '### 🤖 ClinSaarthi AI Guidance';
      lines.push(`${header}:\n${msg.content}\n`);

      if (msg.role === 'assistant' && msg.citations && msg.citations.length > 0) {
        lines.push('#### 📚 Verified Guideline Citations:');
        for (const cit of msg.citations) {
          lines.push(
            `- **${cit.inline_tag}**: *${cit.source_title}* (Page ${cit.page_number}) - Section: ${cit.section_title || 'General'}\n  > "${cit.highlight_text}"`
          );
        }
        lines.push('');
      }

      if (msg.role === 'assistant' && msg.verifications && msg.verifications.length > 0) {
        lines.push('#### 🛡️ Pharmaceutical Verification Audit:');
        for (const v of msg.verifications) {
          lines.push(`- **${v.drug_name}** (${v.dosage || ''} ${v.unit || ''}): [${v.status}] — ${v.explanation}`);
        }
        lines.push('');
      }
    }

    lines.push('\n---\n');
    lines.push(
      '> **MANDATORY MEDICAL DISCLAIMER**:\n> ClinSaarthi AI is an automated decision-support reference intended strictly for qualified clinicians and supervised medical students.'
    );

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ClinSaarthi_Consultation_${Date.now()}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      <Header
        role={role}
        onRoleChange={switchRole}
        activeMode={activeMode}
        onModeChange={setActiveMode}
        onExportMarkdown={handleExportMarkdown}
        username={username}
      />

      <SplitPane
        initialLeftPercentage={58}
        left={
          activeMode === 'study_mode' ? (
            <StudyModeView onSelectCitation={setActiveCitation} />
          ) : (
            <ChatPanel
              messages={messages}
              isStreaming={isStreaming}
              streamingStatus={streamingStatus}
              activeMode={activeMode}
              activeNoteTitle={activeNoteTitle || undefined}
              documents={documents}
              selectedDocumentId={selectedDocumentId}
              onSelectDocument={setSelectedDocumentId}
              onUploadGuideline={handleUploadGuideline}
              onSendMessage={handleSendMessage}
              onClearChat={handleClearChat}
              activeCitation={activeCitation}
              onSelectCitation={setActiveCitation}
            />
          )
        }
        right={
          <SourceViewer
            activeCitation={activeCitation}
            activeMode={activeMode}
            documentTitle={
              activeCitation?.source_title ||
              selectedDoc?.title ||
              '2026 AHA/ACC/HRS Guideline for the Management of Atrial Fibrillation'
            }
            totalPages={selectedDoc?.total_pages || 4}
            onSelectNoteForQA={handleSelectNoteForQA}
          />
        }
      />
    </div>
  );
};

export default App;
