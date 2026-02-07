import { create } from 'zustand';

// UI-only state store (server state has been migrated to React Query)
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
interface AppState {
  // Add UI-only state here when needed
}

export const useAppStore = create<AppState>(() => ({
  // Initial UI state
}));
