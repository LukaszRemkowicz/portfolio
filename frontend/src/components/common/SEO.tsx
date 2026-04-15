import { FC } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { useRequestOrigin } from '../../context/RequestOriginContext';
import { publicEnv } from '../../../server/publicEnv.js';

interface SEOProps {
  title?: string | null;
  description?: string | null;
  ogImage?: string | null;
  url?: string | null;
  robots?: string | null;
  includeCanonical?: boolean;
}

const SEO: FC<SEOProps> = ({
  title,
  description,
  ogImage,
  url,
  robots,
  includeCanonical = true,
}) => {
  const { t } = useTranslation();
  const location = useLocation();
  const requestOrigin = useRequestOrigin();
  const ownerName = publicEnv.PROJECT_OWNER;

  const defaultTitle = t('meta.defaultTitle', {
    ownerName,
    defaultValue: `${ownerName} | Portfolio & Astrophotography`,
  });
  const defaultDescription = t('meta.defaultDescription', {
    ownerName,
    defaultValue: `Personal portfolio and astrophotography gallery of ${ownerName}.`,
  });

  const finalTitle = title ? `${title} | ${defaultTitle}` : defaultTitle;
  const finalDescription = description || defaultDescription;
  const publicOrigin = publicEnv.SITE_DOMAIN
    ? `https://${publicEnv.SITE_DOMAIN}`
    : 'http://localhost';
  const origin =
    requestOrigin ||
    (typeof window !== 'undefined' ? window.location.origin : publicOrigin);
  const routePath = url || `${location.pathname}${location.search}`;
  const finalUrl = new URL(routePath || '/', origin).toString();

  return (
    <Helmet>
      {/* Standard Metadata */}
      <title>{finalTitle}</title>
      <meta name='description' content={finalDescription} />
      {robots && <meta name='robots' content={robots} />}

      {/* Open Graph / Facebook */}
      <meta property='og:type' content='website' />
      <meta property='og:url' content={finalUrl} />
      <meta property='og:title' content={finalTitle} />
      <meta property='og:description' content={finalDescription} />
      {ogImage && <meta property='og:image' content={ogImage} />}
      {includeCanonical && <link rel='canonical' href={finalUrl} />}

      {/* Twitter */}
      <meta name='twitter:card' content='summary_large_image' />
      <meta name='twitter:url' content={finalUrl} />
      <meta name='twitter:title' content={finalTitle} />
      <meta name='twitter:description' content={finalDescription} />
      {ogImage && <meta name='twitter:image' content={ogImage} />}
    </Helmet>
  );
};

export default SEO;
