-- Role password is set out of band and lives in Doppler.
create role portfolio login;
grant usage, create on schema public to portfolio;
grant usage on schema extensions to portfolio;
alter role portfolio set search_path = public, extensions;
create extension if not exists btree_gist with schema extensions;
