# Django Admin Image Cropper Mechanism

## Purpose
This document explains how the reusable Django admin image cropper works today.

It is intended as:
- implementation context for future engineers,
- architectural context for future LLM sessions,
- a technical reference for extending the cropper to new model fields.

## Scope
Current implementation covers the `users.User` admin and these source image fields:

- `avatar`
- `about_me_image`
- `about_me_image2`

The cropper is a single reusable sidebar widget that can switch between those fields.

## High-Level Contract

### Source-of-truth model fields
The system does not persist crop coordinates in the database.

Instead:
- the cropper works entirely in the browser,
- the cropped result is written back into the selected source file input,
- the normal Django form submission persists that source image field.

For `users.User`:
- `avatar` is the source field
- `avatar_webp` is the derived optimized field
- `about_me_image` is the source field
- `about_me_image_webp` is the derived optimized field
- `about_me_image2` is the source field
- `about_me_image2_webp` is the derived optimized field

### Derived image generation
After save, the existing async image pipeline still runs:

1. Django admin saves the selected source field.
2. `User.save()` detects changed image fields.
3. `process_user_images_task.delay_on_commit(...)` is scheduled.
4. Celery regenerates the derived WebP field for the changed source field.
5. cache invalidation runs after image processing.

This means the cropper does not replace the existing backend image-processing architecture. It only changes what source file is submitted.

## Main Files

### Backend config and types
- [backend/users/types.py](../../backend/users/types.py)
  - `CropperFieldConfig`
  - `CropperPreviewShape`
- [backend/settings/base.py](../../backend/settings/base.py)
  - `USER_ADMIN_CROPPER_FIELD_CONFIGS`

### Admin integration
- [backend/users/admin.py](../../backend/users/admin.py)
  - injects cropper context into the change view
- [backend/users/templates/admin/users/user/robust_change_form.html](../../backend/users/templates/admin/users/user/robust_change_form.html)
  - mounts the widget in the sidebar
- [backend/users/templates/admin/users/widgets/admin_image_cropper.html](../../backend/users/templates/admin/users/widgets/admin_image_cropper.html)
  - widget markup and JSON payload

### Frontend behavior
- [backend/users/static/users/js/admin_image_cropper.js](../../backend/users/static/users/js/admin_image_cropper.js)
  - field switching
  - image loading
  - canvas rendering
  - drag / zoom / reset
  - crop export and apply
- [backend/users/static/users/css/admin_image_cropper.css](../../backend/users/static/users/css/admin_image_cropper.css)
  - widget styling
  - viewport ratio
  - preview overlay shape

### Media serving and tests
- [backend/settings/urls.py](../../backend/settings/urls.py)
  - admin-domain media serving
  - `safe_serve()`
- [backend/core/tests/test_admin_media_urls.py](../../backend/core/tests/test_admin_media_urls.py)
  - regression coverage for admin media URL behavior
- [backend/users/tests/test_admin.py](../../backend/users/tests/test_admin.py)
  - cropper admin integration coverage
- [backend/users/tests/test_tasks.py](../../backend/users/tests/test_tasks.py)
  - backend regeneration coverage

## Settings-Backed Field Configuration

### Why config lives in settings
The cropper field instances are defined in Django settings so admin does not own the configuration itself.

Current setting:
- `USER_ADMIN_CROPPER_FIELD_CONFIGS`

Each entry is a `CropperFieldConfig` with:
- `field_name`
- `label`
- `input_id`
- `spec_method`
- `preview_shape`
- `crop_aspect_ratio`

### Shape typing
`preview_shape` is not a free string.

It uses `CropperPreviewShape`:
- `CIRCLE`
- `ROUNDED_SQUARE`

Admin serializes the enum value for the browser widget.

### Current effective field config
- `avatar`
  - preview shape: `circle`
  - crop ratio: `1.0`
  - output spec: `get_avatar_spec()`
- `about_me_image`
  - preview shape: `rounded-square`
  - crop ratio: `1.0`
  - output spec: `get_portrait_spec()`
- `about_me_image2`
  - preview shape: `rounded-square`
  - crop ratio: `1.0`
  - output spec: `get_portrait_spec()`

## Admin Rendering Flow

### Change view context
`UserAdmin.change_view()` does this:

1. Loads the current `User` object.
2. Iterates over `settings.USER_ADMIN_CROPPER_FIELD_CONFIGS`.
3. Reads the current source image name and URL from the model field.
4. Resolves output size from the configured `spec_method`.
5. Pushes a normalized JSON-friendly structure into `extra_context["admin_image_cropper"]`.

The admin template then renders:
- widget markup,
- JSON config payload via `json_script`,
- JS and CSS assets.

### Sidebar placement
The widget is mounted in the right sidebar under the standard admin submit/history block.

It is only visible while the `Media` tab is active.

## Browser-Side Mechanism

### Initialization
`admin_image_cropper.js`:

1. finds the component root,
2. parses the JSON field config payload,
3. builds a `fieldConfigMap`,
4. initializes internal state,
5. loads the default field (`avatar`).

### Field switching
When the selected field changes:

