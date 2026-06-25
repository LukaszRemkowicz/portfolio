# Image Variant Quickstart

## Purpose

Use this as the cheap entry point for image variant work before opening larger
analysis documents or broad repository searches.

## Key Files

- `backend/common/types.py`
  Owns `ImageVariantSpec`, `ViewportWidths`, and `ImageVariantSource`.
- `backend/common/utils/image.py`
  Owns generated image file naming and width-based image builders.
- `backend/core/mixins.py`
  Owns `ImageVariantModelMixin`, variant sync, lookup helpers, and shared
  compatibility methods.
- `backend/core/models.py`
  Owns `ImageVariant`, `BaseImage`, and shared image model fields.
- `backend/astrophotography/models.py`
  Owns astrophotography image variant specs.
- `backend/programming/models.py`
  Owns programming/project image variant specs.
- `backend/shop/models.py`
  Owns shop product/settings image variant specs.
- `backend/users/models.py`
  Owns user image variant specs.

## Key Tests

- `backend/core/tests/test_image_variants.py`
  Shared variant generation, sync, fallback, and compatibility behavior.
- `backend/core/tests/test_tasks.py`
  Core image-processing task behavior.
- `backend/astrophotography/tests/test_models.py`
  Astrophotography image model behavior.
- `backend/shop/tests/test_models.py`
  Shop image variant behavior.
- `backend/users/tests/test_tasks.py`
  User image processing and namespaced variants.

## Search Rules

Start with exact symbols and direct callers:

- `rg -n "def make_thumbnail|make_thumbnail\\(" backend/core backend/astrophotography backend/programming backend/shop backend/users`
- `rg -n "ImageVariantSpec|ViewportWidths" backend/core backend/common backend/astrophotography backend/programming backend/shop backend/users`
- `rg -n "sync_image_variants|get_image_variant_sources|get_image_variant_specs" backend`

Avoid opening `infra/docs/project/analysis/TODO.md` or other large analysis
records unless the user explicitly asks for a phase/TODO analysis task or this
quickstart and targeted code inspection are insufficient.

## Common Invariants

- `ImageVariantSpec.viewport_widths.as_tuple()` is the generated width contract.
- `ViewportWidths.fixed(width)` still represents a set of viewport widths; it
  just deduplicates to one generated width.
- Variant generation should use shared builders in `backend/common/utils/image.py`
  instead of ad hoc image manipulation.
- Required variant roles are handled in `ImageVariantModelMixin`; avoid
  duplicating required-role behavior in model classes.
- Compatibility paths may exist during rollout, but new serving behavior should
  prefer `ImageVariant` rows over legacy image fields.

## Verification

Run backend commands from `backend/`.

- Focused shared tests:
  `cd backend && uv run test core/tests/test_image_variants.py`
- Add model-specific tests when touching model-owned specs or source selection.
