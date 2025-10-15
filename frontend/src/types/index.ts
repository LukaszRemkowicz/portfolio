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
  message: string;
}

export interface ContactResponse {
  success: boolean;
  message: string;
}

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

export interface MainLayoutProps {
  children: React.ReactNode;
}

export interface GalleryItem {
  id: number;
  title: string;
  imageUrl: string;
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
