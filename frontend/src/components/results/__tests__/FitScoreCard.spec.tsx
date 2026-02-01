import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { FitScoreCard } from '../FitScoreCard';
import { JobMatch } from '../../../types/specs';

describe('FitScoreCard', () => {
  const mockJobMatch: JobMatch = {
    jobId: '1',
    resumeId: '1',
    jobTitle: 'Senior Software Engineer',
    company: 'Tech Corp',
    fitScore: 85,
    skillMatchScore: 80,
    experienceMatchScore: 90,
    educationMatchScore: 100,
    matchingSkills: [
      { skillName: 'React', resumeLevel: 'expert', requiredLevel: 'advanced', matchQuality: 'exact' },
      { skillName: 'TypeScript', resumeLevel: 'intermediate', requiredLevel: 'intermediate', matchQuality: 'exact' },
      { skillName: 'Node.js', resumeLevel: 'beginner', requiredLevel: 'intermediate', matchQuality: 'partial' }
    ],
    missingSkills: [
      { skillName: 'Kubernetes', importance: 'must_have', difficultyToAcquire: 'hard' },
      { skillName: 'GraphQL', importance: 'nice_to_have', difficultyToAcquire: 'medium' }
    ],
    transferableSkills: []
  };

  it('renders job title and company', () => {
    render(<FitScoreCard jobMatch={mockJobMatch} />);
    expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
  });

  it('renders fit score', () => {
    render(<FitScoreCard jobMatch={mockJobMatch} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders matching skills', () => {
    render(<FitScoreCard jobMatch={mockJobMatch} />);
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
    expect(screen.getByText('Node.js (Partial)')).toBeInTheDocument();
  });

  it('renders missing skills', () => {
    render(<FitScoreCard jobMatch={mockJobMatch} />);
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('GraphQL')).toBeInTheDocument();
  });

  it('handles empty missing skills gracefully', () => {
    const perfectMatch = { ...mockJobMatch, missingSkills: [] };
    render(<FitScoreCard jobMatch={perfectMatch} />);
    expect(screen.getByText('No missing skills!')).toBeInTheDocument();
  });
  
    it('handles empty matching skills gracefully', () => {
    const noMatch = { ...mockJobMatch, matchingSkills: [] };
    render(<FitScoreCard jobMatch={noMatch} />);
    expect(screen.getByText('No exact matches yet.')).toBeInTheDocument();
  });
});
