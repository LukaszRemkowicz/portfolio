// API Response Types
export interface UserProfile {
  first_name: string;
  last_name: string;
  avatar?: string;
  bio?: string;
  about_me_image?: string;
  about_me_image2?: string;
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

export type SubmitStatus = 'success' | 'validation_error' | 'error' | null;

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
  children: React.ReactNode;
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
  | 'Landscape'
  | 'Deep Sky'
  | 'Startrails'
  | 'Solar System'
  | 'Milky Way'
  | 'Northern Lights';

// API Types
export interface ApiResponse<T = any> {
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

// CSS Module Types
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}
