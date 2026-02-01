import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import { useSessionStore, useAnalysisStore, useWizardStore } from '@/store';
import type {
  Session,
  ResumeUploadResponse,
  JobDescriptionUploadResponse,
  AnalysisStartedResponse,
  AnalysisResult,
  RecommendationResult,
  InterviewPrepResult,
  MarketInsightsResult,
  ChatRequest,
  ChatResponse,
} from '@/types/specs';

// Helper to deeply transform snake_case to camelCase
function toCamelCase<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((item) => toCamelCase(item)) as T;
  }
  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const key in obj as Record<string, unknown>) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = toCamelCase((obj as Record<string, unknown>)[key]);
    }
    return result as T;
  }
  return obj as T;
}

// Session
export function useCreateSession() {
  const setSession = useSessionStore((s) => s.setSession);
  const setInitializing = useSessionStore((s) => s.setInitializing);
  const setError = useSessionStore((s) => s.setError);

  return useMutation({
    mutationFn: async () => {
      setInitializing(true);
      const response = await apiClient.post('/api/v1/session');
      // Transform snake_case response to camelCase
      return toCamelCase<Session>(response.data);
    },
    onSuccess: (data) => {
      setSession(data);
      setInitializing(false);
    },
    onError: (error: Error) => {
      setError(error.message);
      setInitializing(false);
    },
  });
}

// Resume Upload
export function useUploadResume() {
  const setResume = useAnalysisStore((s) => s.setResume);
  const setCanProceed = useWizardStore((s) => s.setCanProceed);
  const session = useSessionStore((s) => s.session);

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      if (session) {
        formData.append('session_id', session.sessionId);
      }

      const response = await apiClient.post(
        '/api/v1/upload/resume',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 300000, // 5 minutes for LLM processing
        }
      );
      return toCamelCase<ResumeUploadResponse>(response.data);
    },
    onSuccess: (data) => {
      setResume({
        id: data.resumeId,
        skills: data.skills,
        experiences: data.experiences,
        education: data.education,
        certifications: [],
        summary: data.summary,
        contactRedacted: data.piiRedacted,
      });
      setCanProceed(true);
    },
  });
}

// Job Description Upload
export function useUploadJobDescription() {
  const addJob = useAnalysisStore((s) => s.addJob);

  return useMutation({
    mutationFn: async (content: string) => {
      const response = await apiClient.post(
        '/api/v1/upload/job-description',
        { text: content }, // Backend expects "text" field
        { timeout: 120000 } // 2 minutes for LLM processing
      );
      return toCamelCase<JobDescriptionUploadResponse>(response.data);
    },
    onSuccess: (data) => {
      addJob({
        id: data.jobId,
        title: data.title,
        company: data.company,
        requirements: data.requirements,
        requiredSkills: data.requiredSkills,
        niceToHaveSkills: data.niceToHaveSkills,
        educationRequirements: [],
        responsibilities: [],
        cultureSignals: [],
      });
    },
  });
}

// Analysis
export function useStartAnalysis() {
  const session = useSessionStore((s) => s.session);
  const setAnalyzing = useWizardStore((s) => s.setAnalyzing);

  return useMutation({
    mutationFn: async () => {
      setAnalyzing(true);
      const response = await apiClient.post<AnalysisStartedResponse>(
        '/api/v1/analyze',
        { session_id: session?.sessionId }
      );
      return response.data;
    },
  });
}

export function useAnalysisResults(sessionId: string | null, enabled = false) {
  const setAnalysisResult = useAnalysisStore((s) => s.setAnalysisResult);
  const setAnalyzing = useWizardStore((s) => s.setAnalyzing);
  const setCanProceed = useWizardStore((s) => s.setCanProceed);

  return useQuery({
    queryKey: ['analysis', sessionId],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/results/${sessionId}`);
      // Transform snake_case to camelCase
      const data = toCamelCase<AnalysisResult>(response.data);
      // Handle side effects here instead of onSuccess
      if (data.status === 'completed') {
        setAnalysisResult(data);
        setAnalyzing(false);
        setCanProceed(true);
      }
      return data;
    },
    enabled: enabled && !!sessionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000;
    },
  });
}

// Recommendations
export function useRecommendations(sessionId: string | null, jobId: string | null) {
  return useQuery({
    queryKey: ['recommendations', sessionId, jobId],
    queryFn: async (): Promise<RecommendationResult> => {
      const url = jobId
        ? `/api/v1/recommendations/${sessionId}?job_id=${jobId}`
        : `/api/v1/recommendations/${sessionId}`;
      const response = await apiClient.get(url);
      return toCamelCase<RecommendationResult>(response.data);
    },
    enabled: !!sessionId,
  });
}

// Interview Prep
export function useInterviewPrep(sessionId: string | null, jobId: string | null) {
  return useQuery({
    queryKey: ['interview-prep', sessionId, jobId],
    queryFn: async (): Promise<InterviewPrepResult> => {
      const url = jobId
        ? `/api/v1/interview-prep/${sessionId}?job_id=${jobId}`
        : `/api/v1/interview-prep/${sessionId}`;
      const response = await apiClient.get(url);
      return toCamelCase<InterviewPrepResult>(response.data);
    },
    enabled: !!sessionId,
  });
}

// Market Insights
export function useMarketInsights(sessionId: string | null, jobId: string | null) {
  return useQuery({
    queryKey: ['market-insights', sessionId, jobId],
    queryFn: async (): Promise<MarketInsightsResult> => {
      const url = jobId
        ? `/api/v1/market-insights/${sessionId}?job_id=${jobId}`
        : `/api/v1/market-insights/${sessionId}`;
      const response = await apiClient.get(url);
      return toCamelCase<MarketInsightsResult>(response.data);
    },
    enabled: !!sessionId,
  });
}

// Chat
export function useChatMutation() {
  return useMutation({
    mutationFn: async (request: ChatRequest): Promise<ChatResponse> => {
      const response = await apiClient.post('/api/v1/chat', {
        message: request.message,
        job_id: request.jobId,
      }, {
        timeout: 60000, // 1 minute for chat response
      });
      return toCamelCase<ChatResponse>(response.data);
    },
  });
}
