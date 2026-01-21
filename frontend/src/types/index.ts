import { ReactNode } from "react";

// API Response Types
export interface UserProfile {
  first_name: string;
  last_name: string;
  short_description: string;
  avatar?: string | null;
  bio?: string;
  about_me_image?: string | null;
  about_me_image2?: string | null;
  contact_email?: string;
  prelections?: boolean;
  profiles?: Profile[];
}

export interface Profile {
  type: "PROGRAMMING" | "ASTRO";
  is_active: boolean;
  title: string;
  specific_bio: string;
  github_url?: string;
  linkedin_url?: string;
  astrobin_url?: string;
  fb_url?: string;
  ig_url?: string;
}

export interface BackgroundImage {
  url?: string;
}

export interface EquipmentItem {
  id: number;
  model?: string;
  name?: string;
}

export interface AstroImage {
  pk: number;
  url: string;
  thumbnail_url?: string;
  tags?: string[];
  name: string;
  description: string;
  created_at?: string;
  capture_date?: string;
  location?: string;
  telescope?: EquipmentItem[] | string[];
  camera?: EquipmentItem[] | string[];
  tracker?: EquipmentItem[] | string[];
  tripod?: EquipmentItem[] | string[];
  lens?: EquipmentItem[] | string[];
  exposure_details?: string;
  processing_details?: string;
  celestial_object?: string;
  astrobin_url?: string;
}

export interface MainPageLocation {
  pk: number;
  country: string;
  country_name: string;
  country_slug: string;
  place_name: string | null;
  place_slug: string | null;
  highlight_name?: string;
  adventure_date?: string;
  story?: string;
  background_image?: string | null;
  created_at: string;
  images: AstroImage[];
}

export type LocationResponse = MainPageLocation[];

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
export type SubmitStatus =
  | "success"
  | "validation_error"
  | "rate_limited"
  | "error"
  | null;

export interface ProjectImage {
  pk: number;
  url: string;
  thumbnail_url?: string;
  is_cover: boolean;
  name: string;
}

export interface Project {
  pk: number;
  name: string;
  description: string;
  technologies: string;
  technologies_list: string[];
  github_url?: string;
  live_url?: string;
  images: ProjectImage[];
  created_at: string;
  updated_at: string;
}

// Component Props Types
export interface HomeProps {
  portraitUrl: string;
  shortDescription: string;
  backgroundUrl?: string | null;
}

export interface AboutProps {
  profile: UserProfile | null;
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

export interface FilterParams {
  filter?: string;
  tag?: string;
  travel?: string;
  limit?: number;
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

export interface EnabledFeatures {
  programming?: boolean;
  contactForm?: boolean;
  lastimages?: boolean;
  travelHighlights?: boolean;
  meteors?: boolean;
}

export interface ApiRoutes {
  profile: string;
  background: string;
  astroImages: string;
  astroImage: string;
  contact: string;
  whatsEnabled: string;
  projects: string;
  travelHighlights: string;
  travelBySlug: string;
}

// Legacy Gallery Item (for old gallery data structure)
export interface GalleryItem {
  id: number;
  title: string;
  imageUrl: string;
}
