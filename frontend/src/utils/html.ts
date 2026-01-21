import DOMPurify from "dompurify";

/**
 * Utility function to strip HTML tags from a string.
 * Useful for card descriptions, meta tags, and SEO.
 */
export const stripHtml = (html: string): string => {
  if (!html) return "";

  // Use a DOM-based approach for reliability
  const doc = new DOMParser().parseFromString(html, "text/html");
  return doc.body.textContent || "";
};

/**
 * Utility function to sanitize HTML content to prevent XSS attacks.
 * Should be used before rendering any HTML from the backend using dangerouslySetInnerHTML.
 */
export const sanitizeHtml = (html: string): string => {
  if (!html) return "";
  return DOMPurify.sanitize(html);
};
