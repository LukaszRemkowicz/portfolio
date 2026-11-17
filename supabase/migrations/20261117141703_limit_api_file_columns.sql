-- Same rule as the astroimage revoke: the API reads only the columns it uses, never storage
-- keys of source files (served only as image variants) or bookkeeping timestamps.
revoke select on astrophotography_mainpagebackgroundimage from portfolio_api;
grant select (id, created_at) on astrophotography_mainpagebackgroundimage to portfolio_api;

revoke select on shop_shopproduct from portfolio_api;
grant select (id, created_at, price, currency, external_url, is_active)
  on shop_shopproduct to portfolio_api;

revoke select on shop_shopsettings from portfolio_api;
grant select (id) on shop_shopsettings to portfolio_api;
