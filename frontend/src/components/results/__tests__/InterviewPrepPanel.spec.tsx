import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { InterviewPrepPanel } from '../InterviewPrepPanel';
import { InterviewQuestion } from '../../../types/specs';

describe('InterviewPrepPanel', () => {
  const mockQuestions: InterviewQuestion[] = [
    {
      id: '1',
      question: 'Tell me about a challenge you faced.',
      category: 'behavioral',
      difficulty: 'medium',
      whyAsked: 'To assess problem solving.',
      suggestedAnswer: 'Focus on the solution.',
      starExample: {
        situation: 'Database crashed',
        task: 'Restore it',
        action: 'Used backups',
        result: 'Restored in 1 hour'
      }
    }
  ];

  it('renders questions collapsed initially', () => {
    render(<InterviewPrepPanel questions={mockQuestions} />);
    expect(screen.getByText('Tell me about a challenge you faced.')).toBeInTheDocument();
    expect(screen.queryByText('Why they ask this:')).not.toBeInTheDocument();
  });

  it('expands question on click', () => {
    render(<InterviewPrepPanel questions={mockQuestions} />);
    const card = screen.getByText('Tell me about a challenge you faced.');
    fireEvent.click(card);
    expect(screen.getByText('Why they ask this:')).toBeInTheDocument();
    expect(screen.getByText('To assess problem solving.')).toBeInTheDocument();
  });

  it('shows STAR example when expanded', () => {
    render(<InterviewPrepPanel questions={mockQuestions} />);
    const card = screen.getByText('Tell me about a challenge you faced.');
    fireEvent.click(card);
    expect(screen.getByText('STAR Method Example')).toBeInTheDocument();
    expect(screen.getByText('Database crashed')).toBeInTheDocument();
  });
});
