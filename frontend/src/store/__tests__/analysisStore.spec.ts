/**
 * Tests for analysisStore.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useAnalysisStore } from '../analysisStore';
import type {
  ParsedResume,
  ParsedJobDescription,
  AnalysisResult,
  RecommendationResult,
  InterviewPrepResult,
  MarketInsightsResult,
} from '@/types/specs';

describe('analysisStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAnalysisStore.getState().clearAll();
  });

  const mockResume: ParsedResume = {
    id: 'resume-1',
    skills: [{ name: 'TypeScript', category: 'programming', level: 'advanced' }],
    experiences: [
      {
        title: 'Software Engineer',
        company: 'Tech Corp',
        duration: '2 years',
        skillsUsed: ['TypeScript'],
      },
    ],
    education: [{ degree: 'BS Computer Science', institution: 'MIT' }],
    certifications: ['AWS Certified'],
    summary: 'Experienced developer',
    contactRedacted: true,
  };

  const mockJob: ParsedJobDescription = {
    id: 'job-1',
    title: 'Senior Developer',
    company: 'Big Tech',
    requirements: [],
    requiredSkills: [{ name: 'TypeScript', category: 'programming', level: 'advanced' }],
    niceToHaveSkills: [],
    educationRequirements: [],
    responsibilities: [],
    cultureSignals: [],
  };

  describe('Initial State', () => {
    it('has null resume initially', () => {
      expect(useAnalysisStore.getState().resume).toBeNull();
    });

    it('has empty job descriptions initially', () => {
      expect(useAnalysisStore.getState().jobDescriptions).toEqual([]);
    });

    it('has null analysis result initially', () => {
      expect(useAnalysisStore.getState().analysisResult).toBeNull();
    });

    it('has null selected job initially', () => {
      expect(useAnalysisStore.getState().selectedJobId).toBeNull();
    });

    it('has null recommendations initially', () => {
      expect(useAnalysisStore.getState().recommendations).toBeNull();
    });

    it('has null interview prep initially', () => {
      expect(useAnalysisStore.getState().interviewPrep).toBeNull();
    });

    it('has null market insights initially', () => {
      expect(useAnalysisStore.getState().marketInsights).toBeNull();
    });
  });

  describe('setResume', () => {
    it('sets the resume', () => {
      useAnalysisStore.getState().setResume(mockResume);
      expect(useAnalysisStore.getState().resume).toEqual(mockResume);
    });
  });

  describe('addJob', () => {
    it('adds a job description', () => {
      useAnalysisStore.getState().addJob(mockJob);
      expect(useAnalysisStore.getState().jobDescriptions).toHaveLength(1);
      expect(useAnalysisStore.getState().jobDescriptions[0]).toEqual(mockJob);
    });

    it('adds multiple job descriptions', () => {
      const job1 = { ...mockJob, id: 'job-1' };
      const job2 = { ...mockJob, id: 'job-2', title: 'Frontend Developer' };

      useAnalysisStore.getState().addJob(job1);
      useAnalysisStore.getState().addJob(job2);

      expect(useAnalysisStore.getState().jobDescriptions).toHaveLength(2);
    });

    it('limits to 5 job descriptions', () => {
      for (let i = 1; i <= 6; i++) {
        useAnalysisStore.getState().addJob({ ...mockJob, id: `job-${i}` });
      }

      expect(useAnalysisStore.getState().jobDescriptions).toHaveLength(5);
    });

    it('ignores job when at limit', () => {
      for (let i = 1; i <= 5; i++) {
        useAnalysisStore.getState().addJob({ ...mockJob, id: `job-${i}` });
      }

      useAnalysisStore.getState().addJob({ ...mockJob, id: 'job-6', title: 'New Job' });

      const jobs = useAnalysisStore.getState().jobDescriptions;
      expect(jobs.find((j) => j.id === 'job-6')).toBeUndefined();
    });
  });

  describe('removeJob', () => {
    it('removes a job description', () => {
      useAnalysisStore.getState().addJob(mockJob);
      useAnalysisStore.getState().removeJob('job-1');
      expect(useAnalysisStore.getState().jobDescriptions).toHaveLength(0);
    });

    it('removes correct job when multiple exist', () => {
      const job1 = { ...mockJob, id: 'job-1' };
      const job2 = { ...mockJob, id: 'job-2' };
      useAnalysisStore.getState().addJob(job1);
      useAnalysisStore.getState().addJob(job2);

      useAnalysisStore.getState().removeJob('job-1');

      expect(useAnalysisStore.getState().jobDescriptions).toHaveLength(1);
      expect(useAnalysisStore.getState().jobDescriptions[0].id).toBe('job-2');
    });

    it('clears selectedJobId if removed job was selected', () => {
      useAnalysisStore.getState().addJob(mockJob);
      useAnalysisStore.setState({ selectedJobId: 'job-1' });

      useAnalysisStore.getState().removeJob('job-1');

      expect(useAnalysisStore.getState().selectedJobId).toBeNull();
    });

    it('keeps selectedJobId if different job is removed', () => {
      const job1 = { ...mockJob, id: 'job-1' };
      const job2 = { ...mockJob, id: 'job-2' };
      useAnalysisStore.getState().addJob(job1);
      useAnalysisStore.getState().addJob(job2);
      useAnalysisStore.setState({ selectedJobId: 'job-2' });

      useAnalysisStore.getState().removeJob('job-1');

      expect(useAnalysisStore.getState().selectedJobId).toBe('job-2');
    });

    it('handles removing non-existent job', () => {
      useAnalysisStore.getState().addJob(mockJob);
      useAnalysisStore.getState().removeJob('non-existent');
      expect(useAnalysisStore.getState().jobDescriptions).toHaveLength(1);
    });
  });

  describe('setAnalysisResult', () => {
    const mockResult: AnalysisResult = {
      sessionId: 'session-1',
      status: 'completed',
      jobMatches: [
        {
          jobId: 'job-1',
          resumeId: 'resume-1',
          jobTitle: 'Senior Developer',
          fitScore: 85,
          skillMatchScore: 90,
          experienceMatchScore: 80,
          educationMatchScore: 75,
          matchingSkills: [],
          missingSkills: [],
          transferableSkills: [],
        },
      ],
    };

    it('sets the analysis result', () => {
      useAnalysisStore.getState().setAnalysisResult(mockResult);
      expect(useAnalysisStore.getState().analysisResult).toEqual(mockResult);
    });

    it('sets selectedJobId to first job match', () => {
      useAnalysisStore.getState().setAnalysisResult(mockResult);
      expect(useAnalysisStore.getState().selectedJobId).toBe('job-1');
    });

    it('handles empty job matches', () => {
      const emptyResult: AnalysisResult = {
        sessionId: 'session-1',
        status: 'completed',
        jobMatches: [],
      };

      useAnalysisStore.getState().setAnalysisResult(emptyResult);
      expect(useAnalysisStore.getState().selectedJobId).toBeNull();
    });
  });

  describe('setSelectedJob', () => {
    it('sets selected job id', () => {
      useAnalysisStore.getState().setSelectedJob('job-123');
      expect(useAnalysisStore.getState().selectedJobId).toBe('job-123');
    });

    it('clears selected job with null', () => {
      useAnalysisStore.setState({ selectedJobId: 'job-123' });
      useAnalysisStore.getState().setSelectedJob(null);
      expect(useAnalysisStore.getState().selectedJobId).toBeNull();
    });
  });

  describe('setRecommendations', () => {
    const mockRecommendations: RecommendationResult = {
      sessionId: 'session-1',
      recommendations: [
        {
          id: 'rec-1',
          category: 'skill_gap',
          priority: 'high',
          title: 'Learn React',
          description: 'Improve React skills',
          actionItems: ['Take course'],
          resources: ['reactjs.org'],
        },
      ],
      priorityOrder: ['rec-1'],
    };

    it('sets recommendations', () => {
      useAnalysisStore.getState().setRecommendations(mockRecommendations);
      expect(useAnalysisStore.getState().recommendations).toEqual(mockRecommendations);
    });
  });

  describe('setInterviewPrep', () => {
    const mockInterviewPrep: InterviewPrepResult = {
      sessionId: 'session-1',
      questions: [
        {
          id: 'q-1',
          question: 'Tell me about yourself',
          category: 'behavioral',
          difficulty: 'easy',
          suggestedAnswer: 'Start with your background...',
        },
      ],
      talkingPoints: ['Experience with TypeScript'],
      weaknessResponses: [],
      questionsToAsk: ['What is the team structure?'],
    };

    it('sets interview prep', () => {
      useAnalysisStore.getState().setInterviewPrep(mockInterviewPrep);
      expect(useAnalysisStore.getState().interviewPrep).toEqual(mockInterviewPrep);
    });
  });

  describe('setMarketInsights', () => {
    const mockMarketInsights: MarketInsightsResult = {
      sessionId: 'session-1',
      insights: {
        salaryRange: { min: 100000, max: 150000, median: 125000, currency: 'USD', locationAdjusted: true },
        demandTrend: 'increasing',
        topSkillsInDemand: ['TypeScript', 'React'],
        careerPaths: [],
        industryInsights: 'Tech industry is growing',
        dataFreshness: '2024-01',
      },
    };

    it('sets market insights', () => {
      useAnalysisStore.getState().setMarketInsights(mockMarketInsights);
      expect(useAnalysisStore.getState().marketInsights).toEqual(mockMarketInsights);
    });
  });

  describe('clearAll', () => {
    it('clears all state to initial values', () => {
      // Set various state values
      useAnalysisStore.setState({
        resume: mockResume,
        jobDescriptions: [mockJob],
        selectedJobId: 'job-1',
        analysisResult: {
          sessionId: 'session-1',
          status: 'completed',
          jobMatches: [],
        },
        recommendations: {
          sessionId: 'session-1',
          recommendations: [],
          priorityOrder: [],
        },
        interviewPrep: {
          sessionId: 'session-1',
          questions: [],
          talkingPoints: [],
          weaknessResponses: [],
          questionsToAsk: [],
        },
        marketInsights: {
          sessionId: 'session-1',
          insights: {
            salaryRange: { min: 0, max: 0, median: 0, currency: 'USD', locationAdjusted: false },
            demandTrend: 'stable',
            topSkillsInDemand: [],
            careerPaths: [],
            industryInsights: '',
            dataFreshness: '',
          },
        },
      });

      useAnalysisStore.getState().clearAll();

      expect(useAnalysisStore.getState().resume).toBeNull();
      expect(useAnalysisStore.getState().jobDescriptions).toEqual([]);
      expect(useAnalysisStore.getState().analysisResult).toBeNull();
      expect(useAnalysisStore.getState().selectedJobId).toBeNull();
      expect(useAnalysisStore.getState().recommendations).toBeNull();
      expect(useAnalysisStore.getState().interviewPrep).toBeNull();
      expect(useAnalysisStore.getState().marketInsights).toBeNull();
    });
  });
});
