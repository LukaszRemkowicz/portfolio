# Portfolio Frontend

Modern React + TypeScript frontend for a personal portfolio showcasing astrophotography and programming projects. Built with React 18, TypeScript, React Router, and CSS Modules.

## 🚀 Features

### Core Functionality

- **Dynamic Profile Loading** - Fetches user profile, bio, avatar, and social links from Django API
- **Multi-page Navigation** - Home, Astrophotography, Programming, and Contact pages
- **Responsive Design** - Mobile-first approach with CSS Modules
- **Image Gallery** - Interactive astrophotography gallery with filtering
- **Background Management** - Dynamic background images from backend API

### Technical Features

- **100% TypeScript** - Full type safety across entire codebase
- **React Router v6** - Client-side routing with nested layouts
- **Axios HTTP Client** - API communication with error handling
- **CSS Modules** - Scoped styling with design tokens
- **Webpack 5** - Modern build system with hot reloading
- **Jest Testing** - Unit testing setup with React Testing Library + TypeScript

## 📁 Project Structure

```
src/
├── __tests__/                    # Comprehensive TypeScript test suite
│   ├── About.test.tsx           # About component tests
│   ├── AstroGallery.test.tsx    # Gallery component tests
│   ├── Footer.test.tsx          # Footer component tests
│   ├── Gallery.test.tsx         # Static gallery tests
│   ├── HomePage.test.tsx        # Homepage component tests
│   ├── Navbar.test.tsx          # Navigation tests
│   └── README.md                # Test documentation
├── api/                          # API configuration and services
│   ├── api.ts                   # Axios instance configuration
│   ├── routes.ts                # API endpoints and URL helpers
│   └── services.ts              # API service functions
├── data/                         # Static data
│   └── galleryItems.ts          # Homepage gallery items
├── styles/                       # Organized CSS architecture
│   ├── global/                  # Global styles
│   │   └── index.css           # Reset, typography, base styles
│   ├── components/              # Component-specific styles
│   │   ├── About.module.css    # About component styles
│   │   ├── App.module.css      # Main application layout
│   │   ├── AstroGallery.module.css # Dynamic gallery styles
│   │   ├── Footer.module.css   # Footer component styles
│   │   ├── Gallery.module.css  # Static gallery styles
│   │   └── Navbar.module.css   # Navigation bar styles
│   └── themes/                  # Design system
│       ├── variables.css       # CSS custom properties
│       └── mixins.css          # Utility classes and mixins
├── About.tsx                    # About section component
├── App.tsx                      # Main app with routing
├── AstroGallery.tsx             # Astrophotography page
├── Footer.tsx                   # Footer component
├── Gallery.tsx                  # Homepage gallery
├── Home.tsx                     # Hero section
├── HomePage.tsx                 # Landing page container
├── index.tsx                    # App entry point
├── MainLayout.tsx               # Layout wrapper
├── Navbar.tsx                   # Navigation component
├── Programming.tsx              # Programming projects page
├── Contact.tsx                  # Contact form component
├── PrelectionsAndCourses.tsx    # Prelections section
└── types/                       # TypeScript type definitions
    └── index.ts                 # Centralized type definitions
```

## 🔌 API Integration

### Endpoints Used

- **Profile API**: `GET /api/v1/profile/` - User profile data
- **Background API**: `GET /api/v1/background/` - Main page background
- **Astro Images API**: `GET /api/v1/image/` - Astrophotography gallery

### Fallback Behavior

When API is unavailable, the app gracefully falls back to:

- Static logo: `/logo.png`
- Default portrait: `/portrait_default.png`
- Static gallery items from `galleryItems.js`
- Empty bio content

### Error Handling

- Loading states for all API calls
- Error messages for failed requests
- Graceful degradation when backend is offline

## 🛠️ Development Setup

### Prerequisites

- Node.js 16+
- npm or yarn
- Docker (for containerized development)
- Backend API running (see backend README)

