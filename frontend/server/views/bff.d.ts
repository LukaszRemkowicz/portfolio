export const BFF_ROUTES: {
  contact: string;
  images: string;
  travelBySlug: string;
};

export function getTravelBackendPath(pathname: string): string | null;
export function getImagesBackendPath(pathname: string): string | null;
export function resolveBffBackendPath(
  pathname: string,
  method?: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
