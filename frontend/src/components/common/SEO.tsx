import { FC } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';

declare const __PROJECT_OWNER__: string;

const projectOwner =
  typeof __PROJECT_OWNER__ !== 'undefined'
    ? __PROJECT_OWNER__
    : process.env.PROJECT_OWNER || 'Portfolio Owner';

interface SEOProps {
  title?: string | null;
  description?: string | null;
  ogImage?: string | null;
  url?: string | null;
}

const SEO: FC<SEOProps> = ({ title, description, ogImage, url }) => {
  const { t } = useTranslation();
  const ownerName = projectOwner;

  const defaultTitle = t(
    'meta.defaultTitle',
    `${ownerName} | Portfolio & Astrophotography`
  );
  const defaultDescription = t(
    'meta.defaultDescription',
    `Personal portfolio and astrophotography gallery of ${ownerName}.`
  );

  const finalTitle = title ? `${title} | ${defaultTitle}` : defaultTitle;
  const finalDescription = description || defaultDescription;
  const finalUrl = url
    ? `https://lukaszremkowicz.com${url}`
    : 'https://lukaszremkowicz.com';

  return (
    <Helmet>
      {/* Standard Metadata */}
      <title>{finalTitle}</title>
      <meta name='description' content={finalDescription} />

      {/* Open Graph / Facebook */}
      <meta property='og:type' content='website' />
      <meta property='og:url' content={finalUrl} />
      <meta property='og:title' content={finalTitle} />
      <meta property='og:description' content={finalDescription} />
      {ogImage && <meta property='og:image' content={ogImage} />}

      {/* Twitter */}
      <meta property='twitter:card' content='summary_large_image' />
      <meta property='twitter:url' content={finalUrl} />
      <meta property='twitter:title' content={finalTitle} />
      <meta property='twitter:description' content={finalDescription} />
      {ogImage && <meta property='twitter:image' content={ogImage} />}
    </Helmet>
  );
};

export default SEO;
