const fs = require('fs');
const path = require('path');
const axios = require('axios');

const BASE_URL = 'https://lukaszremkowicz.com'; // Replace with actual domain
const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

const STATIC_ROUTES = [
  '/',
  '/astrophotography',
  '/programming',
  '/travel-highlights',
  '/contact',
  '/privacy',
];

async function generateSitemap() {
  console.log('Generating sitemap...');

  let dynamicRoutes = [];

  try {
    // 1. Fetch Astro Images
    console.log(`Fetching images from ${API_URL}/image/...`);
    const imagesRes = await axios.get(`${API_URL}/image/`, { timeout: 5000 });
    let images = imagesRes.data;

    // Handle DRF Pagination
    if (images.results && Array.isArray(images.results)) {
      images = images.results;
    }

    if (Array.isArray(images)) {
      const imageRoutes = images.map(
        img => `/astrophotography?img=${img.slug}`
      );
      dynamicRoutes = [...dynamicRoutes, ...imageRoutes];
      console.log(`Added ${imageRoutes.length} image routes.`);
    }

    // 2. Fetch Travel Highlights
    console.log(
      `Fetching travel highlights from ${API_URL}/travel-highlights/...`
    );
    const travelRes = await axios.get(`${API_URL}/travel-highlights/`, {
      timeout: 5000,
    });
    let locations = travelRes.data;

    // Handle DRF Pagination
    if (locations.results && Array.isArray(locations.results)) {
      locations = locations.results;
    } else if (!Array.isArray(locations)) {
      locations = [];
    }

    if (Array.isArray(locations)) {
      // Check structure based on types/index.ts: MainPageLocation[]
      // URL pattern: /travel-highlights/:countrySlug/:placeSlug?
      const travelRoutes = locations.map(loc => {
        const base = `/travel-highlights/${loc.country_slug}`;
        return loc.place_slug ? `${base}/${loc.place_slug}` : base;
      });
      dynamicRoutes = [...dynamicRoutes, ...travelRoutes];
      console.log(`Added ${travelRoutes.length} travel routes.`);
    }
  } catch (error) {
    console.warn(
      'Could not fetch dynamic routes (Backend might be down). Generating static sitemap only.'
    );
    console.warn(`Error: ${error.message}`);
  }

  const allRoutes = [...STATIC_ROUTES, ...dynamicRoutes];

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allRoutes
  .map(route => {
    return `  <url>
    <loc>${BASE_URL}${route}</loc>
    <changefreq>weekly</changefreq>
    <priority>${route === '/' ? '1.0' : '0.8'}</priority>
  </url>`;
  })
  .join('\n')}
</urlset>`;

  const publicDir = path.resolve(__dirname, '../public');
  // Ensure public dir exists (it should in Vite project)
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  const sitemapPath = path.join(publicDir, 'sitemap.xml');
  fs.writeFileSync(sitemapPath, sitemap);

  console.log(`Sitemap generated at ${sitemapPath}`);
}

generateSitemap();
