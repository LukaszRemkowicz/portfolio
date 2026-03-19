import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './App';
import './styles/global/index.css';
import './i18n.client';
import { initClientServices } from './utils/initClientServices';
import i18n from './i18n.client';
import { setLanguageGetter } from './api/api';

// Wire the axios interceptor to read the live i18n language on the client.
// On the server (Phase 3+) this is handled per-request via createServerI18n.
setLanguageGetter(() => i18n.language || 'en');

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Invalidate all queries when language changes so all data is refetched in new language
i18n.on('languageChanged', () => {
  queryClient.invalidateQueries();
});

// Initialise browser-only services: Sentry (lazy, on interaction) + SW unregister
initClientServices();

const root = createRoot(rootElement);
root.render(
  <QueryClientProvider client={queryClient}>
    <App />
    {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
  </QueryClientProvider>
);
