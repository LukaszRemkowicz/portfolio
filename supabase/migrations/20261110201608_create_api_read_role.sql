-- Read-only role for the public API function; password set out of band (Doppler).
-- It may read only what the public site shows. Django admin keeps full access via role portfolio.
-- When the API needs a new table, grant it here in a new migration.
-- Order on a fresh project: the first two Supabase migrations, then Django `migrate`
-- (docker-compose.supabase.yml), then this one: it grants on tables Django creates.
-- A Django migration that recreates a table drops its grants; re-apply them.
create role portfolio_api login;
alter role portfolio_api set default_transaction_read_only = on;
alter role portfolio_api set statement_timeout = '5s';

-- postgres created role portfolio, so it may grant itself membership; needed to grant on tables portfolio owns.
grant portfolio to postgres;

grant usage on schema public to portfolio_api;
grant select on
  astrophotography_astroimage,
  astrophotography_astroimage_translation,
  astrophotography_astroimage_tags,
  astrophotography_astroimage_camera,
  astrophotography_astroimage_lens,
  astrophotography_astroimage_telescope,
  astrophotography_astroimage_tracker,
  astrophotography_astroimage_tripod,
  astrophotography_camera,
  astrophotography_lens,
  astrophotography_telescope,
  astrophotography_tracker,
  astrophotography_tripod,
  astrophotography_tag,
  astrophotography_tag_translation,
  astrophotography_place,
  astrophotography_place_translation,
  astrophotography_place_sub_places,
  astrophotography_mainpagelocation,
  astrophotography_mainpagelocation_translation,
  astrophotography_mainpagelocation_images,
  astrophotography_mainpagebackgroundimage,
  astrophotography_meteorsmainpageconfig,
  core_imagevariant,
  core_landingpagesettings,
  core_landingpagesettings_latest_filters,
  django_content_type,
  shop_shopproduct,
  shop_shopproduct_translation,
  shop_shopsettings,
  shop_shopsettings_translation,
  users_profile,
  users_profile_translation,
  users_user_translation
to portfolio_api;

-- Only the public profile columns; never the password hash.
grant select (id, first_name, last_name, is_active, contact_email) on users_user to portfolio_api;
