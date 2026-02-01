import { create } from 'zustand';
import type { Session } from '@/types/specs';

interface SessionStore {
  session: Session | null;
  isInitializing: boolean;
  error: string | null;
  setSession: (session: Session) => void;
  setInitializing: (initializing: boolean) => void;
  setError: (error: string | null) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  session: null,
  isInitializing: false,
  error: null,

  setSession: (session) => {
    sessionStorage.setItem('sessionId', session.sessionId);
    set({ session, error: null });
  },

  setInitializing: (isInitializing) => set({ isInitializing }),

  setError: (error) => set({ error }),

  clearSession: () => {
    sessionStorage.removeItem('sessionId');
    set({ session: null, error: null });
  },
}));
