/**
 * ==============================================================================
 * ClinSaarthi AI - REST API Service Client
 * ==============================================================================
 * Connects frontend components to Django REST Framework backend endpoints:
 * Auth, Guidelines, Clinical Notes, and Consultation Exports.
 * ==============================================================================
 */

import type { DocumentSummary, NoteSummary, UserRole } from '../types';

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
