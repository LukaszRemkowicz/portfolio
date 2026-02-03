import { create } from 'zustand';
import {
  UserProfile,
  AstroImage,
  FilterParams,
  EnabledFeatures,
  Project,
  Tag,
  MeteorConfig,
} from '../types';
import {
  fetchProfile,
  fetchBackground,
  fetchAstroImages,
  fetchSettings,
  fetchProjects,
  fetchTags,
  fetchCategories,
} from '../api/services';
import { NetworkError, ServerError } from '../api/errors';

import i18n from '../i18n';

interface AppState {
  profile: UserProfile | null;
  backgroundUrl: string | null;
  images: AstroImage[];
  projects: Project[];
  categories: string[];
  tags: Tag[];
  features: EnabledFeatures | null;
  isInitialLoading: boolean;
  isImagesLoading: boolean;
  isProjectsLoading: boolean;
  error: string | null;
  initialSessionId: string;
  imagesSessionId: string;
  projectsSessionId: string;
  tagsSessionId: string;

  // Actions
  loadInitialData: (force?: boolean) => Promise<void>;
  loadImages: (params?: FilterParams) => Promise<void>;
  loadProjects: () => Promise<void>;
  loadCategories: (force?: boolean) => Promise<void>;
  loadTags: (category?: string) => Promise<void>;
  loadMeteorConfig: () => Promise<void>;
  clearError: () => void;
  meteorConfig: MeteorConfig | null;
}

export const useAppStore = create<AppState>((set, get) => ({
  profile: null,
  backgroundUrl: null,
  images: [],
  projects: [],
  categories: [],
  tags: [],
  features: null,
  isInitialLoading: false,
  isImagesLoading: false,
  isProjectsLoading: false,
  error: null,
  initialSessionId: '',
  imagesSessionId: '',
  projectsSessionId: '',
  tagsSessionId: '',
  meteorConfig: null,

  clearError: () => set({ error: null }),

  loadInitialData: async (force = false) => {
    // Avoid double loading if already have data
    if (!force && get().profile && get().backgroundUrl) return;

    const sessionId = crypto.randomUUID();
    set({ isInitialLoading: true, error: null, initialSessionId: sessionId });
    try {
      const [profileData, bgUrl, settingsData] = await Promise.all([
        fetchProfile(),
        fetchBackground(),
        fetchSettings(),
      ]);

      if (get().initialSessionId === sessionId) {
        set({
          profile: profileData,
          backgroundUrl: bgUrl,
          features: settingsData,
          meteorConfig: settingsData.meteors || null,
          isInitialLoading: false,
        });
      }
    } catch (e: unknown) {
      if (get().initialSessionId === sessionId) {
        let message = 'An unexpected anomaly occurred.';
        if (e instanceof NetworkError) {
          message = 'Signal lost. Please check your network connection.';
        } else if (e instanceof ServerError) {
          message = 'The cosmic archives are temporarily unreachable.';
        }
        set({ error: message, isInitialLoading: false });
      }
      console.error('Store initial load failure:', e);
    }
  },

  loadImages: async (params = {}) => {
    const sessionId = crypto.randomUUID();
    set({ isImagesLoading: true, error: null, imagesSessionId: sessionId });
    try {
      const data = await fetchAstroImages(params);

      // Only update if this is still the current session
      if (get().imagesSessionId === sessionId) {
        set({
          images: data || [],
          isImagesLoading: false,
        });
      }
    } catch (e: unknown) {
      if (get().imagesSessionId === sessionId) {
        let message = 'Failed to fetch gallery images.';
        if (e instanceof NetworkError) {
          message = 'Connection failed. The cosmic relay is offline.';
        } else if (e instanceof ServerError) {
          message = 'Server collision detected. Please try again later.';
        }
        set({ error: message, isImagesLoading: false });
      }
      console.error('Store image load failure:', e);
    }
  },

  loadProjects: async () => {
    const sessionId = crypto.randomUUID();
    set({ isProjectsLoading: true, error: null, projectsSessionId: sessionId });
    try {
      const data = await fetchProjects();

      if (get().projectsSessionId === sessionId) {
        set({ projects: data, isProjectsLoading: false });
      }
    } catch (e: unknown) {
      if (get().projectsSessionId === sessionId) {
        let message = 'Failed to fetch programming projects.';
        if (e instanceof NetworkError) {
          message = 'Connection failure while accessing project archives.';
        } else if (e instanceof ServerError) {
          message = 'Project database is temporarily unavailable.';
        }
        set({ error: message, isProjectsLoading: false });
      }
      console.error('Store projects load failure:', e);
    }
  },
  loadTags: async (category?: string) => {
    const sessionId = crypto.randomUUID();
    set({ tagsSessionId: sessionId });
    try {
      const data = await fetchTags(category);
      if (get().tagsSessionId === sessionId) {
        set({ tags: data });
      }
    } catch (e: unknown) {
      console.error('Store tags load failure:', e);
    }
  },
  loadCategories: async (force = false) => {
    // Avoid double loading if already have data
    if (!force && get().categories.length > 0) return;

    try {
      const data = await fetchCategories();
      set({ categories: data });
    } catch (e: unknown) {
      console.error('Store categories load failure:', e);
    }
  },

  loadMeteorConfig: async () => {
    try {
      const data = await fetchSettings();
      set({ meteorConfig: data.meteors || null });
    } catch (e: unknown) {
      console.error('Store meteor config load failure:', e);
    }
  },
}));

// Listen for language changes and refresh all data
i18n.on('languageChanged', () => {
  const store = useAppStore.getState();

  // Refresh data that doesn't depend on complex state
  store.loadInitialData(true);
  store.loadProjects();
  store.loadCategories(true);
  store.loadTags();

  // Note: loadImages is usually triggered by components (AstroGallery)
  // via useEffect when they re-render on language change if we add i18n.language to deps
});
