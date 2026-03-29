# Django Admin Avatar Zoom/Cropper Implementation Plan

## Goal
Implement a Facebook-style zoom/crop experience in Django admin for the portfolio user avatar so an admin can:

- upload a large source image,
- drag and zoom it inside a fixed avatar frame,
- save the chosen crop,
- preserve the existing WebP optimization and cache invalidation flow.

This plan is scoped to `users.User.avatar` first. It should be designed so the same pattern can be reused later for `about_me_image` and `about_me_image2`.

## Current State

### Relevant code paths
- `backend/users/models.py`
  - `User.avatar`
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
- The system currently does **not** keep a separate original avatar source field.
- Cache invalidation must happen after the final cropped/optimized file is persisted.

### Phase 0 findings from codebase review
- `avatar_original_image` does not exist in the current `User` model. It existed historically and was removed in migration `0014_replace_original_image_fields_with_webp_fields.py`.
- The current source-of-truth image is `User.avatar`; derived output is stored in `User.avatar_webp`.
- The current async save trigger only watches `avatar`, `about_me_image`, and `about_me_image2`. Crop-only edits are not yet detectable.
- Current avatar optimization settings come from `settings.IMAGE_OPTIMIZATION_SPECS["AVATAR"]`, which is `dimension=280` and `quality=10`.
- Cache invalidation currently happens on normal model saves via signals and again after async processing completes. The plan must preserve post-processing invalidation and avoid depending on pre-processing invalidation for correctness.

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
   - the widget submits the cropped image as the new `avatar` file,
   - backend saves the cropped avatar source image,
   - existing WebP optimization runs on that saved source file,
   - backend and frontend caches are invalidated.

## Recommended Design

### Core decision
Perform cropping in the admin widget and submit the cropped image as the new source file.

This fits the current architecture because it:

- keeps `avatar` as the source field and `avatar_webp` as the derived optimized field,
- avoids adding crop-state fields to the database,
- integrates cleanly with the current async processing task,
- keeps the backend flow consistent with the other `User` image fields.

## Assessment

I agree with the direction of this plan.

Recommended adjustments before implementation:

- keep the existing architecture: `avatar` as the source field and `avatar_webp` as the optimized derivative,
- crop in the widget and submit the cropped result as the saved `avatar`,
- keep phase 1 focused on backend contract and regeneration semantics before introducing JS complexity,
- resolve the storage/UI shape decision now: square file output, circular admin preview overlay.

## Data Model Changes

No crop metadata fields are needed in the database.

Notes:
- `avatar` remains the canonical source field,
- `avatar_webp` remains the derived optimized field,
- crop state exists only in the browser while editing,
- saving stores the cropped file itself rather than persisted crop instructions.

## Admin Form and Widget Design

### New admin form
Create a custom `ModelForm` for `UserAdmin`.

Recommended file:
- `backend/users/forms.py`

Responsibilities:
- attach a custom cropper widget to `avatar`,
- coordinate the upload field with the cropper component,
- ensure the cropped file is posted as `avatar`.

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
- export the selected crop into a file/blob for form submission,
- show a square viewport sized to the real avatar target behavior.

Reusability requirement:
- the widget must be implemented as a general cropper widget, not an avatar-only widget,
- the widget must be a portable component that can be placed wherever needed in the admin UI,
- field-specific behavior should be driven by configuration such as field name, aspect ratio, preview shape, and output spec,
- Phase 1-4 should wire the reusable widget only to `avatar`,
- the reusable contract must be suitable for later rollout to `about_me_image` and `about_me_image2` in the last stage.

Placement requirement:
- placement in the existing `Media` tab is only the first integration point,
- the component must not depend on the `Media` tab structure to function,
- markup, JS initialization, and hidden-field binding should work if the component is moved to another admin section or template later,
- avoid hardcoded selectors tied to one page layout when a component root container can be used instead.

Initial mount requirement:
- the first real integration point should be in the right sidebar of the admin change page,
- place the component directly under the `Historia` box,
- the component must be visible only while the `Media` tab is active,
- visibility must work the same for both Polish and English language tabs,
- because media is non-translatable, the same component instance/behavior should be shared across translation tabs rather than duplicated per language tab.

### JS library
Use a mature cropper library instead of building custom drag/zoom logic.

Recommended:
- `Cropper.js`

Why:
- stable,
- well documented,
- supports zoom, drag, crop box locking, preview hooks,
- much lower risk than custom pointer math.

JavaScript constraint:
- do not use `jQuery`,
- do not use `django.jQuery`,
- do not use legacy Django admin JS patterns for DOM binding,
- implement the widget behavior in modern vanilla JavaScript scoped to the component root.

