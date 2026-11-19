# 🚀 Release Scripts

> **VPS rollback only.** These scripts deploy the VPS stack, which has been stopped since 2026-11-17 and is kept only as a rollback path. The current release flow is described in the root [README](../../../README.md) and [supabase_api.md](../../docs/project/supabase_api.md).

The canonical operational documentation for infrastructure scripts lives in:

- [infra/scripts/README.md](../README.md)

## 🗂️ This Folder Contains

- [build.sh](./build.sh) - manual fallback: build production images locally
- [prepare_images.sh](./prepare_images.sh) - pull production images from GHCR and tag them locally
- [release.sh](./release.sh) - one-shot release job (migrations, collectstatic)
- [deploy.sh](./deploy.sh) - switch `be` and `nginx` to a tag, update rollback state
- [deploy_production.sh](./deploy_production.sh) - guided wrapper: `prepare_images.sh` -> `release.sh` -> `deploy.sh`
- [test_deploy_container_selection.sh](./test_deploy_container_selection.sh) - shell test for deploy container selection

## 📖 Use The Shared Runbook For

- build and deploy workflow
- guided production deploy wrapper
- backup and restore workflow
- troubleshooting
- operational prerequisites
- `--dry-run` behavior for release and deploy flows
