export const SHELL_RESOURCES: {
  background: { resource: string; tags: string[] };
  latestAstroImages: { resource: string; tags: string[] };
  profile: { resource: string; tags: string[] };
  settings: { resource: string; tags: string[] };
  travelHighlights: { resource: string; tags: string[] };
};

export function getCachedShellLoader(
  language: string,
  requestOrigin?: string
): <T>(
  resourceConfig: { resource: string; tags: string[] },
  loader: () => Promise<T>
) => Promise<T>;
