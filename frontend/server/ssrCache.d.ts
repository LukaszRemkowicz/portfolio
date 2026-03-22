export function getCachedShellData<T>(options: {
  resource: string;
  language?: string;
  requestOrigin?: string;
  tags?: string[];
  ttlMs?: number;
  loader: () => Promise<T>;
}): Promise<T>;

export function invalidateCacheTags(tags?: string[]): {
  invalidatedKeys: number;
  tags: string[];
};
