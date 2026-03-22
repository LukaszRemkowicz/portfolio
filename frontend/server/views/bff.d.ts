export const BFF_ROUTES: {
  contact: string;
  images: string;
  imageFiles: string;
  profile: string;
  background: string;
  astroImages: string;
  settings: string;
  travelHighlights: string;
  tags: string;
  categories: string;
  travelBySlug: string;
};

export function getContactBackendRoute(
  pathname: string,
  method: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
export function getTravelBackendRoute(
  pathname: string,
  method: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
export function getImagesBackendRoute(
  pathname: string,
  method: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
export function getImageFilesBackendRoute(
  pathname: string,
  method: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
export function getFrontendTransportRoute(
  pathname: string,
  method: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
