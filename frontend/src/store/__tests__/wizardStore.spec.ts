/**
 * Tests for wizardStore.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useWizardStore } from '../wizardStore';
import type { WizardStep, AgentStatusUpdate } from '@/types/specs';

describe('wizardStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useWizardStore.getState().reset();
  });

  describe('Initial State', () => {
    it('starts at step 1', () => {
      expect(useWizardStore.getState().currentStep).toBe(1);
    });

    it('cannot proceed initially', () => {
      expect(useWizardStore.getState().canProceed).toBe(false);
    });

    it('is not analyzing initially', () => {
      expect(useWizardStore.getState().isAnalyzing).toBe(false);
    });

    it('has empty agent statuses', () => {
      expect(useWizardStore.getState().agentStatuses).toEqual([]);
    });

    it('has no error initially', () => {
      expect(useWizardStore.getState().error).toBeNull();
    });
  });

  describe('setStep', () => {
    it('sets current step', () => {
      useWizardStore.getState().setStep(3);
      expect(useWizardStore.getState().currentStep).toBe(3);
    });

    it('resets canProceed when step changes', () => {
      useWizardStore.setState({ canProceed: true });
      useWizardStore.getState().setStep(2);
      expect(useWizardStore.getState().canProceed).toBe(false);
    });
  });

  describe('nextStep', () => {
    it('advances to next step when canProceed is true', () => {
      useWizardStore.setState({ canProceed: true });
      useWizardStore.getState().nextStep();
      expect(useWizardStore.getState().currentStep).toBe(2);
    });

    it('does not advance when canProceed is false', () => {
      useWizardStore.getState().nextStep();
      expect(useWizardStore.getState().currentStep).toBe(1);
    });

    it('does not advance past step 4', () => {
      useWizardStore.setState({ currentStep: 4, canProceed: true });
      useWizardStore.getState().nextStep();
      expect(useWizardStore.getState().currentStep).toBe(4);
    });

    it('resets canProceed after advancing', () => {
      useWizardStore.setState({ canProceed: true });
      useWizardStore.getState().nextStep();
      expect(useWizardStore.getState().canProceed).toBe(false);
    });

    it('advances through all steps', () => {
      for (let i = 1; i < 4; i++) {
        useWizardStore.setState({ canProceed: true });
        useWizardStore.getState().nextStep();
        expect(useWizardStore.getState().currentStep).toBe((i + 1) as WizardStep);
      }
    });
  });

  describe('prevStep', () => {
    it('goes to previous step', () => {
      useWizardStore.setState({ currentStep: 3 });
      useWizardStore.getState().prevStep();
      expect(useWizardStore.getState().currentStep).toBe(2);
    });

    it('does not go below step 1', () => {
      useWizardStore.getState().prevStep();
      expect(useWizardStore.getState().currentStep).toBe(1);
    });

    it('goes back through all steps', () => {
      useWizardStore.setState({ currentStep: 4 });
      for (let i = 4; i > 1; i--) {
        useWizardStore.getState().prevStep();
        expect(useWizardStore.getState().currentStep).toBe((i - 1) as WizardStep);
      }
    });
  });

  describe('setCanProceed', () => {
    it('sets canProceed to true', () => {
      useWizardStore.getState().setCanProceed(true);
      expect(useWizardStore.getState().canProceed).toBe(true);
    });

    it('sets canProceed to false', () => {
      useWizardStore.setState({ canProceed: true });
      useWizardStore.getState().setCanProceed(false);
      expect(useWizardStore.getState().canProceed).toBe(false);
    });
  });

  describe('setAnalyzing', () => {
    it('sets analyzing to true', () => {
      useWizardStore.getState().setAnalyzing(true);
      expect(useWizardStore.getState().isAnalyzing).toBe(true);
    });

    it('sets analyzing to false', () => {
      useWizardStore.setState({ isAnalyzing: true });
      useWizardStore.getState().setAnalyzing(false);
      expect(useWizardStore.getState().isAnalyzing).toBe(false);
    });
  });

  describe('updateAgentStatus', () => {
    const mockStatus: AgentStatusUpdate = {
      agentName: 'resume_parser',
      status: 'running',
      progress: 50,
      currentStep: 'Parsing skills',
    };

    it('adds new agent status', () => {
      useWizardStore.getState().updateAgentStatus(mockStatus);
      expect(useWizardStore.getState().agentStatuses).toHaveLength(1);
      expect(useWizardStore.getState().agentStatuses[0]).toEqual(mockStatus);
    });

    it('updates existing agent status', () => {
      useWizardStore.getState().updateAgentStatus(mockStatus);

      const updatedStatus: AgentStatusUpdate = {
        agentName: 'resume_parser',
        status: 'completed',
        progress: 100,
        currentStep: 'Done',
      };
      useWizardStore.getState().updateAgentStatus(updatedStatus);

      expect(useWizardStore.getState().agentStatuses).toHaveLength(1);
      expect(useWizardStore.getState().agentStatuses[0]).toEqual(updatedStatus);
    });

    it('handles multiple agents', () => {
      const agent1: AgentStatusUpdate = {
        agentName: 'resume_parser',
        status: 'completed',
        progress: 100,
      };
      const agent2: AgentStatusUpdate = {
        agentName: 'job_analyzer',
        status: 'running',
        progress: 30,
      };

      useWizardStore.getState().updateAgentStatus(agent1);
      useWizardStore.getState().updateAgentStatus(agent2);

      expect(useWizardStore.getState().agentStatuses).toHaveLength(2);
    });

    it('updates correct agent when multiple exist', () => {
      const agent1: AgentStatusUpdate = {
        agentName: 'resume_parser',
        status: 'running',
        progress: 50,
      };
      const agent2: AgentStatusUpdate = {
        agentName: 'job_analyzer',
        status: 'pending',
        progress: 0,
      };

      useWizardStore.getState().updateAgentStatus(agent1);
      useWizardStore.getState().updateAgentStatus(agent2);

      const updatedAgent1: AgentStatusUpdate = {
        agentName: 'resume_parser',
        status: 'completed',
        progress: 100,
      };
      useWizardStore.getState().updateAgentStatus(updatedAgent1);

      const statuses = useWizardStore.getState().agentStatuses;
      expect(statuses.find((s) => s.agentName === 'resume_parser')?.status).toBe('completed');
      expect(statuses.find((s) => s.agentName === 'job_analyzer')?.status).toBe('pending');
    });
  });

  describe('clearAgentStatuses', () => {
    it('clears all agent statuses', () => {
      useWizardStore.setState({
        agentStatuses: [
          { agentName: 'agent1', status: 'completed', progress: 100 },
          { agentName: 'agent2', status: 'running', progress: 50 },
        ],
      });

      useWizardStore.getState().clearAgentStatuses();
      expect(useWizardStore.getState().agentStatuses).toEqual([]);
    });
  });

  describe('setError', () => {
    it('sets error message', () => {
      useWizardStore.getState().setError('Something went wrong');
      expect(useWizardStore.getState().error).toBe('Something went wrong');
    });

    it('clears error with null', () => {
      useWizardStore.setState({ error: 'Some error' });
      useWizardStore.getState().setError(null);
      expect(useWizardStore.getState().error).toBeNull();
    });
  });

  describe('reset', () => {
    it('resets all state to initial values', () => {
      // Set various state values
      useWizardStore.setState({
        currentStep: 3,
        canProceed: true,
        isAnalyzing: true,
        agentStatuses: [{ agentName: 'test', status: 'running', progress: 50 }],
        error: 'Some error',
      });

      useWizardStore.getState().reset();

      expect(useWizardStore.getState().currentStep).toBe(1);
      expect(useWizardStore.getState().canProceed).toBe(false);
      expect(useWizardStore.getState().isAnalyzing).toBe(false);
      expect(useWizardStore.getState().agentStatuses).toEqual([]);
      expect(useWizardStore.getState().error).toBeNull();
    });
  });
});
