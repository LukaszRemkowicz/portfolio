export const BFF_ROUTES: {
  contact: string;
  images: string;
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
export function getFrontendTransportRoute(
  pathname: string,
  method: string
): {
  allow: string;
  backendPath: string;
  kind: string;
  methodNotAllowed: boolean;
} | null;
