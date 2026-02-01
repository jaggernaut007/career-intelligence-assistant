/**
 * Tests for sessionStore.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSessionStore } from '../sessionStore';
import type { Session } from '@/types/specs';

describe('sessionStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useSessionStore.setState({
      session: null,
      isInitializing: false,
      error: null,
    });
    // Clear sessionStorage
    sessionStorage.clear();
  });

  describe('Initial State', () => {
    it('has null session initially', () => {
      expect(useSessionStore.getState().session).toBeNull();
    });

    it('is not initializing initially', () => {
      expect(useSessionStore.getState().isInitializing).toBe(false);
    });

    it('has no error initially', () => {
      expect(useSessionStore.getState().error).toBeNull();
    });
  });

  describe('setSession', () => {
    const mockSession: Session = {
      sessionId: 'test-session-123',
      createdAt: '2024-01-01T00:00:00Z',
      expiresAt: '2024-01-02T00:00:00Z',
    };

    it('sets the session', () => {
      useSessionStore.getState().setSession(mockSession);
      expect(useSessionStore.getState().session).toEqual(mockSession);
    });

    it('stores sessionId in sessionStorage', () => {
      useSessionStore.getState().setSession(mockSession);
      expect(sessionStorage.getItem('sessionId')).toBe('test-session-123');
    });

    it('clears error when session is set', () => {
      useSessionStore.setState({ error: 'Some error' });
      useSessionStore.getState().setSession(mockSession);
      expect(useSessionStore.getState().error).toBeNull();
    });
  });

  describe('setInitializing', () => {
    it('sets initializing to true', () => {
      useSessionStore.getState().setInitializing(true);
      expect(useSessionStore.getState().isInitializing).toBe(true);
    });

    it('sets initializing to false', () => {
      useSessionStore.setState({ isInitializing: true });
      useSessionStore.getState().setInitializing(false);
      expect(useSessionStore.getState().isInitializing).toBe(false);
    });
  });

  describe('setError', () => {
    it('sets error message', () => {
      useSessionStore.getState().setError('Connection failed');
      expect(useSessionStore.getState().error).toBe('Connection failed');
    });

    it('clears error with null', () => {
      useSessionStore.setState({ error: 'Some error' });
      useSessionStore.getState().setError(null);
      expect(useSessionStore.getState().error).toBeNull();
    });
  });

  describe('clearSession', () => {
    it('clears the session', () => {
      const mockSession: Session = {
        sessionId: 'test-123',
        createdAt: '2024-01-01T00:00:00Z',
        expiresAt: '2024-01-02T00:00:00Z',
      };
      useSessionStore.setState({ session: mockSession });

      useSessionStore.getState().clearSession();
      expect(useSessionStore.getState().session).toBeNull();
    });

    it('removes sessionId from sessionStorage', () => {
      sessionStorage.setItem('sessionId', 'test-123');

      useSessionStore.getState().clearSession();
      expect(sessionStorage.getItem('sessionId')).toBeNull();
    });

    it('clears error', () => {
      useSessionStore.setState({ error: 'Some error' });
      useSessionStore.getState().clearSession();
      expect(useSessionStore.getState().error).toBeNull();
    });
  });

  describe('Selector Pattern', () => {
    it('can select session with hook', () => {
      const mockSession: Session = {
        sessionId: 'test-123',
        createdAt: '2024-01-01T00:00:00Z',
        expiresAt: '2024-01-02T00:00:00Z',
      };
      useSessionStore.setState({ session: mockSession });

      const session = useSessionStore.getState().session;
      expect(session?.sessionId).toBe('test-123');
    });
  });
});