### Admin placement
Place the cropper only in the existing `Media` tab of the user admin.

Do not add it to translated language tabs.

## Backend Image Pipeline Changes

### Avatar-specific pipeline
Update `process_user_images_task()` in `backend/users/tasks.py`.

New flow for `avatar`:
1. Load `avatar`.
2. Assume the saved `avatar` is already cropped by the widget.
3. Resize/optimize according to avatar spec.
4. Save final processed avatar file to `avatar_webp`.
5. Keep `avatar` untouched as the source image.
6. Invalidate user caches after persistence.

Important:
- Cropping happens before backend optimization because the widget submits the cropped file.
- The crop should not overwrite `avatar`.
- The backend remains responsible only for optimized derivative generation.

## Save Flow Changes

### Existing issue to avoid
Today image processing is triggered when the image field itself changes.

### Required logic change
No crop-field trigger is needed.

The widget must ensure that saving a new crop results in a new uploaded `avatar` file so the existing save trigger continues to work.

Result:
- submitting a cropped avatar file queues `process_user_images_task(self.pk, ["avatar"])` through the existing mechanism.

## Validation Rules

Validate crop data both client-side and server-side.

Client-side rules:
- crop area must remain within image bounds,
- exported crop must respect the configured aspect ratio,
- reset must restore the default cropper state for the currently selected image.

Server-side rules:
- validate the uploaded file as a normal image upload,
- if `avatar` is missing, preserve current empty-image behavior.

Suggested fallback:
- if the widget is not used, preserve current behavior and treat the upload as a normal avatar image.

## Output Rules

Define avatar output behavior explicitly:

- crop shape in storage: square
- UI preview shape: circular preview overlay is acceptable, but stored image should remain square
- output dimension: use existing avatar optimization spec from `settings.IMAGE_OPTIMIZATION_SPECS["AVATAR"]`

Reason:
- circular display can remain a frontend/CSS concern,
- square image storage is more reusable.

## Delivery Workflow Requirements

These requirements apply to every implementation phase in this document:

- each implementation phase starts only after explicit approval,
- each implementation phase ends with all tests green via `poetry run test`,
- each implementation phase prepares a commit message using the local skill/process for commit-message generation,
- after a phase is complete, work stops and waits for approval before the next phase begins.

Exception:
- the analysis stage is not an implementation phase, so it does not require `poetry run test` or a commit message.

## Phased Delivery Plan

### Pre-Phase: Analysis and decision lock
Lock the implementation contract before coding.

Scope:
- review current model, admin, async image-processing, and cache invalidation flow,
- confirm avatar output shape and preview behavior,
- confirm `avatar` remains the canonical source field and `avatar_webp` remains the derived field,
- confirm rollout scope is `avatar` only.

Decisions to freeze:
- storage output is square,
- admin preview may be circular,
- processing stays asynchronous through Celery,
- the widget submits the cropped file as `avatar`,
- backend optimization uses `avatar` as the source and writes optimized output to `avatar_webp`.

Deliverables:
- agreed implementation contract,
- agreed phase boundaries,
- agreed acceptance criteria for phase completion.

Exit criteria:
- output shape and save semantics are explicitly agreed,
- no crop-state database fields are introduced,
- no migration is created,
- cropped avatar upload is the agreed save mechanism,
- no unresolved question blocks implementation,
- approval is given to start Phase 1.

### Phase 1: Admin component contract
Introduce the reusable admin component and mount it in the correct place before adding full cropper behavior.

Scope:
- add custom `ModelForm`,
- add reset semantics,
- design a reusable widget API that can support multiple `User` image fields later,
- design the widget/template contract so the component can be moved to a different admin page location later with minimal or no JS changes,
- connect `UserAdmin.form`,
- render the first mounted component under `Historia` in the right sidebar,
- make the mounted component visible only when the `Media` tab is active.

Files:
- `backend/users/forms.py`
- `backend/users/widgets.py`
- `backend/users/admin.py`
- `backend/users/templates/admin/users/widgets/avatar_cropper.html`

Required tests:
- run full `poetry run test`,
- verify admin form posts the cropped avatar file correctly,
- verify the component is mounted under `Historia`,
- verify the component is visible only when the `Media` tab is active,
- verify the behavior is the same for Polish and English tabs.

Approval gate:
- pause after this phase and wait for approval before starting Phase 2.

Commit message:
- prepare a commit message using the project skill/process for commit-message generation.

