import { stripHtml, slugify, sanitizeHtml } from '../../utils/html';

describe('HTML Utils', () => {
  describe('stripHtml', () => {
    it('removes HTML tags', () => {
      expect(stripHtml('<p>Hello</p>')).toBe('Hello');
    });

    it('handles nested tags', () => {
      expect(stripHtml('<div><p>Hello <b>World</b></p></div>')).toBe(
        'Hello World'
      );
    });

    it('returns empty string for null/undefined/empty input', () => {
      expect(stripHtml('')).toBe('');
      // @ts-ignore
      expect(stripHtml(null)).toBe('');
    });
  });

  describe('slugify', () => {
    it('converts to lowercase', () => {
      expect(slugify('Hello')).toBe('hello');
    });

    it('replaces spaces with dashes', () => {
      expect(slugify('Hello World')).toBe('hello-world');
    });

    it('removes special characters', () => {
      expect(slugify('Hello! @World#')).toBe('hello-world');
    });

    it('handles multiple spaces and dashes', () => {
      expect(slugify('Hello   World--Test')).toBe('hello-world-test');
    });
  });

  describe('sanitizeHtml', () => {
    it('preserves safe HTML', () => {
      expect(sanitizeHtml('<p>Hello</p>')).toBe('<p>Hello</p>');
    });

    it('removes script tags (XSS prevention)', () => {
      const input = '<script>alert("xss")</script>Hello';
      expect(sanitizeHtml(input)).toBe('Hello');
    });

    it('removes event attributes (XSS prevention)', () => {
      const input = '<img src=x onerror=alert(1) />';
      expect(sanitizeHtml(input)).toBe('<img src="x">');
    });

    it('returns empty string for empty input', () => {
      expect(sanitizeHtml('')).toBe('');
    });
  });
});
