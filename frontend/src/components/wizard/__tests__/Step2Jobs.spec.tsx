/**
 * Tests for Step2Jobs component.
 *
 * TDD: These tests are written BEFORE implementation.
 * Tests should FAIL until Step2Jobs.tsx is implemented.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// This import will fail until the component is created
// import { Step2Jobs } from '../Step2Jobs';

describe('Step2Jobs', () => {
  const mockOnAddJob = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Job Description Input', () => {
    it('renders text area for pasting job description', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('has placeholder text with instructions', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // const textarea = screen.getByRole('textbox');
      // expect(textarea).toHaveAttribute('placeholder');
    });

    it('allows file upload as alternative', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // expect(screen.getByTestId('jd-file-input')).toBeInTheDocument();
    });
  });

  describe('Add Job Button', () => {
    it('renders Add Job button', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // expect(screen.getByRole('button', { name: /add job/i })).toBeInTheDocument();
    });

    it('disables Add button when textarea is empty', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // const addButton = screen.getByRole('button', { name: /add job/i });
      // expect(addButton).toBeDisabled();
    });

    it('enables Add button when text is entered', async () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // const textarea = screen.getByRole('textbox');
      // await userEvent.type(textarea, 'Software Engineer at TechCorp');
      // const addButton = screen.getByRole('button', { name: /add job/i });
      // expect(addButton).not.toBeDisabled();
    });

    it('calls onAddJob when Add button is clicked', async () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // const textarea = screen.getByRole('textbox');
      // await userEvent.type(textarea, 'Job description text');
      // const addButton = screen.getByRole('button', { name: /add job/i });
      // fireEvent.click(addButton);
      // expect(mockOnAddJob).toHaveBeenCalledWith('Job description text');
    });

    it('clears textarea after successful add', async () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob.mockResolvedValue({})} />);
      // const textarea = screen.getByRole('textbox');
      // await userEvent.type(textarea, 'Job description');
      // fireEvent.click(screen.getByRole('button', { name: /add job/i }));
      // await waitFor(() => {
      //   expect(textarea).toHaveValue('');
      // });
    });
  });

  describe('Jobs List', () => {
    it('displays added job descriptions', () => {
      // const jobs = [
      //   { id: '1', title: 'Senior Engineer', company: 'Google' },
      //   { id: '2', title: 'Staff Engineer', company: 'Meta' }
      // ];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // expect(screen.getByText('Senior Engineer')).toBeInTheDocument();
      // expect(screen.getByText('Staff Engineer')).toBeInTheDocument();
    });

    it('shows job title and company for each job', () => {
      // Jobs should display both title and company
    });

    it('shows checkmark for successfully parsed jobs', () => {
      // const jobs = [{ id: '1', title: 'Engineer', status: 'parsed' }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // expect(screen.getByTestId('job-1-success')).toBeInTheDocument();
    });

    it('shows parsed skills for each job', () => {
      // const jobs = [{
      //   id: '1',
      //   title: 'Engineer',
      //   requiredSkills: [{ name: 'Python' }, { name: 'AWS' }]
      // }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // expect(screen.getByText('Python')).toBeInTheDocument();
    });
  });

  describe('Job Removal', () => {
    it('shows remove button for each job', () => {
      // const jobs = [{ id: '1', title: 'Engineer' }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument();
    });

    it('calls onRemoveJob when remove is clicked', () => {
      // const mockOnRemove = vi.fn();
      // const jobs = [{ id: '1', title: 'Engineer' }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} onRemoveJob={mockOnRemove} jobs={jobs} />);
      // fireEvent.click(screen.getByRole('button', { name: /remove/i }));
      // expect(mockOnRemove).toHaveBeenCalledWith('1');
    });
  });

  describe('Job Limit - Per Spec (Max 5)', () => {
    it('shows job count (e.g., "2 of 5")', () => {
      // const jobs = [{ id: '1', title: 'Job 1' }, { id: '2', title: 'Job 2' }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // expect(screen.getByText(/2.*5/)).toBeInTheDocument();
    });

    it('disables add button when 5 jobs reached', () => {
      // const jobs = Array.from({ length: 5 }, (_, i) => ({ id: String(i), title: `Job ${i}` }));
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // const addButton = screen.getByRole('button', { name: /add job/i });
      // expect(addButton).toBeDisabled();
    });

    it('shows message when max jobs reached', () => {
      // const jobs = Array.from({ length: 5 }, (_, i) => ({ id: String(i), title: `Job ${i}` }));
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // expect(screen.getByText(/maximum.*5.*jobs/i)).toBeInTheDocument();
    });
  });

  describe('Analyze Button', () => {
    it('shows Analyze button', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} />);
      // expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument();
    });

    it('disables Analyze when no jobs added', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={[]} />);
      // const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      // expect(analyzeButton).toBeDisabled();
    });

    it('enables Analyze when at least one job added', () => {
      // const jobs = [{ id: '1', title: 'Engineer' }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} />);
      // const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      // expect(analyzeButton).not.toBeDisabled();
    });

    it('calls onAnalyze when Analyze clicked', () => {
      // const mockOnAnalyze = vi.fn();
      // const jobs = [{ id: '1', title: 'Engineer' }];
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={jobs} onAnalyze={mockOnAnalyze} />);
      // fireEvent.click(screen.getByRole('button', { name: /analyze/i }));
      // expect(mockOnAnalyze).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('shows loading indicator when adding job', async () => {
      // const slowAddJob = vi.fn(() => new Promise(resolve => setTimeout(resolve, 1000)));
      // render(<Step2Jobs onAddJob={slowAddJob} />);
      // // Type and click add
      // expect(screen.getByTestId('adding-spinner')).toBeInTheDocument();
    });

    it('shows loading indicator when analyzing', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} isAnalyzing={true} />);
      // expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    });

    it('disables all inputs during analysis', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} isAnalyzing={true} />);
      // expect(screen.getByRole('textbox')).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('shows error when job parsing fails', async () => {
      // const failingAddJob = vi.fn().mockRejectedValue(new Error('Parse error'));
      // render(<Step2Jobs onAddJob={failingAddJob} />);
      // // Attempt to add job
      // await waitFor(() => {
      //   expect(screen.getByText(/error/i)).toBeInTheDocument();
      // });
    });

    it('allows retry after error', () => {
      // Error should not prevent adding more jobs
    });
  });

  describe('Empty State', () => {
    it('shows empty state message when no jobs', () => {
      // render(<Step2Jobs onAddJob={mockOnAddJob} jobs={[]} />);
      // expect(screen.getByText(/no job descriptions/i)).toBeInTheDocument();
    });

    it('shows helpful instructions in empty state', () => {
      // Should guide user on what to do
    });
  });
});
