# Django Admin Avatar Zoom/Cropper Implementation Plan

## Goal
Implement a Facebook-style zoom/crop experience in Django admin for the portfolio user avatar so an admin can:

- upload a large source image,
- drag and zoom it inside a fixed avatar frame,
- save the chosen crop,
- keep the original upload for future recropping,
- preserve the existing WebP optimization and cache invalidation flow.

This plan is scoped to `users.User.avatar` first. It should be designed so the same pattern can be reused later for `about_me_image` and `about_me_image2`.

## Current State

### Relevant code paths
- `backend/users/models.py`
  - `User.avatar`
  - `User.avatar_original_image`
  - async save trigger via `process_user_images_task.delay_on_commit(...)`
- `backend/users/tasks.py`
  - `process_user_images_task()` converts uploaded images to WebP and persists optimized files
  - now also clears BE and FE profile caches after async processing completes
- `backend/users/admin.py`
  - custom user change view
  - custom `Media` tab already exists for avatar and portrait fields
- `backend/users/templates/admin/users/user/robust_change_form.html`
  - custom Jazzmin-compatible change form with `Media` tab
- `backend/common/utils/image.py`
  - `convert_to_webp()` currently resizes/compresses but does not crop

### Constraint summary
- The admin already separates translated content from media.
- The avatar is processed asynchronously after model save.
- The system keeps an original file for rollback and alternate serving.
- Cache invalidation must happen after the final cropped/optimized file is persisted.

## Target UX

Inside the Django admin `Media` tab for the user:

1. Admin selects or replaces the avatar image.
2. A cropper preview appears immediately.
3. Admin can:
   - drag image position,
   - zoom in/out,
   - optionally reset crop,
   - preview the final circular or square avatar framing.
4. On save:
   - crop metadata is submitted with the form,
   - backend stores the original upload,
   - backend generates the cropped avatar variant,
   - existing WebP optimization runs on the cropped result,
   - backend and frontend caches are invalidated.

## Recommended Design

### Core decision
Store crop metadata in the database and perform the actual crop server-side.

This is better than trusting a client-generated cropped blob because it:

- keeps a high-quality original for re-editing,
- makes output deterministic,
- integrates cleanly with the current async processing task,
- avoids browser-specific image encoding differences,
- allows future regeneration of different avatar sizes.

## Data Model Changes

Add avatar crop metadata to `users.User`.

Recommended fields:

- `avatar_crop_x = models.FloatField(null=True, blank=True)`
- `avatar_crop_y = models.FloatField(null=True, blank=True)`
- `avatar_crop_width = models.FloatField(null=True, blank=True)`
- `avatar_crop_height = models.FloatField(null=True, blank=True)`
- `avatar_crop_scale = models.FloatField(null=True, blank=True)`

Optional:

- `avatar_crop_version = models.PositiveIntegerField(default=1)`
  - useful if crop math changes later

Notes:
- Store coordinates in the natural pixel space of the original uploaded image if possible.
- If the JS cropper reports values relative to the rendered preview, convert them on the client or server into natural-image coordinates before persistence.
- Keep `avatar_original_image` as the canonical source for recropping after the first optimization pass.

## Admin Form and Widget Design

### New admin form
Create a custom `ModelForm` for `UserAdmin`.

Recommended file:
- `backend/users/forms.py`

Responsibilities:
- expose hidden crop metadata fields,
- validate crop numbers,
- attach a custom cropper widget to `avatar`,
- optionally expose a non-model boolean like `avatar_crop_reset`.

### New widget
Create a custom admin widget for avatar cropping.

Recommended files:
- `backend/users/widgets.py`
- `backend/users/templates/admin/users/widgets/avatar_cropper.html`
- static assets under:
  - `backend/users/static/users/js/avatar_cropper.js`
  - `backend/users/static/users/css/avatar_cropper.css`

Widget responsibilities:
- render current avatar preview,
- render upload input,
- initialize cropper JS when a file is selected,
- maintain hidden inputs for crop metadata,
- support loading previously saved crop values,
- show a square viewport sized to the real avatar target behavior.

### JS library
Use a mature cropper library instead of building custom drag/zoom logic.

Recommended:
- `Cropper.js`

Why:
- stable,
- well documented,
- supports zoom, drag, crop box locking, preview hooks,
- much lower risk than custom pointer math.

### Admin placement
Place the cropper only in the existing `Media` tab of the user admin.

Do not add it to translated language tabs.

## Backend Image Pipeline Changes

### New crop utility
Add a reusable crop helper in the image utilities layer.

Recommended additions:
- `backend/common/utils/image.py`

New function:
- `crop_image_field(image_field, crop_box, output_format=None, max_dimension=None, quality=None)`

Expected behavior:
- open original image,
- apply validated crop box,
- optionally resize to avatar spec,
- return a `ContentFile`,
- keep aspect ratio rules explicit.

### Avatar-specific pipeline
Update `process_user_images_task()` in `backend/users/tasks.py`.

New flow for `avatar`:
1. Load `avatar_original_image` if present, otherwise `avatar`.
2. If crop metadata exists, crop from the original source first.
3. Resize cropped image according to avatar spec.
4. Save final processed avatar file.
5. Keep `avatar_original_image` untouched as source-of-truth original.
6. Invalidate user caches after persistence.

Important:
- Cropping must happen before WebP compression.
- The crop should not overwrite the original upload.
- Re-saving with updated crop metadata and no new file should still regenerate the avatar from `avatar_original_image`.

## Save Flow Changes

### Existing issue to avoid
Today image processing is triggered when the image field itself changes.

For crop support, this is not enough because the admin may:
- keep the same source image,
- only change crop metadata,
- expect a new avatar output.

