export type SupportedLanguage = 'en' | 'pl';

/**
 * Detect the best supported site language from an Accept-Language-like value.
 */
export function detectLanguage(
  acceptLanguage?: string | null
): SupportedLanguage {
  if (!acceptLanguage) return 'en';

  const languages = acceptLanguage
    .split(',')
    .map(lang => lang.split(';')[0].trim().toLowerCase());

  for (const lang of languages) {
    if (lang.startsWith('pl')) return 'pl';
    if (lang.startsWith('en')) return 'en';
  }

  return 'en';
}
