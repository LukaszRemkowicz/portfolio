import { create } from 'zustand';
import { UserProfile, AstroImage, FilterParams } from '../types';
import { fetchProfile, fetchBackground, fetchAstroImages } from '../api/services';
import { NetworkError, ServerError } from '../api/errors';

interface AppState {
    profile: UserProfile | null;
    backgroundUrl: string | null;
    images: AstroImage[];
    isInitialLoading: boolean;
    isImagesLoading: boolean;
    error: string | null;

    // Actions
    loadInitialData: () => Promise<void>;
    loadImages: (params?: FilterParams) => Promise<void>;
    clearError: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
    profile: null,
    backgroundUrl: null,
    images: [],
    isInitialLoading: false,
    isImagesLoading: false,
    error: null,

    clearError: () => set({ error: null }),

    loadInitialData: async () => {
        // Avoid double loading if already have data
        if (get().profile && get().backgroundUrl) return;

        set({ isInitialLoading: true, error: null });
        try {
            const [profileData, bgUrl] = await Promise.all([
                fetchProfile(),
                fetchBackground(),
            ]);
            set({ profile: profileData, backgroundUrl: bgUrl });
        } catch (e: any) {
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
        } catch (e: any) {
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
}));
