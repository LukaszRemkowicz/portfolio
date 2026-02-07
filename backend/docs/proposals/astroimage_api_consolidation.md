# AstroImage API & Serializer Consolidation Proposal

This document outlines the findings regarding `AstroImage` serialization usage and proposes a path forward to optimize performance while reducing redundant code.

## Current State Analysis

### Backend (BE)
- **`AstroImageViewSet`**: Supports `list` (returns `AstroImageSerializerList`) and `retrieve` (returns `AstroImageSerializer`).
- **`AstroImageSerializerList`**: Extremely heavy. Returns technical metadata, descriptions, and equipment strings. Currently returns 20 fields for every image in a list.
- **`AstroImageSerializer`**: Nearly identical to the list counterpart, but returns equipment as nested IDs/Models instead of strings. Surprisingly, it is currently missing the `name` field.
- **Redundancy**: Both serializers manually implement URL signing, tag translation, and `to_representation` logic.

### Frontend (FE)
- **Direct Finding**: The FE **never** calls the detail endpoint (`GET /api/v1/image/<slug>/`).
- **Modal Logic**: When a user clicks an image in the gallery, the `ImageModal` component receives an image object **already present in the store's images array**.
- **Performance Impact**: The frontend store is currently forced to hold full technical metadata and descriptions for every image in the gallery just to support the modal, significantly increasing initial payload size.

---

## Proposed Technical Changes

### 1. Backend: Serializer Inheritance & Optimization

We should introduce a base class to handle shared logic and define distinct field sets.

#### [NEW] `AstroImageBaseSerializer`
- **Shared Logic**: `get_url`, `get_tags`, and `to_representation` (translation handling).
- **Core Fields**: `pk`, `slug`, `name`, `url`, `thumbnail_url`, `tags`, `place`, `capture_date`, `process`.

#### [REFACTOR] `AstroImageSerializerList`
- **Goal**: Lightweight gallery feed.
- **Implementation**: Inherits from `AstroImageBaseSerializer`.
- **Fields**: Limited to Core Fields + `celestial_object`.
- **Optimization**: *Removes* `description`, `camera`, `lens`, `telescope`, `tracker`, `tripod`, `exposure_details`, `processing_details`, and `astrobin_url`.

#### [REFACTOR] `AstroImageSerializer`
- **Goal**: Full technical data for modals/deep-dives.
- **Implementation**: Inherits from `AstroImageBaseSerializer`.
- **Fields**: Everything in Core Fields + full equipment objects, `description`, `exposure_details`, `processing_details`, and `astrobin_url`.

---

## 2. Frontend: Transition to Lazy Loading

To take advantage of the refined BE, the FE should be updated to fetch details on demand.

### Changes in `api/services.ts`
- **[NEW] `fetchAstroImage(slug: string)`**: Add the missing API call to fetch a single image's details.

### Changes in `store/useStore.ts`
- **[NEW] `activeImageDetail` State**: Add a state variable to hold the full details of the currently viewed image.
- **[NEW] `loadImageDetail(slug: string)` Action**: Triggered when opening a modal.

### Changes in `components/common/ImageModal.tsx`
- **Local Loading State**: Display a skeleton or loader for technical details while the secondary API call completes.
- **Data Merging**: Use the basic data from the list (already available) for the header/image immediately, then populate the "Specs" section once the detail API returns.

---

## Benefits

1.  **Lower Initial Latency**: Gallery listing responses will be ~50-70% smaller.
2.  **Cleaner Code**: DRY (Don't Repeat Yourself) principle applied to BE translation and URL logic.
3.  **Scalability**: The backend detail endpoint is ready if we ever decide to create dedicated image pages (good for SEO).
4.  **Consistency**: Ensures fields like `name` are always present in the detail view.
