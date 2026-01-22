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
 * Standardizes a string into a slug (lowercase, hyphenated).
 */
export const slugify = (text: string): string => {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-") // Replace spaces with -
    .replace(/[^\w-]+/g, "") // Remove all non-word chars
    .replace(/--+/g, "-") // Replace multiple - with single -
    .replace(/^-+/, "") // Trim - from start of text
    .replace(/-+$/, ""); // Trim - from end of text
};

/**
 * Utility function to sanitize HTML content to prevent XSS attacks.
 * Should be used before rendering any HTML from the backend using dangerouslySetInnerHTML.
 */
export const sanitizeHtml = (html: string): string => {
  if (!html) return "";
  return DOMPurify.sanitize(html);
};
