import { matchPath } from 'react-router-dom';
import { APP_ROUTES } from '../api/constants';

interface FeatureRouteSettings {
  programming?: boolean;
  shop?: boolean;
}

const KNOWN_PUBLIC_PATHS = new Set([
  APP_ROUTES.HOME,
  APP_ROUTES.ASTROPHOTOGRAPHY,
  APP_ROUTES.SHOP,
  APP_ROUTES.PROGRAMMING,
  APP_ROUTES.PRIVACY,
]);

export const isKnownPublicPath = (pathname: string): boolean => {
  if (KNOWN_PUBLIC_PATHS.has(pathname)) {
    return true;
  }

  return Boolean(
    matchPath(`${APP_ROUTES.ASTROPHOTOGRAPHY}/:slug`, pathname) ||
    matchPath(
      `${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug/:dateSlug`,
      pathname
    )
  );
};

export const getDocumentStatusCode = (pathname: string): number =>
  isKnownPublicPath(pathname) ? 200 : 404;

export const isFeatureRouteEnabled = (
  pathname: string,
  settings?: FeatureRouteSettings
): boolean => {
  if (pathname === APP_ROUTES.PROGRAMMING) {
    return settings?.programming === true;
  }

  if (pathname === APP_ROUTES.SHOP) {
    return settings?.shop === true;
  }

  return true;
};

export const getDocumentStatusCodeForSettings = (
  pathname: string,
  settings?: FeatureRouteSettings
): number => {
  if (!isKnownPublicPath(pathname)) {
    return 404;
  }

  return isFeatureRouteEnabled(pathname, settings) ? 200 : 404;
};
