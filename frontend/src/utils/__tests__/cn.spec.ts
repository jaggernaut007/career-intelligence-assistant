/**
 * Tests for cn utility function.
 */

import { describe, it, expect } from 'vitest';
import { cn } from '../cn';

describe('cn', () => {
  describe('Basic functionality', () => {
    it('returns empty string for no arguments', () => {
      expect(cn()).toBe('');
    });

    it('returns single class name', () => {
      expect(cn('foo')).toBe('foo');
    });

    it('joins multiple class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('filters out falsy values', () => {
      expect(cn('foo', null, undefined, false, '', 'bar')).toBe('foo bar');
    });
  });

  describe('Conditional classes', () => {
    it('handles conditional object syntax', () => {
      expect(cn({ foo: true, bar: false })).toBe('foo');
    });

    it('combines strings and objects', () => {
      expect(cn('base', { active: true, disabled: false })).toBe('base active');
    });

    it('handles boolean conditions', () => {
      const isActive = true;
      const isDisabled = false;
      expect(cn('btn', isActive && 'btn-active', isDisabled && 'btn-disabled')).toBe('btn btn-active');
    });
  });

  describe('Array support', () => {
    it('handles arrays of class names', () => {
      expect(cn(['foo', 'bar'])).toBe('foo bar');
    });

    it('handles nested arrays', () => {
      expect(cn(['foo', ['bar', 'baz']])).toBe('foo bar baz');
    });
  });

  describe('Tailwind class merging', () => {
    it('merges conflicting padding classes', () => {
      expect(cn('p-4', 'p-2')).toBe('p-2');
    });

    it('merges conflicting margin classes', () => {
      expect(cn('m-4', 'm-8')).toBe('m-8');
    });

    it('merges conflicting color classes', () => {
      expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500');
    });

    it('merges conflicting text color classes', () => {
      expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    });

    it('merges conflicting width classes', () => {
      expect(cn('w-4', 'w-8')).toBe('w-8');
    });

    it('merges conflicting height classes', () => {
      expect(cn('h-4', 'h-full')).toBe('h-full');
    });

    it('preserves non-conflicting classes', () => {
      expect(cn('p-4', 'm-4')).toBe('p-4 m-4');
    });

    it('merges responsive variants correctly', () => {
      expect(cn('md:p-4', 'md:p-8')).toBe('md:p-8');
    });

    it('handles hover variants', () => {
      expect(cn('hover:bg-red-500', 'hover:bg-blue-500')).toBe('hover:bg-blue-500');
    });
  });

  describe('Complex scenarios', () => {
    it('handles component styling pattern', () => {
      const baseStyles = 'px-4 py-2 rounded';
      const variantStyles = 'bg-blue-500 text-white';
      const sizeStyles = 'text-sm';
      const customStyles = 'bg-red-500'; // Should override bg-blue-500

      expect(cn(baseStyles, variantStyles, sizeStyles, customStyles)).toBe(
        'px-4 py-2 rounded text-white text-sm bg-red-500'
      );
    });

    it('handles disabled state override', () => {
      const isDisabled = true;
      expect(
        cn('bg-blue-500 cursor-pointer', isDisabled && 'bg-gray-300 cursor-not-allowed')
      ).toBe('bg-gray-300 cursor-not-allowed');
    });

    it('handles multiple conditional classes', () => {
      const state = { active: true, disabled: false, loading: true };
      expect(
        cn(
          'btn',
          state.active && 'btn-active',
          state.disabled && 'btn-disabled',
          state.loading && 'btn-loading'
        )
      ).toBe('btn btn-active btn-loading');
    });
  });

  describe('Edge cases', () => {
    it('handles whitespace in class names', () => {
      expect(cn('  foo  ', '  bar  ')).toBe('foo bar');
    });

    it('handles duplicate class names (clsx does not dedupe non-tailwind classes)', () => {
      // Note: clsx/twMerge only dedupes conflicting tailwind classes, not arbitrary duplicates
      expect(cn('foo', 'foo', 'foo')).toBe('foo foo foo');
    });

    it('handles number 0', () => {
      expect(cn('foo', 0, 'bar')).toBe('foo bar');
    });
  });
});
