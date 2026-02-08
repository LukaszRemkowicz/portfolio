import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Contact from '../components/Contact';
import { useAppStore } from '../store/useStore';
import { fetchContact } from '../api/services';
import { AppError } from '../api/errors';

// Mock the services
jest.mock('../api/services', () => ({
  fetchEnabledFeatures: jest.fn(),
  fetchContact: jest.fn(),
}));

describe('Contact Component', () => {
  const mockFetchContact = fetchContact as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    useAppStore.setState({
      features: null,
      isInitialLoading: false,
    });
  });

  it('renders the form when contactForm is enabled', async () => {
    useAppStore.setState({ features: { contactForm: true } });
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
    useAppStore.setState({ features: { contactForm: false } });
    const { container } = render(<Contact />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it('shows validation errors when fields are empty', async () => {
    useAppStore.setState({ features: { contactForm: true } });
    render(<Contact />);

    const form = screen.getByRole('form');
    fireEvent.submit(form);

    expect(await screen.findByText('contact.errors.name')).toBeInTheDocument();
    expect(screen.getByText('contact.errors.email')).toBeInTheDocument();
    expect(screen.getByText('contact.errors.subject')).toBeInTheDocument();
    expect(screen.getByText('contact.errors.message')).toBeInTheDocument();
  });

  it('shows success message on successful submission', async () => {
    useAppStore.setState({ features: { contactForm: true } });
    mockFetchContact.mockResolvedValue({ message: 'Success' });

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
    useAppStore.setState({ features: { contactForm: true } });

    // Simulate a 429 Throttled error with a specific message
    const throttledError = new AppError('Too many requests. Wait 1 hour.', 429);
    mockFetchContact.mockRejectedValue(throttledError);

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
    useAppStore.setState({ features: { contactForm: true } });

    // We need to import the class or simulate the behavior
    // Since we mock services, we can just throw what the interceptor would throw
    const { ValidationError } = require('../api/errors');
    mockFetchContact.mockRejectedValue(
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
