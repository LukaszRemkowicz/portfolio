# Translation System Overview

## Purpose

This document explains how content translation works in the backend:

- what components are involved
- how translations are queued and executed
- how translated content is read by the API and admin
- where task state is stored
- what the known operational limits are

Use this document for:

- translation bugs
- stale or missing translated content
- `TranslationTask` admin issues
- Celery translation queue debugging
- adding translation support to new models


## High-Level Flow

The translation system is asynchronous and model-driven.

1. A translatable model is saved in the default language.
2. The model triggers translation tasks for non-default languages that are missing content.
3. A `TranslationTask` row is created with `PENDING`.
4. Celery runs `translation.tasks.translate_instance_task`.
5. `TranslationService` chooses the correct translation method for the model.
6. `TranslationAgent` calls the configured LLM provider and returns translated text.
7. The translated Parler fields are saved.
8. The `TranslationTask` row is marked `COMPLETED` or `FAILED`.
9. API serializers read translated content through `TranslationService.get_translation(...)`.


## Main Components

### 1. `TranslationTask` model

Path: [backend/translation/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/models.py)

This model tracks async translation execution state.

Important fields:

- `task_id`: Celery task id
- `content_type` + `object_id`: generic relation to the translated object
- `language`: target language
- `method`: service method used, for example `translate_astro_image`
- `status`: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`
- `error_message`: failure details when available

Important limitation:

- a row can remain stuck in `PENDING` if the task record is created but Celery never reaches task execution
- in that case Celery failure hooks do not help, because the task body never starts


### 2. Translation-triggering model mixin

Path: [backend/translation/mixins.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/mixins.py)

`AutomatedTranslationModelMixin` is the model-side entry point.

Responsibilities:

- determine supported languages from `PARLER_LANGUAGES`
- skip the default language
- detect whether a translation is already active (`PENDING` / `RUNNING`)
- detect whether target fields are empty and source fields have content
- queue a new Celery translation task when needed

Important methods:

- `trigger_translations(...)`
- `_needs_translation(...)`
- `_trigger_translation(...)`

Key behavior:

- translations are only queued for languages with missing content
- completed/failed tasks are deleted before a new task is queued for the same object/language
- active tasks are not duplicated


### 3. Translation admin mixins

Path: [backend/translation/mixins.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/mixins.py)

Admin-specific helpers:

- `AutomatedTranslationAdminMixin`
  - calls `obj.trigger_translations(...)` after save
  - shows Django admin success messages for queued languages
- `TranslationStatusMixin`
  - adds a translation status column in admin list pages
  - aggregates `TranslationTask` rows into `Not Started`, `In Progress`, `Failed`, `Complete`
- `DynamicParlerStyleMixin`
  - injects generated CSS to prevent deletion of the default language tab in Parler
- `HideNonTranslatableFieldsMixin`
  - hides non-translatable fields when editing non-default language entries in admin


### 4. Celery task wrapper

Path: [backend/translation/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/tasks.py)

`translate_instance_task` is the async execution wrapper.

Responsibilities:

- load model class dynamically from `model_name`
- fetch the instance
- mark task `RUNNING`
- call the correct `TranslationService` method
- mark `COMPLETED` on success
- mark `FAILED` on partial or full failure
- retry on `RequestException`

Helper functions:

- `_update_task_record(...)`
- `_handle_task_failure(...)`
- `_task_result(...)`

Important behavior:

- task state is anchored to the Celery `task_id` when available
- transient HTTP/network failures raise Celery retry instead of immediate hard failure
- partial field-level failures are treated as task failure and saved to `error_message`


### 5. `TranslationService`

Path: [backend/translation/services.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/services.py)

This is the orchestration layer for translation logic.

Responsibilities:

- map models to translatable fields
- choose plain-text vs HTML translation handlers
- skip already translated fields unless `force=True`
- read default-language source content
- validate LLM output before saving
- save Parler translations atomically
- provide a unified read API with fallback behavior

Main concepts:

- `TRANSLATION_CONFIGS`
  - registry of supported models and their translatable fields
- `_parler_ceremony(...)`
  - shared generator for checking existing translation, yielding source text, and writing translated text
- `_run_parler_translation(...)`
  - shared field-level orchestration for most models
- `get_translation(...)`
  - safe read path used by serializers and API output

Supported model methods:

- `translate_astro_image`
- `translate_main_page_location`
- `translate_main_page_background_image`
- `translate_project_image`
- `translate_user`
- `translate_profile`
- `translate_place`
- `translate_parler_tag`

Special cases:

- `translate_place(...)`
  - uses country-aware place-name translation
- `translate_parler_tag(...)`
  - uses short technical tag translation and then regenerates slug locally


### 6. `TranslationAgent`

Path: [backend/translation/agents.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/agents.py)

This is the LLM-facing adapter.

Responsibilities:

- build prompts for translation
- run two-step plain-text translation:
  - literal translation
  - editorial refinement
- preserve HTML by replacing tags with placeholders before translation
- provide specialized prompts for places and tags

Main methods:

- `translate(...)`
- `translate_html(...)`
- `translate_place(...)`
- `translate_tag(...)`

Important behavior:

- HTML is preserved using `[[T0]]`, `[[L0]]`, etc placeholder tokens
- short or unusual strings are supposed to be translated literally, not treated as user requests
- assistant-style refusal/help text is filtered later by `TranslationService`


### 7. LLM provider boundary

Paths:

- [backend/common/llm/protocols.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/llm/protocols.py)
- [backend/common/llm/registry.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/llm/registry.py)

`TranslationService.create_default()` resolves the provider through:

- `settings.TRANSLATION_LLM_PROVIDER`
- `LLMProviderRegistry.get(...)`

This means the translation system is provider-agnostic at the service layer.


### 8. Serializer read path

Path: [backend/common/serializers.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/serializers.py)

`TranslatedSerializerMixin` standardizes how translated content is returned.

Responsibilities:

- read `lang` from the request
- fetch translated content through `TranslationService.get_translation(...)`
- fall back to default language when target translation is missing
- strip old `[TRANSLATION FAILED]` markers and empty CKEditor paragraphs

This is the main reason failed or missing translations do not always surface as empty strings in the public API.


### 9. Translation admin UI

Paths:

- [backend/translation/admin.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/admin.py)
- [backend/translation/views.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/views.py)
- [backend/translation/urls.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/urls.py)

Components:

- `TranslationTaskAdmin`
  - monitor task rows in Django admin
  - safely renders target objects even if translations are incomplete
- `admin_dynamic_parler_css_view`
  - serves generated CSS used by admin mixins


## Which Models Currently Participate

The system currently supports model-level translation for:

- `astrophotography.AstroImage`
- `astrophotography.Place`
- `astrophotography.Tag`
- `astrophotography.MainPageBackgroundImage`
- `astrophotography.MainPageLocation`
- `programming.ProjectImage`
- `users.User`
- `users.Profile`

These models opt in by setting `translation_service_method` and calling `trigger_translations()` in their save flow.


## Language Configuration

Primary settings path: [backend/settings/base.py](/Users/lukaszremkowicz/Projects/landingpage/backend/settings/base.py)

Relevant settings:

- `DEFAULT_APP_LANGUAGE`
- `PARLER_DEFAULT_LANGUAGE_CODE`
- `PARLER_LANGUAGES`
- `TRANSLATION_LLM_PROVIDER`

Important rule:

- the default app language is the source of truth for generated translations
- `TranslationService.get_available_languages()` derives supported targets from `PARLER_LANGUAGES`


## Lifecycle in Detail

### Queueing

When a model using `AutomatedTranslationModelMixin` is saved:

- it checks each supported non-default language
- it checks whether relevant target fields are empty
- if needed, it dispatches `translate_instance_task.delay(...)`
- it stores/updates a `TranslationTask` row with `PENDING`

### Execution

When Celery receives the task:

- it marks the task row `RUNNING`
- it loads the service method dynamically
- it translates field-by-field
- it saves Parler translations
- it marks the task `COMPLETED`

### Failure handling

A task becomes `FAILED` when:

- the instance no longer exists
- the service method raises
- field-level translation returns failures

But a task may remain `PENDING` forever when:

- the row is created
- the Celery task never actually starts
- or execution history is lost before task bookkeeping advances


## Validation and Fallback Rules

`TranslationService` rejects obviously bad LLM output such as:

- empty output
- assistant-style refusal/help text
- other known refusal patterns

It accepts identity matches for proper nouns in some cases:

- if source and target are identical, the source may be accepted as valid unchanged text

Read-time fallback behavior:

- target language first
- then default language
- then any other available language

This fallback keeps the API populated even when translation is incomplete.


## Operational Notes

### 1. `TranslationTask` can become stale

Current design records execution failures well, but does not automatically reconcile old orphaned `PENDING` rows.

Implication:

- admin status can show `In Progress` because of ancient stale task rows

### 2. Public stale content may be unrelated to translation itself

Successful translation does not guarantee immediate frontend freshness if cache invalidation fails elsewhere.

Translation completion and frontend cache invalidation are separate concerns.

### 3. Container logs are not long-term task history

Short Docker log retention can make old task failures impossible to reconstruct later.

Forensic debugging benefits from:

- archived log snapshots
- or dedicated persistent translation lifecycle logs


## How to Add Translation Support to a New Model

1. Make the model translatable with Parler.
2. Add a service method or reuse `translate_model(...)`.
3. Register the model and fields in `TranslationService.TRANSLATION_CONFIGS`.
4. Set `translation_service_method` on the model.
5. Ensure the model calls `trigger_translations()` at the correct save point.
6. Use `TranslatedSerializerMixin` or `TranslationService.get_translation(...)` in API output.
7. Add lifecycle and service tests.


## Useful Files

- [backend/translation/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/models.py)
- [backend/translation/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/tasks.py)
- [backend/translation/services.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/services.py)
- [backend/translation/agents.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/agents.py)
- [backend/translation/mixins.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/mixins.py)
- [backend/translation/admin.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/admin.py)
- [backend/common/serializers.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/serializers.py)
- [backend/translation/tests/test_translation_lifecycle.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/tests/test_translation_lifecycle.py)
- [backend/translation/tests/test_tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/translation/tests/test_tasks.py)
