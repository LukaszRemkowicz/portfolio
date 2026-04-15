import DOMPurify from 'isomorphic-dompurify';

/**
 * Utility function to strip HTML tags from a string.
 * Useful for card descriptions, meta tags, and SEO.
 */
export const stripHtml = (html: string): string => {
  if (!html) return '';

  if (typeof DOMParser === 'undefined') {
    // Server-side fallback: remove tags and normalize common entities so
    // meta descriptions do not leak tag/style fragments into SSR output.
    return html
      .replace(/<[^>]*>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/gi, "'")
      .replace(/\s+/g, ' ')
      .trim();
  }

  // Use a DOM-based approach for reliability
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
};

/**
 * Trim plain-text SEO copy to a stable snippet length without aggressively
 * cutting mid-word when there is a nearby whitespace boundary.
 */
export const truncateText = (text: string, maxLength: number): string => {
  const normalized = text.trim().replace(/\s+/g, ' ');

  if (normalized.length <= maxLength) {
    return normalized;
  }

  const boundary = normalized.lastIndexOf(' ', maxLength - 1);
  const truncated =
    boundary >= Math.floor(maxLength * 0.6)
      ? normalized.slice(0, boundary)
      : normalized.slice(0, maxLength);

  return `${truncated.trim()}...`;
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

  const sanitizedHtml = DOMPurify.sanitize(html);

  return sanitizedHtml.replace(
    /\sstyle=(['"])(.*?)\1/gi,
    (_match, quote: string, styleValue: string) => {
      const preservedDeclarations = styleValue
        .split(';')
        .map(declaration => declaration.trim())
        .filter(Boolean)
        .filter(
          declaration =>
            !/^(background|background-color)\s*:/i.test(declaration)
        );

      if (preservedDeclarations.length === 0) {
        return '';
      }

      return ` style=${quote}${preservedDeclarations.join('; ')}${quote}`;
    }
  );
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
