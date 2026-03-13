import { create } from 'zustand';
import type { Session } from '@/types/specs';

interface SessionStore {
  session: Session | null;
  isInitializing: boolean;
  error: string | null;
  apiKeyValidated: boolean;
  setSession: (session: Session) => void;
  setInitializing: (initializing: boolean) => void;
  setError: (error: string | null) => void;
  setApiKeyValidated: (validated: boolean) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  session: null,
  isInitializing: false,
  error: null,
  apiKeyValidated: false,

  setSession: (session) => {
    sessionStorage.setItem('sessionId', session.sessionId);
    set({ session, error: null });
  },

  setInitializing: (isInitializing) => set({ isInitializing }),

  setError: (error) => set({ error }),

  setApiKeyValidated: (apiKeyValidated) => set({ apiKeyValidated }),

  clearSession: () => {
    sessionStorage.removeItem('sessionId');
    set({ session: null, isInitializing: false, error: null, apiKeyValidated: false });
  },
}));
