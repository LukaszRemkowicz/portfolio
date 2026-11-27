-- Projects endpoint reads the live price source (Project.price_source_url, programming 0016).
grant select (price_source_url) on programming_project to portfolio_api;
