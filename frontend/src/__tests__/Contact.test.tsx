import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Contact from '../components/Contact';
import { useSettings } from '../hooks/useSettings';
import { fetchContact } from '../api/services';
import { AppError } from '../api/errors';

// Mock useSettings hook
jest.mock('../hooks/useSettings');

// Mock services
jest.mock('../api/services', () => ({
  fetchContact: jest.fn(),
}));

describe('Contact Component', () => {
  const mockUseSettings = useSettings as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSettings.mockReturnValue({
      data: null,
      isLoading: false,
    });
  });

  it('renders the form when contactForm is enabled', async () => {
    mockUseSettings.mockReturnValue({
      data: { contactForm: true },
      isLoading: false,
    });
    render(<Contact />);

    expect(
      await screen.findByRole('heading', { name: 'contact.title' })
    ).toBeInTheDocument();
    expect(screen.getByText('contact.identity')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'contact.submit' })
    ).toBeInTheDocument();
  });

  it('renders nothing when contactForm is disabled', async () => {
    mockUseSettings.mockReturnValue({
      data: { contactForm: false },
      isLoading: false,
    });
    const { container } = render(<Contact />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it('shows validation errors when fields are empty', async () => {
    mockUseSettings.mockReturnValue({
      data: { contactForm: true },
      isLoading: false,
    });
    render(<Contact />);

    const form = screen.getByRole('form');
    fireEvent.submit(form);

    expect(await screen.findByText('contact.errors.name')).toBeInTheDocument();
    expect(screen.getByText('contact.errors.email')).toBeInTheDocument();
    expect(screen.getByText('contact.errors.subject')).toBeInTheDocument();
    expect(screen.getByText('contact.errors.message')).toBeInTheDocument();
  });

  it('shows success message on successful submission', async () => {
    mockUseSettings.mockReturnValue({
      data: { contactForm: true },
      isLoading: false,
    });
    (fetchContact as jest.Mock).mockResolvedValue({ message: 'Success' });

    render(<Contact />);

    fireEvent.change(screen.getByPlaceholderText('contact.namePlaceholder'), {
      target: { value: 'John Doe' },
    });
    fireEvent.change(screen.getByPlaceholderText('contact.emailPlaceholder'), {
      target: { value: 'john@example.com' },
    });
    fireEvent.change(
      screen.getByPlaceholderText('contact.subjectPlaceholder'),
      {
        target: { value: 'Hello There' },
      }
    );
    fireEvent.change(
      screen.getByPlaceholderText('contact.messagePlaceholder'),
      {
        target: { value: 'This is a long message for testing.' },
      }
    );

    fireEvent.click(screen.getByRole('button', { name: 'contact.submit' }));

    expect(await screen.findByText('contact.success')).toBeInTheDocument();

    // Verify inputs are cleared
    expect(screen.getByPlaceholderText('contact.namePlaceholder')).toHaveValue(
      ''
    );
  });

  it('displays server error message (e.g., 429 Throttling)', async () => {
    mockUseSettings.mockReturnValue({
      data: { contactForm: true },
      isLoading: false,
    });

    // Simulate a 429 Throttled error with a specific message
    const throttledError = new AppError('Too many requests. Wait 1 hour.', 429);
    (fetchContact as jest.Mock).mockRejectedValue(throttledError);

    render(<Contact />);

    fireEvent.change(screen.getByPlaceholderText('contact.namePlaceholder'), {
      target: { value: 'John Doe' },
    });
    fireEvent.change(screen.getByPlaceholderText('contact.emailPlaceholder'), {
      target: { value: 'john@example.com' },
    });
    fireEvent.change(
      screen.getByPlaceholderText('contact.subjectPlaceholder'),
      {
        target: { value: 'Hello There' },
      }
    );
    fireEvent.change(
      screen.getByPlaceholderText('contact.messagePlaceholder'),
      {
        target: { value: 'This is a long message for testing.' },
      }
    );

    fireEvent.click(screen.getByRole('button', { name: 'contact.submit' }));

    expect(
      await screen.findByText(/Too many requests. Wait 1 hour./i)
    ).toBeInTheDocument();
  });

  it('handles 400 validation errors from server', async () => {
    mockUseSettings.mockReturnValue({
      data: { contactForm: true },
      isLoading: false,
    });

    // We need to import the class or simulate the behavior
    // Since we mock services, we can just throw what the interceptor would throw
    const { ValidationError } = require('../api/errors');
    (fetchContact as jest.Mock).mockRejectedValue(
      new ValidationError({ name: ['Server says name is too short.'] })
    );

    render(<Contact />);

    fireEvent.change(screen.getByPlaceholderText('contact.namePlaceholder'), {
      target: { value: 'John Doe' },
    });
    fireEvent.change(screen.getByPlaceholderText('contact.emailPlaceholder'), {
      target: { value: 'john@example.com' },
    });
    fireEvent.change(
      screen.getByPlaceholderText('contact.subjectPlaceholder'),
      {
        target: { value: 'Hello There' },
      }
    );
    fireEvent.change(
      screen.getByPlaceholderText('contact.messagePlaceholder'),
      {
        target: { value: 'This is a long message for testing.' },
      }
    );

    fireEvent.submit(screen.getByRole('form'));

    expect(
      await screen.findByText(/Server says name is too short./i)
    ).toBeInTheDocument();
  });
});
