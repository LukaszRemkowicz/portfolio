import { createRoot } from 'react-dom/client';
import * as Sentry from '@sentry/react';
import App from './App';
import './styles/global/index.css';
import './i18n'; // Initialize i18n
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}

// Initialize Sentry
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const sentryDsn = (process.env as any).SENTRY_DSN_FE;
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    // Tracing
    tracesSampleRate: 1.0, // Capture 100% of the transactions
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
    environment:
      (process.env as { [key: string]: string | undefined }).ENVIRONMENT ||
      'development',
  });
}

const root = createRoot(rootElement);
root.render(<App />);

// Register service worker for offline support and PWA features
const isProd = process.env.NODE_ENV === 'production';
if (isProd) {
  serviceWorkerRegistration.register();
} else {
  // Unregister service worker in development to avoid refresh loops
  serviceWorkerRegistration.unregister();
}
