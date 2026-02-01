import { create } from 'zustand';
import type { WizardStep, AgentStatusUpdate } from '@/types/specs';

interface WizardStore {
  currentStep: WizardStep;
  canProceed: boolean;
  isAnalyzing: boolean;
  agentStatuses: AgentStatusUpdate[];
  error: string | null;

  setStep: (step: WizardStep) => void;
  nextStep: () => void;
  prevStep: () => void;
  setCanProceed: (can: boolean) => void;
  setAnalyzing: (analyzing: boolean) => void;
  updateAgentStatus: (update: AgentStatusUpdate) => void;
  clearAgentStatuses: () => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 1 as WizardStep,
  canProceed: false,
  isAnalyzing: false,
  agentStatuses: [],
  error: null,
};

export const useWizardStore = create<WizardStore>((set) => ({
  ...initialState,

  setStep: (step) => set({ currentStep: step, canProceed: false }),

  nextStep: () =>
    set((state) => {
      if (state.currentStep < 4 && state.canProceed) {
        return { currentStep: (state.currentStep + 1) as WizardStep, canProceed: false };
      }
      return state;
    }),

  prevStep: () =>
    set((state) => {
      if (state.currentStep > 1) {
        return { currentStep: (state.currentStep - 1) as WizardStep };
      }
      return state;
    }),

  setCanProceed: (canProceed) => set({ canProceed }),

  setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

  updateAgentStatus: (update) =>
    set((state) => {
      const existingIndex = state.agentStatuses.findIndex(
        (s) => s.agentName === update.agentName
      );
      if (existingIndex >= 0) {
        const newStatuses = [...state.agentStatuses];
        newStatuses[existingIndex] = update;
        return { agentStatuses: newStatuses };
      }
      return { agentStatuses: [...state.agentStatuses, update] };
    }),

  clearAgentStatuses: () => set({ agentStatuses: [] }),

  setError: (error) => set({ error }),

  reset: () => set(initialState),
}));