### Required logic change
Update `User.save()` in `backend/users/models.py` so async processing is triggered when either:

- `avatar` changed, or
- any avatar crop metadata field changed.

Recommended approach:
- extend the `FieldTracker` set to include avatar crop fields, or
- add explicit comparison logic for crop fields.

Result:
- changing crop values without uploading a new file still queues `process_user_images_task(self.pk, ["avatar"])`.

## Validation Rules

Validate crop data both client-side and server-side.

Server-side rules:
- all crop values must be finite numbers,
- width and height must be positive,
- crop box must remain inside source image bounds after normalization,
- reject impossible crop boxes,
- if crop data is missing, fall back to center crop or current no-crop behavior,
- if `avatar_original_image` is missing, fall back to `avatar`.

Suggested fallback:
- if no crop metadata exists, preserve current behavior initially.

## Output Rules

Define avatar output behavior explicitly:

- crop shape in storage: square
- UI preview shape: circular preview overlay is acceptable, but stored image should remain square
- output dimension: use existing avatar optimization spec from `settings.IMAGE_OPTIMIZATION_SPECS["AVATAR"]`

Reason:
- circular display can remain a frontend/CSS concern,
- square image storage is more reusable.

## Migration Plan

### Phase 1: Schema
Create migration for avatar crop fields.

Files:
- `backend/users/models.py`
- new migration under `backend/users/migrations/`

### Phase 2: Admin UI
Add:
- custom form,
- custom widget,
- widget template,
- JS/CSS assets,
- `UserAdmin.form = UserAdminForm`

Files:
- `backend/users/forms.py`
- `backend/users/widgets.py`
- `backend/users/admin.py`
- `backend/users/templates/admin/users/widgets/avatar_cropper.html`
- `backend/users/static/users/js/avatar_cropper.js`
- `backend/users/static/users/css/avatar_cropper.css`

### Phase 3: Processing
Update:
- `backend/common/utils/image.py`
- `backend/users/tasks.py`
- `backend/users/models.py`

### Phase 4: Cache and save semantics
Confirm:
- backend API profile cache clears,
- frontend SSR `profile` tag clears,
- crop-only edits regenerate avatar correctly.

### Phase 5: Tests
Add tests before rollout.

## Test Plan

### Unit tests
Add tests for crop math and image utility behavior.

Recommended targets:
- `backend/common/tests/test_image_utils.py`

Cases:
- valid square crop,
- crop outside image bounds rejected,
- crop metadata omitted,
- crop metadata with floats,
- image already webp,
- crop then resize order.

### Model tests
Recommended target:
- `backend/users/tests/test_models.py`

Cases:
- crop-only metadata change queues image task,
- avatar upload queues task,
- no-op save does not queue task.

### Task tests
Recommended target:
- `backend/users/tests/test_tasks.py`

Cases:
- task crops avatar from original image,
- task preserves original image,
- task overwrites final avatar output,
- task invalidates caches after crop regeneration.

### Admin/form tests
Recommended target:
- `backend/users/tests/test_admin.py`

Cases:
- media tab renders cropper widget,
- saved crop values are present in form,
- changing crop metadata posts correctly,
- cropper remains in `Media` tab only.

### Manual QA
Test in browser:
- upload large portrait image,
- zoom in and out,
- drag to reframe face,
- save,
- refresh admin page and confirm crop persists,
- open public page and confirm avatar updates,
- verify cache refresh on both FE and BE.

## Rollout Notes

### First release scope
Implement cropper for `avatar` only.

Do not include `about_me_image` or `about_me_image2` in the first pass because:
- avatar has the clearest fixed-frame use case,
- it exercises the full admin + async + cache path,
- it reduces migration and UI complexity.

### Second release candidates
After avatar is stable, extend the same pattern to:
- `about_me_image`
- `about_me_image2`

For those fields, prefer focal-point support or aspect-ratio-specific crop presets instead of hardcoding square behavior.

## Risks

### 1. Crop metadata drift
If crop coordinates are stored in preview-space instead of natural-image space, regeneration may be inaccurate.

Mitigation:
- normalize coordinates against natural image dimensions.

### 2. Losing original source
If processing overwrites the only source image, recropping quality degrades permanently.

Mitigation:
- always keep `avatar_original_image` intact.

### 3. Async race conditions
Admin save may finish before the final cropped asset exists.

Mitigation:
- keep cache invalidation at task completion,
- optionally show help text in admin that processed avatar appears after async completion.

### 4. Re-upload edge cases
Uploading a new avatar while stale crop metadata remains may create an invalid crop.

Mitigation:
- reset crop metadata when a new file is chosen unless the widget recalculates immediately.

## Open Decisions

These need confirmation before implementation:

1. Should the avatar crop be strictly square, or should the UI preview be circular while storage remains square?
2. Should crop-only edits regenerate immediately via current async Celery flow, or should avatar crop save synchronously in admin for instant feedback?
3. Do we want a visible live preview of the final frontend avatar size, or just a general crop window?
4. Should a new upload automatically clear existing crop metadata before the user touches the cropper?

## Recommended Default Answers

- store square output,
- show circular preview overlay in admin,
- process asynchronously through the existing task pipeline,
- clear old crop metadata on new upload until the cropper writes fresh values.

## Suggested Implementation Order

1. Add avatar crop model fields and migration.
2. Add custom admin form and cropper widget in the existing `Media` tab.
3. Extend `User.save()` trigger conditions to include crop metadata changes.
4. Add crop utility and update `process_user_images_task()`.
5. Add tests for crop generation, crop-only save, and cache invalidation.
6. Manually QA admin upload, recrop, and frontend refresh behavior.
