import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Replace with your actual domain
const BASE_URL = 'https://lukaszremkowicz.com';

// API base URL for fetching dynamic content
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000/api';

// Static routes
const staticRoutes = ['/', '/astrophotography', '/programming', '/privacy'];

async function fetchDynamicRoutes() {
  try {
    // We only need the top-level travel highlights here for simplicity
    // A full implementation might fetch from `/api/travel-highlights/` and build all routes
    const res = await fetch(`${API_URL}/travel-highlights/`);
    if (!res.ok) {
      console.warn(
        'Failed to fetch travel highlights for sitemap. Using empty array.'
      );
      return [];
    }
    const data = await res.json();
    return data.map(
      (item: {
        date_slug?: string;
        adventure_date_raw?: string;
        country_slug: string;
        place_slug: string;
      }) => {
        // Very basic URL construction
        const dateSlug =
          item.date_slug || item.adventure_date_raw?.substring(0, 10);
        return `/travel/${item.country_slug}/${item.place_slug}/${dateSlug}`;
      }
    );
  } catch (err) {
    console.error('Error fetching dynamic routes:', err);
    return [];
  }
}

async function generateSitemap() {
  console.log('Generating sitemap...');
  const dynamicRoutes = await fetchDynamicRoutes();
  const allRoutes = [...staticRoutes, ...dynamicRoutes];

  const sitemapContent = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${allRoutes
    .map(route => {
      return `
    <url>
      <loc>${BASE_URL}${route}</loc>
      <lastmod>${new Date().toISOString()}</lastmod>
      <changefreq>weekly</changefreq>
      <priority>${route === '/' ? '1.0' : '0.8'}</priority>
    </url>
      `.trim();
    })
    .join('\n  ')}
</urlset>`;

  const publicDir = path.resolve(__dirname, '../public');
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  fs.writeFileSync(path.join(publicDir, 'sitemap.xml'), sitemapContent);
  console.log('Sitemap generated successfully!');
}

generateSitemap();
