/**
 * Tests for API hooks.
 *
 * Tests the React Query hooks that handle API communication.
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import { apiClient } from '../client';
import {
  useCreateSession,
  useUploadResume,
  useUploadJobDescription,
  useStartAnalysis,
  useAnalysisResults,
  useRecommendations,
  useInterviewPrep,
  useMarketInsights,
  useChatMutation,
} from '../hooks';
import { useSessionStore, useAnalysisStore, useWizardStore } from '@/store';

// Mock the API client
vi.mock('../client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock the stores
vi.mock('@/store', () => ({
  useSessionStore: vi.fn(),
  useAnalysisStore: vi.fn(),
  useWizardStore: vi.fn(),
}));

// Helper to create a wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// Mock store state and setters
const mockSetSession = vi.fn();
const mockSetInitializing = vi.fn();
const mockSetError = vi.fn();
const mockSetResume = vi.fn();
const mockSetCanProceed = vi.fn();
const mockAddJob = vi.fn();
const mockSetAnalyzing = vi.fn();
const mockSetAnalysisResult = vi.fn();

describe('API Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default store mocks
    (useSessionStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        session: { sessionId: 'test-session-123' },
        setSession: mockSetSession,
        setInitializing: mockSetInitializing,
        setError: mockSetError,
      };
      return selector ? selector(state) : state;
    });

    (useAnalysisStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        setResume: mockSetResume,
        addJob: mockAddJob,
        setAnalysisResult: mockSetAnalysisResult,
      };
      return selector ? selector(state) : state;
    });

    (useWizardStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        setCanProceed: mockSetCanProceed,
        setAnalyzing: mockSetAnalyzing,
      };
      return selector ? selector(state) : state;
    });
  });

  describe('useCreateSession', () => {
    it('creates a session and updates store on success', async () => {
      const mockResponse = {
        data: {
          session_id: 'new-session-456',
          created_at: '2026-01-31T10:00:00Z',
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useCreateSession(), {
        wrapper: createWrapper(),
      });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/session');
      expect(mockSetInitializing).toHaveBeenCalledWith(true);
      expect(mockSetSession).toHaveBeenCalledWith({
        sessionId: 'new-session-456',
        createdAt: '2026-01-31T10:00:00Z',
      });
      expect(mockSetInitializing).toHaveBeenCalledWith(false);
    });

    it('handles errors and updates store', async () => {
      const error = new Error('Network error');
      (apiClient.post as Mock).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useCreateSession(), {
        wrapper: createWrapper(),
      });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(mockSetError).toHaveBeenCalledWith('Network error');
      expect(mockSetInitializing).toHaveBeenCalledWith(false);
    });
  });

  describe('useUploadResume', () => {
    it('uploads resume and updates store on success', async () => {
      const mockResponse = {
        data: {
          resume_id: 'resume-789',
          skills: [{ name: 'Python', level: 'advanced' }],
          experiences: [{ title: 'Developer', company: 'Acme' }],
          education: [{ degree: 'BS', institution: 'MIT' }],
          summary: 'Experienced developer',
          pii_redacted: true,
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useUploadResume(), {
        wrapper: createWrapper(),
      });

      const mockFile = new File(['resume content'], 'resume.pdf', {
        type: 'application/pdf',
      });
      result.current.mutate(mockFile);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/upload/resume',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 300000,
        })
      );
      expect(mockSetResume).toHaveBeenCalledWith({
        id: 'resume-789',
        skills: [{ name: 'Python', level: 'advanced' }],
        experiences: [{ title: 'Developer', company: 'Acme' }],
        education: [{ degree: 'BS', institution: 'MIT' }],
        certifications: [],
        summary: 'Experienced developer',
        contactRedacted: true,
      });
      expect(mockSetCanProceed).toHaveBeenCalledWith(true);
    });

    it('includes session ID in form data when available', async () => {
      const mockResponse = {
        data: {
          resume_id: 'resume-789',
          skills: [],
          experiences: [],
          education: [],
          summary: '',
          pii_redacted: false,
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useUploadResume(), {
        wrapper: createWrapper(),
      });

      const mockFile = new File(['content'], 'resume.pdf');
      result.current.mutate(mockFile);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const formDataCall = (apiClient.post as Mock).mock.calls[0][1] as FormData;
      expect(formDataCall.get('session_id')).toBe('test-session-123');
    });
  });

  describe('useUploadJobDescription', () => {
    it('uploads job description and adds to store', async () => {
      const mockResponse = {
        data: {
          job_id: 'job-001',
          title: 'Senior Engineer',
          company: 'Tech Corp',
          requirements: ['5+ years experience'],
          required_skills: [{ name: 'Python', level: 'expert' }],
          nice_to_have_skills: [{ name: 'Go', level: 'intermediate' }],
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useUploadJobDescription(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('Job description text here...');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/upload/job-description',
        { text: 'Job description text here...' },
        { timeout: 120000 }
      );
      expect(mockAddJob).toHaveBeenCalledWith({
        id: 'job-001',
        title: 'Senior Engineer',
        company: 'Tech Corp',
        requirements: ['5+ years experience'],
        requiredSkills: [{ name: 'Python', level: 'expert' }],
        niceToHaveSkills: [{ name: 'Go', level: 'intermediate' }],
        educationRequirements: [],
        responsibilities: [],
        cultureSignals: [],
      });
    });
  });

  describe('useStartAnalysis', () => {
    it('starts analysis and sets analyzing state', async () => {
      const mockResponse = {
        data: {
          status: 'started',
          message: 'Analysis started',
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useStartAnalysis(), {
        wrapper: createWrapper(),
      });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/analyze', {
        session_id: 'test-session-123',
      });
      expect(mockSetAnalyzing).toHaveBeenCalledWith(true);
    });
  });

  describe('useAnalysisResults', () => {
    it('fetches results and updates store when completed', async () => {
      const mockResponse = {
        data: {
          status: 'completed',
          job_matches: [{ job_id: 'job-001', fit_score: 85 }],
          overall_fit_score: 85,
        },
      };
      (apiClient.get as Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useAnalysisResults('test-session-123', true),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/results/test-session-123');
      expect(mockSetAnalysisResult).toHaveBeenCalled();
      expect(mockSetAnalyzing).toHaveBeenCalledWith(false);
      expect(mockSetCanProceed).toHaveBeenCalledWith(true);
    });

    it('does not fetch when disabled', () => {
      renderHook(() => useAnalysisResults('test-session-123', false), {
        wrapper: createWrapper(),
      });

      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('does not fetch when sessionId is null', () => {
      renderHook(() => useAnalysisResults(null, true), {
        wrapper: createWrapper(),
      });

      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('continues polling when status is not completed', async () => {
      const mockResponse = {
        data: {
          status: 'processing',
          progress: 50,
        },
      };
      (apiClient.get as Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useAnalysisResults('test-session-123', true),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.data?.status).toBe('processing');
      });

      // Store should not be updated when still processing
      expect(mockSetAnalysisResult).not.toHaveBeenCalled();
    });
  });

  describe('useRecommendations', () => {
    it('fetches recommendations for a session', async () => {
      const mockResponse = {
        data: {
          recommendations: [
            { id: 'rec-1', title: 'Learn Kubernetes', priority: 'high' },
          ],
        },
      };
      (apiClient.get as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(
        () => useRecommendations('test-session-123', null),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/recommendations/test-session-123'
      );
    });

    it('includes job ID in URL when provided', async () => {
      const mockResponse = { data: { recommendations: [] } };
      (apiClient.get as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(
        () => useRecommendations('test-session-123', 'job-001'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/recommendations/test-session-123?job_id=job-001'
      );
    });
  });

  describe('useInterviewPrep', () => {
    it('fetches interview prep content', async () => {
      const mockResponse = {
        data: {
          questions: [
            { id: 'q-1', question: 'Tell me about yourself', category: 'behavioral' },
          ],
          talking_points: ['Highlight Python experience'],
        },
      };
      (apiClient.get as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(
        () => useInterviewPrep('test-session-123', 'job-001'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/interview-prep/test-session-123?job_id=job-001'
      );
      expect(result.current.data?.questions).toHaveLength(1);
    });
  });

  describe('useMarketInsights', () => {
    it('fetches market insights', async () => {
      const mockResponse = {
        data: {
          salary_range: { min: 120000, max: 180000 },
          demand_level: 'high',
          trending_skills: ['Kubernetes', 'AI/ML'],
        },
      };
      (apiClient.get as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(
        () => useMarketInsights('test-session-123', 'job-001'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/market-insights/test-session-123?job_id=job-001'
      );
    });
  });

  describe('useChatMutation', () => {
    it('sends chat message and returns response', async () => {
      const mockResponse = {
        data: {
          message: 'Based on your resume, you should emphasize...',
          sources: ['resume', 'job-001'],
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useChatMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        message: 'What skills should I highlight?',
        jobId: 'job-001',
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/chat',
        {
          message: 'What skills should I highlight?',
          job_id: 'job-001',
        },
        { timeout: 60000 }
      );
      expect(result.current.data?.message).toContain('Based on your resume');
    });
  });

  describe('toCamelCase transformation', () => {
    it('transforms snake_case keys to camelCase in response', async () => {
      const mockResponse = {
        data: {
          session_id: 'test-123',
          created_at: '2026-01-31',
          nested_object: {
            inner_value: 'test',
            deep_nested: {
              very_deep: 'value',
            },
          },
          array_field: [
            { item_name: 'first' },
            { item_name: 'second' },
          ],
        },
      };
      (apiClient.post as Mock).mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useCreateSession(), {
        wrapper: createWrapper(),
      });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Verify the transformation happened
      expect(mockSetSession).toHaveBeenCalledWith(
        expect.objectContaining({
          sessionId: 'test-123',
          createdAt: '2026-01-31',
          nestedObject: expect.objectContaining({
            innerValue: 'test',
            deepNested: expect.objectContaining({
              veryDeep: 'value',
            }),
          }),
          arrayField: [
            { itemName: 'first' },
            { itemName: 'second' },
          ],
        })
      );
    });
  });
});