1. widget state updates `currentFieldName`
2. live field select element is synchronized
3. viewport ratio and output dimensions are updated
4. previous pending image loads are invalidated
5. current preview is cleared
6. the selected field source is resolved:
   - if a new unsaved file is already in the input, load that file
   - else if the persisted field has a URL, load that URL
   - else show empty preview

### Why live select lookup is used
The widget does not trust a startup-time reference to the dropdown element.

The admin/theme can replace or rerender DOM fragments after load. Because of that, the cropper queries the live select node when syncing selected values.

This avoided a bug where the dropdown visually changed but the cropper kept listening to a stale DOM element.

### Canvas interaction
The cropper currently uses a canvas-based implementation:

- image is rendered into a fixed viewport
- pointer drag changes `offsetX` / `offsetY`
- zoom slider changes `zoom`
- reset recalculates base scale and clears offsets

There is no persisted crop state in the database.

### Export and apply
When the user clicks `Apply`:

1. the cropper exports the current viewport to an off-screen canvas
2. export dimensions come from backend-provided `output_width` / `output_height`
3. the exported blob becomes a `File`
4. the widget writes that file into the selected source input using `DataTransfer`
5. the form is not submitted automatically

The normal Django admin save buttons still control model persistence.

## Media Loading Rules

### Current image loading
The widget loads persisted images from `current_image_url`, for example:

- `/media/avatars/...`
- `/media/about_me_images/...`

These are loaded directly in the browser via `new Image()`.

### Admin-domain media serving
On `admin.portfolio.local`, media is served by `safe_serve()` in [backend/settings/urls.py](../../backend/settings/urls.py).

Allowed:
- `about_me_images/...`
- `avatars/...`

Blocked:
- `logs/...`
- `images/...`

### Important regression that already happened
An earlier version of `safe_serve()` blocked any path containing the substring `"images/"`.

That accidentally blocked:
- `about_me_images/...`

Effect:
- avatar previews worked
- `about_me_image` and `about_me_image2` previews failed with `404`

Current fix:
- block only path prefixes:
  - `logs/`
  - `images/`

Regression test:
- [backend/core/tests/test_admin_media_urls.py](../../backend/core/tests/test_admin_media_urls.py)

## Image Spec Interaction

The cropper config uses `spec_method` to resolve the effective output target:

- `get_avatar_spec()`
- `get_portrait_spec()`

Those methods currently return `ImageSpec` objects from `settings.IMAGE_OPTIMIZATION_SPECS`.

The cropper uses those specs indirectly to calculate:
- `output_width`
- `output_height`

The async backend pipeline still uses the same model methods when creating derived WebP images.

## Important Constraints

### No database crop metadata
The system intentionally does not store:
- crop x/y
- crop width/height
- zoom level

Implications:
- reopening admin does not restore a previous crop session
- crop state is temporary until `Apply`
- persisted source image becomes the cropped source of truth

### No jQuery
The cropper is implemented in modern vanilla JavaScript only.

Do not reintroduce:
- `jQuery`
- `django.jQuery`
- old Django admin inline JS patterns tied to jQuery helpers

### Portable component
The current first mount point is the user admin sidebar, but the cropper is designed as a reusable component.

Portability assumptions:
- backend passes field config
- template renders one component root
- JS initializes from data attributes and JSON payload

The component should not depend on the current sidebar position as part of its core contract.

## Failure Modes To Remember

### 1. Dropdown changes but preview does not
Likely causes:
- stale DOM reference to the select element
- pending older image load overriding the new field selection
- cached old JS asset

Current mitigations:
- live select lookup
- load request invalidation via `loadRequestId`
- asset versioning in the admin template

### 2. Preview stays empty for a specific field
Likely causes:
- media URL returns `404`
- wrong `input_id`
- field has no file persisted and no unsaved file selected

Check:
- browser console network tab
- model field `.name` and `.url`
- `safe_serve()` behavior on admin domain

### 3. Backend appears broken after frontend work
Common cause seen during development:
- backend restart overlapped with local requests
- transient `502` or source-map noise in devtools was misread as the main bug

Check:
- `poetry run test`
- backend health endpoint
- actual server logs for `/admin/...` and `/media/...`

## Extension Guidance

If a new model field should use the cropper:

1. add a new `CropperFieldConfig` instance to `USER_ADMIN_CROPPER_FIELD_CONFIGS`
2. make sure the admin form exposes a stable file input id
3. ensure the model has a compatible image spec method
4. ensure admin-domain media serving allows that media path
5. verify the existing async derivative pipeline supports the field, or extend it
6. add admin and backend regression coverage

If a field needs a non-square crop:

1. set a different `crop_aspect_ratio`
2. choose the correct `preview_shape`
3. confirm output width/height math is acceptable
4. verify frontend display expectations for that field

## Testing Guidance

Minimum verification for cropper changes:

1. `poetry run test`
2. manual admin check on `admin.portfolio.local`
3. switch dropdown across all configured fields
4. confirm preview loads for persisted files
5. confirm `Apply` writes back to the correct file input
6. save model and confirm derived WebP regeneration still works

## Current Status
As of March 29, 2026:

- reusable multi-field cropper exists
- field config type is centralized in `users/types.py`
- cropper field instances are centralized in Django settings
- shape is typed with `CropperPreviewShape`
- admin-domain media serving bug for `about_me_images` is fixed
- backend test suite is green
