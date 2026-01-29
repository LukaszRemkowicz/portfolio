// frontend/src/__tests__/PrivacyPolicy.test.tsx
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PrivacyPolicy from '../components/PrivacyPolicy';

describe('PrivacyPolicy Component', () => {
  beforeEach(() => {
    render(<PrivacyPolicy />);
  });

  describe('Page Structure', () => {
    it('renders the page title', () => {
      expect(
        screen.getByText('Privacy Policy & Cookie Notice')
      ).toBeInTheDocument();
    });

    it('renders last updated date', () => {
      expect(screen.getByText(/Last updated:/i)).toBeInTheDocument();
    });

    it('renders introduction section', () => {
      expect(screen.getByText(/Introduction/i)).toBeInTheDocument();
      expect(
        screen.getByText(/personal portfolio showcasing/i)
      ).toBeInTheDocument();
    });
  });

  describe('Cookie Information', () => {
    it('documents _ga cookie', () => {
      expect(screen.getByText('_ga')).toBeInTheDocument();
      expect(screen.getByText(/2 years/i)).toBeInTheDocument();
    });

    it('documents _gid cookie', () => {
      expect(screen.getByText('_gid')).toBeInTheDocument();
      expect(screen.getByText(/24 hours/i)).toBeInTheDocument();
    });

    it('documents _gat cookie', () => {
      expect(screen.getByText('_gat')).toBeInTheDocument();
      expect(screen.getByText(/1 minute/i)).toBeInTheDocument();
    });

    it('explains what data is collected', () => {
      expect(screen.getByText(/What Data We Collect/i)).toBeInTheDocument();
      expect(screen.getByText(/Anonymous usage data/i)).toBeInTheDocument();
      expect(screen.getByText(/Geographic location/i)).toBeInTheDocument();
      expect(screen.getByText(/Referral source/i)).toBeInTheDocument();
    });

    it('explains why cookies are used', () => {
      expect(screen.getByText(/Why We Use Cookies/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Which content is most popular/i)
      ).toBeInTheDocument();
    });
  });

  describe('User Rights & Opt-Out', () => {
    it('provides opt-out options', () => {
      expect(screen.getByText(/Your Choices & Rights/i)).toBeInTheDocument();
      expect(screen.getByText(/Opt-Out Options:/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Configure your browser to block cookies/i)
      ).toBeInTheDocument();
    });

    it('includes Google Analytics opt-out link', () => {
      const optOutLink = screen.getByText(
        /Google Analytics Opt-out Browser Add-on/i
      );
      expect(optOutLink).toBeInTheDocument();
      expect(optOutLink.closest('a')).toHaveAttribute(
        'href',
        'https://tools.google.com/dlpage/gaoptout'
      );
      expect(optOutLink.closest('a')).toHaveAttribute('target', '_blank');
      expect(optOutLink.closest('a')).toHaveAttribute(
        'rel',
        'noopener noreferrer'
      );
    });
  });

  describe('Data Retention', () => {
    it('specifies data retention period', () => {
      expect(screen.getByText(/Data Retention/i)).toBeInTheDocument();
      expect(screen.getByText(/26 months/i)).toBeInTheDocument();
    });
  });

  describe('Third-Party Services', () => {
    it('lists Google Analytics as third-party service', () => {
      expect(
        screen.getByRole('heading', { name: /Third-Party Services/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Web analytics service by Google LLC/i)
      ).toBeInTheDocument();
    });

    it('includes link to Google Privacy Policy', () => {
      const googlePrivacyLink = screen.getByText(/Google Privacy Policy/i);
      expect(googlePrivacyLink).toBeInTheDocument();
      expect(googlePrivacyLink.closest('a')).toHaveAttribute(
        'href',
        'https://policies.google.com/privacy'
      );
      expect(googlePrivacyLink.closest('a')).toHaveAttribute(
        'target',
        '_blank'
      );
    });
  });

  describe('Contact Information', () => {
    it('provides contact section', () => {
      expect(screen.getByText(/^Contact$/i)).toBeInTheDocument();
      expect(
        screen.getByText(/contact form on this website/i)
      ).toBeInTheDocument();
    });
  });

  describe('GDPR Compliance', () => {
    it('states no PII is collected', () => {
      expect(
        screen.getByText(/No personally identifiable information/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/cannot identify individual visitors/i)
      ).toBeInTheDocument();
    });

    it('provides transparency about data usage', () => {
      expect(screen.getByText(/being transparent/i)).toBeInTheDocument();
    });
  });
});
