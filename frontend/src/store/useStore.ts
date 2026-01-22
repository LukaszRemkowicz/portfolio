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

  // Actions
  loadInitialData: () => Promise<void>;
  loadImages: (params?: FilterParams) => Promise<void>;
  loadProjects: () => Promise<void>;
  loadTags: () => Promise<void>;
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

  clearError: () => set({ error: null }),

  loadInitialData: async () => {
    // Avoid double loading if already have data
    if (get().profile && get().backgroundUrl) return;

    set({ isInitialLoading: true, error: null });
    try {
      const [profileData, bgUrl, featuresData, tagsData] = await Promise.all([
        fetchProfile(),
        fetchBackground(),
        fetchEnabledFeatures(),
        fetchTags(),
      ]);
      set({
        profile: profileData,
        backgroundUrl: bgUrl,
        features: featuresData,
        tags: tagsData,
      });
    } catch (e: unknown) {
      let message = "An unexpected anomaly occurred.";
      if (e instanceof NetworkError) {
        message = "Signal lost. Please check your network connection.";
      } else if (e instanceof ServerError) {
        message = "The cosmic archives are temporarily unreachable.";
      }
      set({ error: message });
      console.error("Store initial load failure:", e);
    } finally {
      set({ isInitialLoading: false });
    }
  },

  loadImages: async (params = {}) => {
    set({ isImagesLoading: true, error: null });
    try {
      const data = await fetchAstroImages(params);
      set({ images: data });
    } catch (e: unknown) {
      let message = "Failed to fetch gallery images.";
      if (e instanceof NetworkError) {
        message = "Connection failed. The cosmic relay is offline.";
      } else if (e instanceof ServerError) {
        message = "Server collision detected. Please try again later.";
      }
      set({ error: message });
      console.error("Store image load failure:", e);
    } finally {
      set({ isImagesLoading: false });
    }
  },

  loadProjects: async () => {
    set({ isProjectsLoading: true, error: null });
    try {
      const data = await fetchProjects();
      set({ projects: data });
    } catch (e: unknown) {
      let message = "Failed to fetch programming projects.";
      if (e instanceof NetworkError) {
        message = "Connection failure while accessing project archives.";
      } else if (e instanceof ServerError) {
        message = "Project database is temporarily unavailable.";
      }
      set({ error: message });
      console.error("Store projects load failure:", e);
    } finally {
      set({ isProjectsLoading: false });
    }
  },
  loadTags: async () => {
    try {
      const data = await fetchTags();
      set({ tags: data });
    } catch (e: unknown) {
      console.error("Store tags load failure:", e);
    }
  },
}));