> **Docker Compose Version**: Check your Docker version with `docker --version`. Use `docker compose` (V2) or `docker-compose` (V1) accordingly.

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm start
```

- Runs on `https://portfolio.local:3000/`
- Hot reloading enabled
- Requires backend API at `https://admin.portfolio.local/`

### Production Build

```bash
npm run build
```

- Creates optimized build in `dist/` directory
- Minified CSS and JavaScript
- Creates optimized build in `dist/` directory
- Minified CSS and JavaScript
- Asset optimization

> **Deployment**: For full production deployment with Docker (including backend and Nginx), refer to the **Root README** "Production Deployment" section.

### Testing

#### Local Testing

```bash
npm test
```

- Jest test runner
- React Testing Library for component tests
- CSS Modules mock setup included

#### Docker Testing

```bash
# Run tests in Docker container (Docker Compose V2)
docker compose exec portfolio-fe npm test

# Run tests in Docker container (Docker Compose V1)
docker-compose exec portfolio-fe npm test

# Or run tests in dedicated test container
cd frontend
docker build --target test -t portfolio-frontend-test .
docker run --rm portfolio-frontend-test
```

> **Note**: The Docker build automatically handles SSL certificate issues. The webpack configuration gracefully falls back to HTTP when SSL certificates are not available in the container, but HTTPS is supported in both development and production modes when certificates are present.

## 🐳 Docker Integration

### With Docker Compose (Recommended)

```bash
# Docker Compose V2 (newer versions)
docker compose up --build

# Docker Compose V1 (older versions)
docker-compose up --build
```

- Frontend: `https://portfolio.local/`
- Backend: `https://admin.portfolio.local/`
- Shared network configuration
- Volume mounting for development

### Frontend-Only Docker

```bash
cd frontend
docker build -t portfolio-frontend .
docker run -p 3000:3000 portfolio-frontend
```

## 🎨 Styling Architecture

### CSS Organization

The project uses a well-organized CSS architecture with clear separation of concerns:

```
src/styles/
├── global/                  # Global styles and base setup
│   └── index.css           # Reset, typography, base styles, imports
├── components/              # Component-specific CSS modules
│   ├── About.module.css    # About component styles
│   ├── App.module.css      # Main application layout
│   ├── AstroGallery.module.css # Dynamic gallery styles
│   ├── Footer.module.css   # Footer component styles
│   ├── Gallery.module.css  # Static gallery styles
│   └── Navbar.module.css   # Navigation bar styles
└── themes/                  # Design system and utilities
    ├── variables.css       # CSS custom properties (colors, spacing, etc.)
    └── mixins.css          # Utility classes and mixins
```

### CSS Modules

- **Scoped Styling**: Each component has its own CSS module
- **No Global Conflicts**: Styles are automatically scoped to components
- **Type Safety**: CSS class names are validated at build time

### Design System

- **CSS Variables**: Consistent colors, spacing, typography, and other design tokens
- **Utility Classes**: Reusable mixins for common patterns (flexbox, spacing, etc.)
- **Responsive Design**: Mobile-first approach with consistent breakpoints
- **Dark Mode Support**: Automatic dark mode detection with CSS variables

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

- Link exists in navigation
- Implementation pending

## 🔧 Configuration

### Environment Variables

### Environment Variables

- `API_BASE_URL` - Backend API endpoint (default: `https://admin.portfolio.local`)
- `ENABLE_SHOOTING_STARS` - Toggle shooting stars animation ("true"/"false", default: "true")
- Custom domains configured in nginx

### Build Configuration

- Webpack 5 with modern JavaScript features
- CSS Modules support
- Asset optimization
- Development server with HTTPS

## 🧪 Testing Strategy

### Current Tests

- **Component Tests** - All major components have test coverage
- **API Mocking** - Services are properly mocked for testing
- **Router Testing** - Navigation components tested with React Router
- **Error Handling** - API error scenarios tested
- **User Interactions** - Click events and state changes tested
- **CSS Modules Support** - Identity proxy configured for CSS Modules

