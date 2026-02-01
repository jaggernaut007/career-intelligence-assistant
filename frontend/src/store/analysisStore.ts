import { create } from 'zustand';
import type {
  ParsedResume,
  ParsedJobDescription,
  AnalysisResult,
  RecommendationResult,
  InterviewPrepResult,
  MarketInsightsResult,
} from '@/types/specs';

interface AnalysisStore {
  resume: ParsedResume | null;
  jobDescriptions: ParsedJobDescription[];
  analysisResult: AnalysisResult | null;
  selectedJobId: string | null;
  recommendations: RecommendationResult | null;
  interviewPrep: InterviewPrepResult | null;
  marketInsights: MarketInsightsResult | null;

  setResume: (resume: ParsedResume) => void;
  addJob: (job: ParsedJobDescription) => boolean;
  removeJob: (jobId: string) => void;
  setAnalysisResult: (result: AnalysisResult) => void;
  setSelectedJob: (jobId: string | null) => void;
  setRecommendations: (recommendations: RecommendationResult) => void;
  setInterviewPrep: (interviewPrep: InterviewPrepResult) => void;
  setMarketInsights: (marketInsights: MarketInsightsResult) => void;
  clearAll: () => void;
}

const initialState = {
  resume: null,
  jobDescriptions: [],
  analysisResult: null,
  selectedJobId: null,
  recommendations: null,
  interviewPrep: null,
  marketInsights: null,
};

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  ...initialState,

  setResume: (resume) => set({ resume }),

  addJob: (job) => {
    const state = useAnalysisStore.getState();
    if (state.jobDescriptions.length >= 5) {
      return false;
    }
    set({ jobDescriptions: [...state.jobDescriptions, job] });
    return true;
  },

  removeJob: (jobId) =>
    set((state) => ({
      jobDescriptions: state.jobDescriptions.filter((j) => j.id !== jobId),
      selectedJobId: state.selectedJobId === jobId ? null : state.selectedJobId,
    })),

  setAnalysisResult: (result) =>
    set({
      analysisResult: result,
      selectedJobId: result.jobMatches[0]?.jobId || null,
    }),

  setSelectedJob: (jobId) => set({ selectedJobId: jobId }),

  setRecommendations: (recommendations) => set({ recommendations }),

  setInterviewPrep: (interviewPrep) => set({ interviewPrep }),

  setMarketInsights: (marketInsights) => set({ marketInsights }),

  clearAll: () => set(initialState),
}));
