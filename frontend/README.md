# landingpage (Frontend)

This is the React frontend for the Portfolio Page project. It fetches dynamic content (profile, portrait, bio, etc.) from the backend API and displays it in a modern, responsive layout.

## Features
- Dynamic loading of profile data (name, bio, avatar) from the backend API
- Responsive, modern design using CSS Modules and design tokens
- Navbar with subpages: Astrophotography, Programming, Contact
- Dockerized for easy local development
- Integrated with nginx and backend via Docker Compose

## API-Driven Content

This app fetches the following from the backend API:
- **Profile** (name, bio, avatar, social links): `/api/v1/profile/`
- **Portrait**: from the `avatar` field in the profile response
- **About text**: from the `bio` field in the profile response

All API endpoints are configured in `src/api/routes.js`.

### Fallback Behavior
- If the API is not set or does not respond, the app will use:
  - `/public/logo.png` for the logo
  - `/public/portrait.jpg` or `/public/portrait.jpeg` for the portrait
  - An empty about text

---

## Design System
Design tokens and reusable UI components are in `src/design-system/`.
- `tokens.js`: Centralized color, spacing, and font variables
- `Button.jsx` + `Button.module.css`: Example of a reusable, themeable button component

---

## Running the Frontend

### With Docker Compose (Recommended)
The easiest way to run the full stack (frontend, backend, nginx, database) is:
```sh
docker-compose up --build
```
- The frontend will be available at `https://portfolio.local/`
- The backend will be available at `https://admin.portfolio.local/`

### Standalone (Development)
```sh
cd frontend
npm install
npm start
```
- By default, the dev server runs at `https://portfolio.local:3000/`
- Make sure the backend is running and accessible at the API base URL in `src/api/routes.js`

---

## Example Usage of Design Tokens
```jsx
import { colors, spacing } from './src/design-system/tokens';

const style = {
  background: colors.primary,
  padding: spacing.md,
};
```

---

For more, see the backend README for API setup. 