### Test Structure

```bash
src/
├── __tests__/                    # Test module
│   ├── AstroGallery.test.jsx     # Gallery component tests
│   ├── HomePage.test.jsx         # Homepage component tests
│   ├── About.test.jsx            # About section tests
│   ├── Navbar.test.jsx           # Navigation tests
│   ├── Gallery.test.jsx          # Static gallery tests
│   ├── Footer.test.jsx           # Footer tests
│   └── README.md                 # Test documentation and guide
└── jest.config.js                # Jest configuration file
```

### Test Configuration

- **Jest Config** (`jest.config.js`) - Main Jest configuration with proper setup
- **Test Match** - Automatically finds tests in `__tests__/` directory
- **CSS Modules** - Identity proxy configured for CSS imports
- **Jest DOM** - Custom matchers imported in each test file for reliability
- **Comprehensive Documentation** - Each test file includes detailed JSDoc comments
- **Test Module README** - Complete guide for running and understanding tests

### Test Documentation

- **Comprehensive JSDoc Comments** - Every test file and individual test is documented
- **Test Module README** (`src/__tests__/README.md`) - Detailed guide for running and understanding tests
- **Mock Strategy** - Clear documentation of how API services are mocked
- **Best Practices** - Guidelines for writing maintainable tests
- **Troubleshooting Guide** - Common issues and solutions
- **Self-contained Tests** - Each test file imports its own dependencies (no separate setup files)

## 🚀 Performance Features

- **Code Splitting** - Route-based lazy loading
- **Image Optimization** - Lazy loading for gallery images
- **API Caching** - Efficient data fetching
- **Bundle Optimization** - Webpack production optimizations

## ✅ Recently Completed

### 🎯 TypeScript Migration (COMPLETED)

- ✅ **Full TypeScript Migration** - 100% TypeScript coverage across entire frontend
- ✅ **23 Files Migrated** - All components, API services, data files, and tests
- ✅ **Type Safety** - Strict TypeScript configuration with comprehensive interfaces
- ✅ **Enhanced Developer Experience** - IntelliSense, autocomplete, error detection
- ✅ **Professional Grade** - Enterprise-level TypeScript codebase
- ✅ **All Tests Passing** - 21/21 tests with full TypeScript support

## 🌐 Deployment Checklist (Production)

> [!IMPORTANT]
> The current SEO and discovery files use `portfolio.local` for development. Before deploying to production, ensure the following manual updates are made:

- **`public/index.html`**:
  - Update `<meta property="og:url" content="..." />`
  - Update `<meta property="og:image" content="..." />`
  - Update `<meta property="twitter:url" content="..." />`
  - Update `<meta property="twitter:image" content="..." />`
  - Update `<script type="application/ld+json">` (Update `@id`, `url`, and `sameAs` links)
- **`public/sitemap.xml`**:
  - Replace all instances of `https://portfolio.local/` with your actual production domain.
- **`public/robots.txt`**:
  - Update the `Sitemap:` directive link.
- **Environment Variables**:
  - Set `API_URL` to your production backend URL (e.g., `https://api.yourdomain.com`).

---

## 📋 TODO / Future Improvements

### ⚡ Priority 1 - Important

- [ ] **Add Equipment Section** - Document astronomical gear and setups

### 🎯 Priority 2 - Nice to Have

- [ ] **Complete Programming Page** - Implement actual programming projects showcase
- [ ] **Filtering by Tags** - Add tag-based filtering to astrophotography gallery for more granular search
- [ ] **React Admin Panel** - Create custom admin dashboard using React Admin or Refine framework
  - Alternative to Django Admin with premium design matching portfolio aesthetic
  - Connect to existing DRF API endpoints
  - Features: Image management, drag-drop ordering, inline editing, better UX
  - Frameworks to consider: [React Admin](https://marmelab.com/react-admin/), [Refine](https://refine.dev/)

---

For backend setup and API documentation, see [Backend README](../backend/README.md).
