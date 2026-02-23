# Portfolio Frontend

Modern React + TypeScript frontend for a personal portfolio showcasing astrophotography and programming projects. Built with React 18, TypeScript, React Router, and CSS Modules.

## 🚀 Features

### Core Functionality

- **Dynamic Profile Loading** - Fetches user profile, bio, avatar, and social links from API
- **Multi-page Navigation** - Home, Astrophotography, Programming, and Contact pages
- **Responsive Design** - Mobile-first approach with CSS Modules
- **Image Gallery** - Interactive astrophotography gallery with filtering
- **Background Management** - Dynamic background images from backend API

### Technical Features

- **Vite** - Next-generation frontend tooling for ultra-fast development (HMR)
- **100% TypeScript** - Full type safety across entire codebase
- **TanStack Query (v5)** - Powerful server-state management with advanced caching
- **React Router v6** - Client-side routing with nested layouts
- **React Helmet Async** - Dynamic SEO management and metadata injection
- **Axios HTTP Client** - Robust API communication with interceptors
- **CSS Modules** - Scoped styling with design tokens
- **Sentry** - Production error tracking and telemetry
- **Vite PWA** - Progressive Web App support with offline capabilities

## 🔌 API Integration

### Endpoints Used

All API routes and endpoint configurations are centrally managed in `src/api/routes.ts` and `src/api/constants.ts`. Refer to these files for the complete and up-to-date list of available backend REST connections.

### Fallback Behavior

When the API is unavailable or `API_URL` is not set, the app gracefully falls back to:

- **Default API**: `https://api.portfolio.local` (Configured in `api/constants.ts`)
- Static logo: `/logo.png`
- Default portrait: `/portrait_default.png`
- Static gallery items from `galleryItems.js`
- Empty bio content

### Error Handling

- Loading states using Skeleton components
- Error messages for failed requests
- Graceful degradation when backend is offline

## 🛠️ Development Setup

### Prerequisites

- Node.js 18+
- npm (recommended) or yarn
- Docker (for containerized development)
- Backend API running (see backend README)

> **Docker Compose Version**: Use `docker compose` (V2) for all commands.

### Installation

```bash
# Clone the repository
# Navigate to frontend
cd frontend
npm install
```

### Development Server

#### 🐳 Using Docker (Recommended)

```bash
# From root directory
docker compose up
```

- Frontend: `https://portfolio.local/`
- API: `https://api.portfolio.local/`
- Admin: `https://admin.portfolio.local/`

#### 💻 Native (Without Docker)

You can run the frontend directly on your host machine:

1.  **Environment Variables**: Set your API URL (defaults to production if unset):
    ```bash
    export API_URL="http://localhost:8000"
    ```
2.  **Start the App**:
    ```bash
    npm run dev
    ```

- URL: `http://localhost:3000`

### Production Build

```bash
npm run build
```

- Compiles TypeScript and builds optimized assets via Vite (Rollup)
- Minified CSS and JavaScript
- Route-based lazy-loading and dynamic asset optimization
- Configures PWA service workers

> **Deployment**: For full production deployment with Docker, refer to the **Root README**.

### Testing

#### E2E Testing (Playwright)

```bash
npm run test:e2e
```

- Full end-to-end verification of gallery filtering, travel highlights, image modals, and routing.
- Emulates Chromium browsers internally to test real user interactions.

#### Unit Testing (Jest)

```bash
npm test
```

- Jest test runner with React Testing Library
- Comprehensive coverage for hooks (TanStack Query) and components
- React 18 `act` support
- Mock service workers and DOM abstraction

#### Docker Testing

```bash
# Run tests in Docker container
docker compose exec portfolio-fe npm test

# Or run tests in dedicated test container
cd frontend
docker build --target test -t portfolio-frontend-test .
docker run --rm portfolio-frontend-test
```

> **Note**: The Vite dev server automatically handles hot reloading. HTTP is utilized gracefully as a proxy fallback when SSL configurations are missing.

## 🐳 Docker Integration

### With Docker Compose (Recommended)

```bash
docker compose up --build
```

- Shared network configuration
- Volume mounting for instant HMR in dev
- Internal Nginx proxy for production parity

### Frontend-Only Docker

```bash
cd frontend
docker build -t portfolio-frontend .
docker run -p 3000:3000 portfolio-frontend
```

## 🎨 Styling Architecture

### Design System

