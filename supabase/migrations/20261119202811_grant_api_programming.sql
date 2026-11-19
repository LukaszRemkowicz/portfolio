-- Public Projects endpoint: the API reads only non-file columns (cover image is served as
-- variants), like shop_shopproduct in 20261117141703_limit_api_file_columns.sql.
grant select (id, technologies, github_url, live_url, is_active, pricing, price, currency, created_at,
  updated_at)
  on programming_project to portfolio_api;
grant select on programming_project_translation to portfolio_api;