Exit criteria:
- admin form posts the cropped avatar file correctly,
- existing avatar management remains functional,
- widget API is reusable for other image fields without redesign,
- component is portable and not coupled to one template section structure,
- first integration is under `Historia` in the sidebar,
- cropper UI is visible only in the `Media` tab across language tabs.

### Phase 2: Interactive cropper UI
Add the JavaScript cropper experience and align it with the backend contract.

Scope:
- integrate `Cropper.js`,
- initialize cropper state for the selected file,
- export the crop result to a file/blob assigned to the form submission,
- reset stale crop values on new upload,
- keep the JS/component structure reusable for other image fields,
- scope all DOM behavior to a component root so the component can be relocated later,
- bind component visibility to admin tab state rather than language-tab state,
- use modern vanilla JS only, with no `jQuery` dependency,
- show a square crop area with circular preview overlay if desired.

Files:
- `backend/users/static/users/js/avatar_cropper.js`
- `backend/users/static/users/css/avatar_cropper.css`
- `backend/users/templates/admin/users/widgets/avatar_cropper.html`

Required tests:
- run full `poetry run test`,
- verify upload, zoom, drag, reset, and resave flows work,
- verify the component toggles correctly with `Media` tab activation,
- verify switching between Polish and English does not break visibility or cropper behavior,
- verify new uploads do not reuse stale crop state.

Approval gate:
- pause after this phase and wait for approval before starting Phase 3.

Commit message:
- prepare a commit message using the project skill/process for commit-message generation.

Exit criteria:
- upload, zoom, drag, reset, and resave flows work in admin,
- widget implementation is reusable even though only `avatar` is enabled in this release,
- component can be moved to another admin page location without redesigning the JS contract,
- first mount location under `Historia` behaves correctly,
- new uploads do not reuse stale crop state.

### Phase 3: Image pipeline and validation
Keep backend processing focused on derivative generation and validation of the uploaded cropped file.

Scope:
- keep backend image processing centered on `convert_to_webp()` and derivative generation,
- validate uploaded cropped files through existing image handling,
- preserve `avatar` untouched,
- keep cache invalidation after final processed file persistence.

Files:
- `backend/users/tasks.py`

Required tests:
- run full `poetry run test`,
- verify uploaded cropped avatar files are processed into `avatar_webp`,
- verify `avatar` remains untouched,
- verify cache invalidation still occurs after async completion.

Approval gate:
- pause after this phase and wait for approval before starting Phase 4.

Commit message:
- prepare a commit message using the project skill/process for commit-message generation.

Exit criteria:
- regenerated avatar is derived from the uploaded `avatar` file,
- cache invalidation still happens after async completion.

### Phase 4: Multi-field widget refinement
Expand the reusable admin image cropper so one widget can target multiple image fields from backend-provided configuration.

Scope:
- keep a single reusable `admin_image_cropper` component in the sidebar,
- add a dropdown for selectable image fields,
- populate the dropdown from backend-provided field definitions rather than hardcoding options in JS,
- prefer a class attribute or equivalent admin-level configuration as the source of supported crop fields,
- allow field-specific config such as label, input id, preview shape, output size, and future aspect-ratio rules,
- add a widget-level `Apply` button that writes the cropped file into the currently selected file input,
- keep normal admin save buttons as the only mechanism that persists the model,
- do not render separate cropper widgets for each file field.

Files:
- `backend/users/admin.py`
- `backend/users/templates/admin/users/widgets/admin_image_cropper.html`
- `backend/users/static/users/js/admin_image_cropper.js`
- `backend/users/static/users/css/admin_image_cropper.css`

Required tests:
- run full `poetry run test`,
- verify the dropdown options are rendered from backend config,
- verify switching selected field updates the widget target correctly,
- verify `Apply` updates the selected field input without submitting the admin form,
- verify the widget still remains visible only on the `Media` tab.

Approval gate:
- pause after this phase and wait for approval before starting Phase 5.

Commit message:
- prepare a commit message using the project skill/process for commit-message generation.

Exit criteria:
- one widget can target multiple configured image fields,
- field list is backend-driven,
- widget-level `Apply` updates the selected input without saving the model,
- no duplicate cropper widgets are needed in the UI.

### Phase 5: Automated tests
Cover the contract from utility layer through admin behavior.

Scope:
- image utility tests,
- model save-trigger tests,
- Celery task processing tests,
- admin/form rendering and POST tests.

Required tests:
- run full `poetry run test`,
- ensure new and updated tests are green in the full suite.

Approval gate:
- pause after this phase and wait for approval before starting Phase 6.

Commit message:
- prepare a commit message using the project skill/process for commit-message generation.

