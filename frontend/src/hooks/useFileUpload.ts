import { useState, useCallback } from 'react';
import { validateFile, type ValidationResult } from '@/utils/validation';

interface UseFileUploadOptions {
  onUpload: (file: File) => Promise<void>;
}

interface UseFileUploadReturn {
  file: File | null;
  isDragging: boolean;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
  handleDragEnter: (e: React.DragEvent) => void;
  handleDragLeave: (e: React.DragEvent) => void;
  handleDragOver: (e: React.DragEvent) => void;
  handleDrop: (e: React.DragEvent) => void;
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  reset: () => void;
}

export function useFileUpload({ onUpload }: UseFileUploadOptions): UseFileUploadReturn {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const processFile = useCallback(
    async (selectedFile: File) => {
      setError(null);

      const validation: ValidationResult = validateFile(selectedFile);
      if (!validation.valid) {
        setError(validation.error || 'Invalid file');
        return;
      }

      setFile(selectedFile);
      setIsUploading(true);
      setUploadProgress(0);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      try {
        await onUpload(selectedFile);
        setUploadProgress(100);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed');
        setFile(null);
      } finally {
        clearInterval(progressInterval);
        setIsUploading(false);
      }
    },
    [onUpload]
  );

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        processFile(droppedFile);
      }
    },
    [processFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        processFile(selectedFile);
      }
    },
    [processFile]
  );

  const reset = useCallback(() => {
    setFile(null);
    setIsDragging(false);
    setIsUploading(false);
    setUploadProgress(0);
    setError(null);
  }, []);

  return {
    file,
    isDragging,
    isUploading,
    uploadProgress,
    error,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
    handleFileSelect,
    reset,
  };
}
