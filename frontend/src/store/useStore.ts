import { create } from "zustand";
import {
  UserProfile,
  AstroImage,
  FilterParams,
  EnabledFeatures,
  Project,
  Tag,
} from "../types";
import {
  fetchProfile,
  fetchBackground,
  fetchAstroImages,
  fetchEnabledFeatures,
  fetchProjects,
  fetchTags,
} from "../api/services";
import { NetworkError, ServerError } from "../api/errors";

interface AppState {
  profile: UserProfile | null;
  backgroundUrl: string | null;
  images: AstroImage[];
  projects: Project[];
  tags: Tag[];
  features: EnabledFeatures | null;
  isInitialLoading: boolean;
  isImagesLoading: boolean;
  isProjectsLoading: boolean;
  error: string | null;
  initialSessionId: number;
  imagesSessionId: number;
  projectsSessionId: number;

  // Actions
  loadInitialData: () => Promise<void>;
  loadImages: (params?: FilterParams) => Promise<void>;
  loadProjects: () => Promise<void>;
  loadTags: (category?: string) => Promise<void>;
  clearError: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  profile: null,
  backgroundUrl: null,
  images: [],
  projects: [],
  tags: [],
  features: null,
  isInitialLoading: false,
  isImagesLoading: false,
  isProjectsLoading: false,
  error: null,
  initialSessionId: 0,
  imagesSessionId: 0,
  projectsSessionId: 0,

  clearError: () => set({ error: null }),

  loadInitialData: async () => {
    // Avoid double loading if already have data
    if (get().profile && get().backgroundUrl) return;

    const sessionId = get().initialSessionId + 1;
    set({ isInitialLoading: true, error: null, initialSessionId: sessionId });
    try {
      const [profileData, bgUrl, featuresData] = await Promise.all([
        fetchProfile(),
        fetchBackground(),
        fetchEnabledFeatures(),
      ]);

      if (get().initialSessionId === sessionId) {
        set({
          profile: profileData,
          backgroundUrl: bgUrl,
          features: featuresData,
          isInitialLoading: false,
        });
      }
    } catch (e: unknown) {
      if (get().initialSessionId === sessionId) {
        let message = "An unexpected anomaly occurred.";
        if (e instanceof NetworkError) {
          message = "Signal lost. Please check your network connection.";
        } else if (e instanceof ServerError) {
          message = "The cosmic archives are temporarily unreachable.";
        }
        set({ error: message, isInitialLoading: false });
      }
      console.error("Store initial load failure:", e);
    }
  },

  loadImages: async (params = {}) => {
    const sessionId = get().imagesSessionId + 1;
    set({ isImagesLoading: true, error: null, imagesSessionId: sessionId });
    try {
      const data = await fetchAstroImages(params);

      // Only update if this is still the current session
      if (get().imagesSessionId === sessionId) {
        set({
          images: data,
          isImagesLoading: false,
        });
      }
    } catch (e: unknown) {
      if (get().imagesSessionId === sessionId) {
        let message = "Failed to fetch gallery images.";
        if (e instanceof NetworkError) {
          message = "Connection failed. The cosmic relay is offline.";
        } else if (e instanceof ServerError) {
          message = "Server collision detected. Please try again later.";
        }
        set({ error: message, isImagesLoading: false });
      }
      console.error("Store image load failure:", e);
    }
  },

  loadProjects: async () => {
    const sessionId = get().projectsSessionId + 1;
    set({ isProjectsLoading: true, error: null, projectsSessionId: sessionId });
    try {
      const data = await fetchProjects();

      if (get().projectsSessionId === sessionId) {
        set({ projects: data, isProjectsLoading: false });
      }
    } catch (e: unknown) {
      if (get().projectsSessionId === sessionId) {
        let message = "Failed to fetch programming projects.";
        if (e instanceof NetworkError) {
          message = "Connection failure while accessing project archives.";
        } else if (e instanceof ServerError) {
          message = "Project database is temporarily unavailable.";
        }
        set({ error: message, isProjectsLoading: false });
      }
      console.error("Store projects load failure:", e);
    }
  },
  loadTags: async (category?: string) => {
    try {
      const data = await fetchTags(category);
      set({ tags: data });
    } catch (e: unknown) {
      console.error("Store tags load failure:", e);
    }
  },
}));
