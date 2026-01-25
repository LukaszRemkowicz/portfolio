import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/global/index.css';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}

const root = createRoot(rootElement);
root.render(<App />);

// Register service worker for offline support and PWA features
// Register service worker for offline support and PWA features
if (process.env.NODE_ENV === 'production') {
  serviceWorkerRegistration.register();
} else {
  // Unregister service worker in development to avoid refresh loops
  serviceWorkerRegistration.unregister();
}
