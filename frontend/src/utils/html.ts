import DOMPurify from 'isomorphic-dompurify';

/**
 * Utility function to strip HTML tags from a string.
 * Useful for card descriptions, meta tags, and SEO.
 */
export const stripHtml = (html: string): string => {
  if (!html) return '';

  if (typeof DOMParser === 'undefined') {
    // Fallback: remove angle brackets so any residual tag fragments
    // cannot be interpreted as HTML, then normalize whitespace.
    return html.replace(/[<>]/g, ' ').replace(/\s+/g, ' ').trim();
  }

  // Use a DOM-based approach for reliability
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
};
/**
 * Standardizes a string into a slug (lowercase, hyphenated).
 */
export const slugify = (text: string): string => {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-') // Replace spaces with -
    .replace(/[^\w-]+/g, '') // Remove all non-word chars
    .replace(/--+/g, '-') // Replace multiple - with single -
    .replace(/^-+/, '') // Trim - from start of text
    .replace(/-+$/, ''); // Trim - from end of text
};

/**
 * Utility function to sanitize HTML content to prevent XSS attacks.
 * Should be used before rendering any HTML from the backend using dangerouslySetInnerHTML.
 */
export const sanitizeHtml = (html: string): string => {
  if (!html) return '';

  return DOMPurify.sanitize(html);
};

/**
 * Returns true when an HTML string is visually empty —
 * i.e. contains no meaningful text after stripping tags and common entities.
 * Catches CKEditor empty states like "<p></p>" or "<p>&nbsp;</p>".
 */
export const isHtmlEmpty = (html: string | undefined | null): boolean => {
  if (!html) return true;
  const text = stripHtml(html)
    .replace(/\u00a0/g, '')
    .trim();
  return text.length === 0;
};
