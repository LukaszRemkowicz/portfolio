import { ReactNode } from "react";

// API Response Types
export interface UserProfile {
  first_name: string;
  last_name: string;
  avatar?: string | null;
  bio?: string;
  about_me_image?: string | null;
  about_me_image2?: string | null;
  prelections?: boolean;
}

export interface BackgroundImage {
  url?: string;
}

export interface AstroImage {
  pk: number;
  url: string;
  name: string;
  description: string;
  capture_date?: string;
  location?: string;
  equipment?: string;
  exposure_details?: string;
  processing_details?: string;
  celestial_object?: string;
  astrobin_url?: string;
}

export interface ContactFormData {
  name: string;
  email: string;
  subject: string;
  message: string;
  website?: string; // Honeypot field - invisible to humans, bots will fill it
}

export interface ContactResponse {
  success: boolean;
  message: string;
}

export interface ValidationErrors {
  name?: string[];
  email?: string[];
  subject?: string[];
  message?: string[];
}

export type SubmitStatus = "success" | "validation_error" | "rate_limited" | "error" | null;

// Component Props Types
export interface HomeProps {
  portraitUrl: string;
  firstName: string;
  lastName: string;
}

export interface NavbarProps {
  transparent?: boolean;
  programmingBg?: boolean;
}

export interface NavLinkClassProps {
  isActive: boolean;
}

export interface MainLayoutProps {
  children: ReactNode;
}

// HomePage state types
export interface HomePageState {
  portraitUrl: string;
  firstName: string;
  lastName: string;
  backgroundUrl: string | null;
  loading: boolean;
  error: string | null;
}

export interface GalleryItem {
  id: number;
  title: string;
  imageUrl: string;
}

// AstroGallery types
export interface AstroGalleryState {
  images: AstroImage[];
  loading: boolean;
  error: string;
  background: string;
  selectedFilter: string | null;
  modalImage: AstroImage | null;
  modalDescription: string;
  modalDescriptionLoading: boolean;
}

export interface FilterParams {
  filter?: string;
}

export type FilterType =
  | "Landscape"
  | "Deep Sky"
  | "Startrails"
  | "Solar System"
  | "Milky Way"
  | "Northern Lights";

// API Types
export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
}

export interface ApiError {
  response?: {
    data?: {
      errors?: ValidationErrors;
      message?: string;
    };
  };
  message: string;
}

export interface ApiRoutes {
  profile: string;
  background: string;
  astroImages: string;
  astroImage: string;
  contact: string;
}
