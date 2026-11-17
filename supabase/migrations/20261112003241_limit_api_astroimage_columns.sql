-- The API reads only the columns the site shows. Not granted: original (storage key of the
-- source file; originals are served from image variants via signed links) and updated_at.
revoke select on astrophotography_astroimage from portfolio_api;
grant select (id, slug, created_at, capture_date, celestial_object, astrobin_url, zoom, place_id,
  calculated_exposure_hours) on astrophotography_astroimage to portfolio_api;
