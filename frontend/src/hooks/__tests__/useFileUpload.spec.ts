/**
 * Tests for useFileUpload hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFileUpload } from '../useFileUpload';

describe('useFileUpload', () => {
  const mockOnUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnUpload.mockResolvedValue(undefined);
  });

  const createFile = (name: string, type: string, size?: number) => {
    const file = new File(['test content'], name, { type });
    if (size !== undefined) {
      Object.defineProperty(file, 'size', { value: size });
    }
    return file;
  };

  describe('Initial State', () => {
    it('returns initial state', () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));

      expect(result.current.file).toBeNull();
      expect(result.current.isDragging).toBe(false);
      expect(result.current.isUploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
      expect(result.current.error).toBeNull();
    });

    it('returns all handler functions', () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));

      expect(typeof result.current.handleDragEnter).toBe('function');
      expect(typeof result.current.handleDragLeave).toBe('function');
      expect(typeof result.current.handleDragOver).toBe('function');
      expect(typeof result.current.handleDrop).toBe('function');
      expect(typeof result.current.handleFileSelect).toBe('function');
      expect(typeof result.current.reset).toBe('function');
    });
  });

  describe('File Selection', () => {
    it('sets file when valid file is selected', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.file).toBe(file);
      });
    });

    it('calls onUpload with file', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(file);
      });
    });

    it('does nothing when no file is selected', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));

      await act(async () => {
        const event = {
          target: { files: [] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      expect(result.current.file).toBeNull();
      expect(mockOnUpload).not.toHaveBeenCalled();
    });
  });

  describe('File Validation', () => {
    it('sets error for invalid file type', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('image.jpg', 'image/jpeg');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      expect(result.current.error).toBe('Invalid file type. Supported formats: PDF, DOCX, TXT');
      expect(mockOnUpload).not.toHaveBeenCalled();
    });

    it('sets error for file too large', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('large.pdf', 'application/pdf', 15 * 1024 * 1024);

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      expect(result.current.error).toBe('File too large. Maximum size is 10MB');
      expect(mockOnUpload).not.toHaveBeenCalled();
    });
  });

  describe('Upload Progress', () => {
    it('sets isUploading to true during upload', async () => {
      let resolveUpload: () => void;
      const slowUpload = vi.fn(() => new Promise<void>((resolve) => {
        resolveUpload = resolve;
      }));

      const { result } = renderHook(() => useFileUpload({ onUpload: slowUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      act(() => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.isUploading).toBe(true);
      });

      await act(async () => {
        resolveUpload!();
      });

      await waitFor(() => {
        expect(result.current.isUploading).toBe(false);
      });
    });

    it('sets progress to 100 after successful upload', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.uploadProgress).toBe(100);
      });
    });
  });

  describe('Upload Error', () => {
    it('sets error when upload fails', async () => {
      const failingUpload = vi.fn().mockRejectedValue(new Error('Network error'));
      const { result } = renderHook(() => useFileUpload({ onUpload: failingUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });
    });

    it('clears file when upload fails', async () => {
      const failingUpload = vi.fn().mockRejectedValue(new Error('Failed'));
      const { result } = renderHook(() => useFileUpload({ onUpload: failingUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.file).toBeNull();
      });
    });

    it('handles non-Error rejection', async () => {
      const failingUpload = vi.fn().mockRejectedValue('string error');
      const { result } = renderHook(() => useFileUpload({ onUpload: failingUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Upload failed');
      });
    });
  });

  describe('Drag and Drop', () => {
    it('sets isDragging on drag enter', () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));

      act(() => {
        const event = {
          preventDefault: vi.fn(),
          stopPropagation: vi.fn(),
        } as unknown as React.DragEvent;
        result.current.handleDragEnter(event);
      });

      expect(result.current.isDragging).toBe(true);
    });

    it('clears isDragging on drag leave', () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));

      act(() => {
        const enterEvent = {
          preventDefault: vi.fn(),
          stopPropagation: vi.fn(),
        } as unknown as React.DragEvent;
        result.current.handleDragEnter(enterEvent);
      });

      act(() => {
        const leaveEvent = {
          preventDefault: vi.fn(),
          stopPropagation: vi.fn(),
        } as unknown as React.DragEvent;
        result.current.handleDragLeave(leaveEvent);
      });

      expect(result.current.isDragging).toBe(false);
    });

    it('prevents default on drag over', () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const preventDefault = vi.fn();
      const stopPropagation = vi.fn();

      act(() => {
        const event = { preventDefault, stopPropagation } as unknown as React.DragEvent;
        result.current.handleDragOver(event);
      });

      expect(preventDefault).toHaveBeenCalled();
      expect(stopPropagation).toHaveBeenCalled();
    });

    it('handles file drop', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      await act(async () => {
        const event = {
          preventDefault: vi.fn(),
          stopPropagation: vi.fn(),
          dataTransfer: { files: [file] },
        } as unknown as React.DragEvent;
        result.current.handleDrop(event);
      });

      await waitFor(() => {
        expect(result.current.file).toBe(file);
        expect(result.current.isDragging).toBe(false);
      });
    });

    it('clears isDragging on drop even with no files', () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));

      act(() => {
        const enterEvent = {
          preventDefault: vi.fn(),
          stopPropagation: vi.fn(),
        } as unknown as React.DragEvent;
        result.current.handleDragEnter(enterEvent);
      });

      act(() => {
        const dropEvent = {
          preventDefault: vi.fn(),
          stopPropagation: vi.fn(),
          dataTransfer: { files: [] },
        } as unknown as React.DragEvent;
        result.current.handleDrop(dropEvent);
      });

      expect(result.current.isDragging).toBe(false);
    });
  });

  describe('Reset', () => {
    it('resets all state', async () => {
      const { result } = renderHook(() => useFileUpload({ onUpload: mockOnUpload }));
      const file = createFile('resume.pdf', 'application/pdf');

      // First upload a file
      await act(async () => {
        const event = {
          target: { files: [file] },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        result.current.handleFileSelect(event);
      });

      await waitFor(() => {
        expect(result.current.file).not.toBeNull();
      });

      // Then reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.file).toBeNull();
      expect(result.current.isDragging).toBe(false);
      expect(result.current.isUploading).toBe(false);
      expect(result.current.uploadProgress).toBe(0);
      expect(result.current.error).toBeNull();
    });
  });
});
