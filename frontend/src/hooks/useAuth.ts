/**
 * ==============================================================================
 * ClinSaarthi AI - User & Role State Hook
 * ==============================================================================
 * Manages active clinician/student/admin role context across the application.
 * Supports instant role switching for rapid demonstration of RBAC permissions.
 * ==============================================================================
 */

import { useState, useEffect } from 'react';
import type { UserRole } from '../types';
import { AuthService } from '../services/api';

export interface AuthContextValue {
  role: UserRole;
  setRole: (role: UserRole) => void;
  token: string | null;
  username: string;
  department: string;
  switchRole: (newRole: UserRole) => void;
}

export function useAuth(): AuthContextValue {
  const [role, setRoleState] = useState<UserRole>(() => AuthService.getStoredRole());
  const [token, setTokenState] = useState<string | null>(() => AuthService.getToken());

  const roleMeta: Record<UserRole, { username: string; department: string }> = {
    clinician: { username: 'Dr. Kavya Sharma, MD', department: 'Cardiology & Intensive Care' },
    student: { username: 'Rohan Verma (Resident)', department: 'General Internal Medicine' },
    admin: { username: 'System Administrator', department: 'Clinical IT & Compliance' },
  };

  const switchRole = (newRole: UserRole) => {
    setRoleState(newRole);
    AuthService.setStoredRole(newRole);
  };

  useEffect(() => {
    // If no token exists, set demo mock token so all API calls have auth headers
    if (!token) {
      const demoToken = 'demo-jwt-clinsaarthi-token';
      setTokenState(demoToken);
      AuthService.setToken(demoToken);
    }
  }, [token]);

  return {
    role,
    setRole: switchRole,
    token,
    username: roleMeta[role].username,
    department: roleMeta[role].department,
    switchRole,
  };
}