Exit criteria:
- crop math and fallback behavior are covered,
- cropped upload behavior is covered,
- cache invalidation assertions are covered,
- admin integration is covered.

### Phase 6: Manual QA and rollout
Validate end-to-end behavior before extending the pattern to other fields.

Scope:
- browser QA in admin,
- verify delayed async update behavior,
- verify public avatar refresh after cache invalidation,
- confirm recropping works against the current `avatar` source file.

Required validation:
- if code changes are made in this phase, run full `poetry run test`,
- complete manual QA checklist and record the result.

Approval gate:
- pause after this phase for rollout approval or next-scope approval.

Commit message:
- only required if this phase includes code changes.

Exit criteria:
- admin workflow is stable,
- frontend displays updated avatar,
- no regression in existing avatar optimization flow.

### Final stage extension
After the avatar rollout is stable, extend the same reusable widget and backend pattern to:

- `about_me_image`
- `about_me_image2`

Requirements for the final stage:
- reuse the same widget/component contract rather than introducing separate field-specific implementations,
- keep field-specific differences configurable,
- run full `poetry run test`,
- prepare a commit message,
- stop for approval before release.

## Test Plan

### Unit tests
Add tests for crop math and image utility behavior.

Recommended targets:
- `backend/common/tests/test_image_utils.py`

Cases:
- valid square crop export,
- crop outside image bounds rejected by widget logic,
- image already webp,
- cropped upload then backend optimization order.

### Model tests
Recommended target:
- `backend/users/tests/test_models.py`

Cases:
- avatar upload queues task,
- no-op save does not queue task.

### Task tests
Recommended target:
- `backend/users/tests/test_tasks.py`

Cases:
- task processes uploaded cropped avatar from `avatar`,
- task preserves `avatar`,
- task overwrites final avatar output,
- task invalidates caches after crop regeneration.

### Admin/form tests
Recommended target:
- `backend/users/tests/test_admin.py`

Cases:
- media tab renders cropper widget,
- cropper widget is mounted under `Historia`,
- cropper widget is hidden outside the `Media` tab,
- cropper widget remains available when switching Polish/English tabs,
- dropdown renders backend-provided crop field options,
- widget-level `Apply` updates the selected field input without submitting the form,
- cropped avatar submission posts correctly,
- cropper visibility remains tied to `Media` tab only.

### Manual QA
Test in browser:
- upload large portrait image,
- zoom in and out,
- drag to reframe face,
- save,
- refresh admin page and confirm crop persists,
- refresh admin page and confirm saved cropped avatar is displayed,
- open public page and confirm avatar updates,
- verify cache refresh on both FE and BE.

## Rollout Notes

### First release scope
Ship the reusable widget with backend-driven field selection, but keep the initial verified crop behavior focused on `avatar`.

Why:
- the widget architecture can support multiple fields immediately,
- `avatar` remains the first fully validated crop flow,
- this keeps rollout risk lower while avoiding duplicated UI.

### Second release candidates
After avatar is stable, enable verified crop flows for:
- `about_me_image`
- `about_me_image2`

For those fields, prefer focal-point support or aspect-ratio-specific crop presets instead of hardcoding square behavior, but reuse the same dropdown-driven widget.

## Risks

### 1. Crop export mismatch
If the widget exports a crop that does not match the preview, the saved avatar may differ from what the admin selected.

Mitigation:
- use a mature cropper library,
- keep preview and export behavior driven by the same cropper state,
- test exported output against expected framing.

### 2. Losing original source
If processing overwrites the only source image, recropping quality degrades permanently.

Mitigation:
- never overwrite the uploaded source during backend optimization,
- store the cropped result in `avatar` and only generate the optimized derivative in `avatar_webp`.

### 3. Async race conditions
Admin save may finish before the final cropped asset exists.

Mitigation:
- keep cache invalidation at task completion,
- optionally show help text in admin that processed avatar appears after async completion.

### 4. Re-upload edge cases
Uploading a new avatar while stale cropper UI state remains may create an invalid or misleading preview.

Mitigation:
- fully reset cropper state when a new file is chosen.

## Decision Resolution

Recommended defaults for implementation:

- store square output,
- show circular preview overlay in admin,
- process asynchronously through the existing task pipeline,
- provide a live preview inside the widget,
- clear old cropper state on new upload until the cropper initializes the new file.

## Suggested Implementation Order

1. Freeze phase 0 decisions.
2. Implement phase 1 image pipeline changes.
3. Implement phase 2 admin form contract.
4. Implement phase 3 interactive cropper UI.
5. Implement phase 4 automated tests.
6. Complete phase 5 manual QA before rollout.
