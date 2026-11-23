#!/usr/bin/env bash
###############################################################################
# utils.sh
#
# Purpose:
#   Shared helpers for the local db_backup scripts.
#   Production data lives in Supabase (see .github/workflows/supabase-maintenance.yml),
#   so this file only knows about the local dev Compose database.
###############################################################################

# ------------------------------------------------------------------
# get_db_name
#   Returns the local dev database name used by docker-compose.yml (service db).
# ------------------------------------------------------------------
get_db_name() {
  echo "portfolio_dev"
}
