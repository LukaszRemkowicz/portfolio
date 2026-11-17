-- The sitemap shows lastmod from updated_at, so the API may read it again.
grant select (updated_at) on astrophotography_astroimage to portfolio_api;