- **CSS Variables**: Consistent colors, spacing, typography, and other design tokens
- **Utility Classes**: Reusable mixins for common patterns (flexbox, spacing, etc.)
- **Responsive Design**: Mobile-first approach with consistent breakpoints
- **Dark Mode Support**: Automatic dark mode detection with CSS variables
- **Skeleton Screens**: Shimmer animations for smooth loading transitions

### Component Styles

All component styles are organized in `styles/components/` directory:

- **Modular Structure**: Each component has its dedicated CSS file
- **Consistent Naming**: All files follow `ComponentName.module.css` convention
- **Easy Maintenance**: Clear separation makes styles easy to find and modify

## 📱 Pages & Components

### HomePage (`/`)

- Hero section with dynamic background
- User profile display
- Quick gallery preview
- About section with bio

### Astrophotography (`/astrophotography`)

- Full-screen image gallery
- Filter by celestial object type
- Modal lightbox for image details
- Equipment and processing info

### Programming (`/programming`)

- Currently shows "under construction"
- Planned: Project showcase with screenshots
- Technology stacks and links

### Contact (`/contact`)

- Full implementation with validation and spam protection
- Integrated with backend API

## 🔧 Configuration

### Environment Variables

The frontend application requires specific `VITE_` prefixed variables at build/runtime. When using Docker Compose, these are automatically aliased from your host's environment:

- `VITE_API_URL` - Backend API endpoint (mapped from `API_URL`)
- `VITE_GA_TRACKING_ID` - Google Analytics ID (mapped from `GA_TRACKING_ID`)
- `VITE_ENABLE_GA` - Analytics toggle (mapped from `ENABLE_GA`)
- `VITE_SENTRY_DSN_FE` - Sentry DSN (mapped from `SENTRY_DSN_FE`)
- `VITE_ENVIRONMENT` - Deployment mode (mapped from `ENVIRONMENT`)

## 🚀 Performance Features

- **TanStack Query** - Efficient data fetching, caching, and state synchronization
- **Code Splitting** - Automatic route-level chunking via Vite/Rollup
- **Lazy Loading** - Native lazy loading for off-screen images
- **Hover Prefetching** - Passive prefetching of query data on interaction
- **Skeleton States** - Improved Perceived Performance during data fetching

## ✅ Recently Completed

### 🎯 Vite & State Migration

- [x] Migrated from Webpack 5 to **Vite 6**
- [x] Implemented **TanStack Query** for all server-state
- [x] Added **React Helmet Async** for dynamic SEO
- [x] Configured **Vite PWA** with service workers
- [x] Added **Skeleton components** for core loading states
- [x] Implemented **Playwright** for E2E testing

## 🌐 Deployment Checklist (Production)

> [!NOTE]
> All SEO and discovery files (`index.html`, `sitemap.xml`, `robots.txt`) are now **automatically configured** during the build process using the `inject-metadata.sh` script.

To deploy to production, you only need to ensure the following environment variables are correctly set in your CI/CD or production `docker-compose.yml`:

- **`SITE_DOMAIN`**: Your production domain (e.g., `yourdomain.com`). Used to inject OG tags, Twitter metadata, and generate the sitemap.
- **`API_URL`**: Your production backend URL (e.g., `https://api.yourdomain.com`).
- **`SENTRY_DSN_FE`**: Your frontend Sentry DSN for error tracking.
- **`ENVIRONMENT`**: Set to `production` to enable production-only optimizations and telemetry.

---

## 📋 TODO / Future Improvements

### ⚡ Priority 1 - Important

- [ ] **Google Analytics Environment Storage** - Move GA measurement ID to environment variables for better security and portability.
- [ ] **Add Equipment Section** - Document astronomical gear and setups

### 🎯 Priority 2 - Nice to Have

- [x] **Complete Programming Page** - Portfolio projects showcase fully implemented.
- [x] **Contact Form** - Implementation with honeypot and multi-channel notification.
- [x] **Filtering by Tags** - Add tag-based filtering to astrophotography gallery
- [ ] **React Admin Panel** - Create custom admin dashboard using React Admin or Refine framework
  - Alternative to Django Admin with premium design matching portfolio aesthetic
  - Connect to existing DRF API endpoints
  - Features: Image management, drag-drop ordering, inline editing, better UX
  - Frameworks to consider: [React Admin](https://marmelab.com/react-admin/), [Refine](https://refine.dev/)

---

For backend setup and API documentation, see [Backend README](../backend/README.md).
