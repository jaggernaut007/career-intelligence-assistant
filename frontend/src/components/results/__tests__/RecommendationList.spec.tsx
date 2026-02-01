import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { RecommendationList } from '../RecommendationList';
import { Recommendation } from '../../../types/specs';

describe('RecommendationList', () => {
  const mockRecommendations: Recommendation[] = [
    {
      id: '1',
      category: 'skill_gap',
      priority: 'high',
      title: 'Learn Docker',
      description: 'Docker is a must-have skill for this role.',
      actionItems: ['Take a course', 'Build a container'],
      resources: ['https://docker.com'],
      estimatedTime: '2 weeks'
    },
    {
      id: '2',
      category: 'resume_improvement',
      priority: 'medium',
      title: 'Quantify Impact',
      description: 'Add numbers to your experience.',
      actionItems: ['Review bullet points'],
      resources: []
    }
  ];

  it('renders recommendations', () => {
    render(<RecommendationList recommendations={mockRecommendations} />);
    expect(screen.getByText('Learn Docker')).toBeInTheDocument();
    expect(screen.getByText('Quantify Impact')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    render(<RecommendationList recommendations={[]} />);
    expect(screen.getByText(/No recommendations available/i)).toBeInTheDocument();
  });

  it('displays correct priority badges', () => {
    render(<RecommendationList recommendations={mockRecommendations} />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  it('displays action items', () => {
    render(<RecommendationList recommendations={mockRecommendations} />);
     expect(screen.getByText('Take a course')).toBeInTheDocument();
  });
});
