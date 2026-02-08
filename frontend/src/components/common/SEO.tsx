import React from 'react';
import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title: string;
  description?: string;
  keywords?: string[];
  image?: string;
  url?: string;
  type?: string;
}

const SEO: React.FC<SEOProps> = ({
  title,
  description = 'Portfolio landing page with astrophotography gallery, built with React, TypeScript, and Zustand.',
  keywords = [
    'astrophotography',
    'web development',
    'portfolio',
    'react',
    'typescript',
  ],
  image = '/og-image.jpg',
  url = typeof window !== 'undefined' ? window.location.href : '',
  type = 'website',
}) => {
  const siteTitle = 'Lukasz Remkowicz | Portfolio';
  const fullTitle = title === siteTitle ? title : `${title} | ${siteTitle}`;

  // Ensure full URL for OpenGraph images
  const fullImage = image.startsWith('http')
    ? image
    : `${window.location.origin}${image.startsWith('/') ? '' : '/'}${image}`;

  return (
    <Helmet>
      {/* Standard Metadata */}
      <title>{fullTitle}</title>
      <meta name='description' content={description} />
      {keywords && <meta name='keywords' content={keywords.join(', ')} />}

      {/* OpenGraph Metadata */}
      <meta property='og:title' content={fullTitle} />
      <meta property='og:description' content={description} />
      <meta property='og:type' content={type} />
      <meta property='og:url' content={url} />
      <meta property='og:image' content={fullImage} />

      {/* Twitter Metadata */}
      <meta name='twitter:card' content='summary_large_image' />
      <meta name='twitter:title' content={fullTitle} />
      <meta name='twitter:description' content={description} />
      <meta name='twitter:image' content={fullImage} />

      {/* Canonical URL */}
      <link rel='canonical' href={url} />
    </Helmet>
  );
};

export default SEO;
