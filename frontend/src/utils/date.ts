export const getDateSlug = (
  dateString: string | null | undefined
): string | null => {
  if (!dateString) return null;
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return null;

    // e.g. "jan2026"
    const month = date
      .toLocaleString('en-US', { month: 'short' })
      .toLowerCase();
    const year = date.getFullYear();
    return `${month}${year}`;
  } catch (error) {
    console.error('Failed to parse date string for slug:', dateString, error);
    return null;
  }
};
