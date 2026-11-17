-- Contact form for the API function. portfolio_api gets no table rights on inbox_contactmessage:
-- it may only call two SECURITY DEFINER functions (owned by portfolio, the Django table owner),
-- so the API can add a message but never read stored ones.
-- Callers must run them in a `begin read write` transaction (portfolio_api defaults to read-only).
create schema api_private authorization portfolio;
revoke all on schema api_private from public;
grant usage on schema api_private to portfolio_api;

-- Attempts in the last hour, mirrors Django's ContactFormThrottle cache counters.
create table api_private.contact_attempt (
  id bigint generated always as identity primary key,
  ip text not null,
  email text,
  created_at timestamptz not null default now()
);
create index contact_attempt_created_at_idx on api_private.contact_attempt (created_at);
alter table api_private.contact_attempt owner to portfolio;

-- true = allowed and recorded; false = limit hit (per IP 5/h, per email 3/h, IP+email 2/h).
create function api_private.contact_throttle(p_ip text, p_email text)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, pg_temp
as $$
begin
  -- Serialise attempts from one IP so parallel requests cannot both slip under the limit.
  perform pg_advisory_xact_lock(hashtext('contact_throttle:' || p_ip));
  delete from api_private.contact_attempt where created_at < now() - interval '1 hour';
  if (select count(*) from api_private.contact_attempt where ip = p_ip) >= 5 then
    return false;
  end if;
  if p_email is not null and (
    (select count(*) from api_private.contact_attempt where email = p_email) >= 3
    or (select count(*) from api_private.contact_attempt where ip = p_ip and email = p_email) >= 2
  ) then
    return false;
  end if;
  insert into api_private.contact_attempt (ip, email) values (p_ip, p_email);
  return true;
end;
$$;

-- New message id, or null when the same email+subject was sent in the last 5 minutes.
create function api_private.contact_submit(p_name text, p_email text, p_subject text, p_message text)
returns bigint
language plpgsql
security definer
set search_path = pg_catalog, pg_temp
as $$
declare
  v_id bigint;
begin
  perform pg_advisory_xact_lock(hashtext('contact_submit:' || p_email));
  if exists (
    select 1 from public.inbox_contactmessage
    where email = p_email and subject = p_subject and created_at >= now() - interval '5 minutes'
  ) then
    return null;
  end if;
  insert into public.inbox_contactmessage (name, email, subject, message, created_at, updated_at, is_read)
  values (p_name, p_email, p_subject, p_message, now(), now(), false)
  returning id into v_id;
  return v_id;
end;
$$;

alter function api_private.contact_throttle(text, text) owner to portfolio;
alter function api_private.contact_submit(text, text, text, text) owner to portfolio;
revoke all on function api_private.contact_throttle(text, text) from public;
revoke all on function api_private.contact_submit(text, text, text, text) from public;
grant execute on function api_private.contact_throttle(text, text) to portfolio_api;
grant execute on function api_private.contact_submit(text, text, text, text) to portfolio_api;
