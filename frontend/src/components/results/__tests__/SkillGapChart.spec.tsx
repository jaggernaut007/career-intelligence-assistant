import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { SkillGapChart } from '../SkillGapChart';
import { JobMatch } from '../../../types/specs';

// ResizeObserver mock needed for Recharts
(globalThis as any).ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any;

describe('SkillGapChart', () => {
  const mockJobMatch: JobMatch = {
    jobId: '1',
    resumeId: '1',
    jobTitle: 'Frontend Engineer',
    fitScore: 75,
    skillMatchScore: 70,
    experienceMatchScore: 80,
    educationMatchScore: 90,
    matchingSkills: [
      { skillName: 'React', resumeLevel: 'expert', requiredLevel: 'advanced', matchQuality: 'exceeds' },
      { skillName: 'CSS', resumeLevel: 'advanced', requiredLevel: 'advanced', matchQuality: 'exact' }
    ],
    missingSkills: [
      { skillName: 'Docker', importance: 'must_have', difficultyToAcquire: 'medium' }
    ],
    transferableSkills: []
  };

  it('renders graph title', () => {
    render(<SkillGapChart jobMatch={mockJobMatch} />);
    expect(screen.getByText('Skill Alignment Analysis')).toBeInTheDocument();
  });

  it('renders empty state when no skills provided', () => {
      const emptyMatch = { ...mockJobMatch, matchingSkills: [], missingSkills: [] };
      render(<SkillGapChart jobMatch={emptyMatch} />);
      expect(screen.getByText('No skill data available to chart.')).toBeInTheDocument();
  });
  
  // Note: Testing actual SVG rendering of Recharts is complex and usually requires integration tests or visual diffs.
  // We check if the container renders without crashing for unit tests.
});
