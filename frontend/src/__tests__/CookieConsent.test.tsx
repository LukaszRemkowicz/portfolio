import { render, screen, act, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import CookieConsent from '../components/common/CookieConsent';

const renderWithRouter = (component: React.ReactElement) => {
  return render(<MemoryRouter>{component}</MemoryRouter>);
};

describe('CookieConsent Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders nothing initially', () => {
    renderWithRouter(<CookieConsent onAccept={jest.fn()} />);
    const banner = screen.queryByRole('heading', { name: 'Cookie Consent' });
    expect(banner).not.toBeInTheDocument();
  });

  it('shows banner after delay if no consent is stored', async () => {
    renderWithRouter(<CookieConsent onAccept={jest.fn()} />);

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(200);
    });

    const banner = screen.getByRole('heading', { name: 'Cookie Consent' });
    expect(banner).toBeInTheDocument();
  });

  it('does not show banner if consent is already true', () => {
    localStorage.setItem('cookieConsent', 'true');
    renderWithRouter(<CookieConsent onAccept={jest.fn()} />);

    act(() => {
      jest.advanceTimersByTime(200);
    });

    const banner = screen.queryByRole('heading', { name: 'Cookie Consent' });
    expect(banner).not.toBeInTheDocument();
  });

  it('does not show banner if consent is already false', () => {
    localStorage.setItem('cookieConsent', 'false');
    renderWithRouter(<CookieConsent onAccept={jest.fn()} />);

    act(() => {
      jest.advanceTimersByTime(200);
    });

    const banner = screen.queryByRole('heading', { name: 'Cookie Consent' });
    expect(banner).not.toBeInTheDocument();
  });

  it('sets localStorage to true and calls onAccept when Accept is clicked', async () => {
    const onAccept = jest.fn();
    renderWithRouter(<CookieConsent onAccept={onAccept} />);

    act(() => {
      jest.advanceTimersByTime(200);
    });

    const acceptBtn = screen.getByRole('button', { name: 'Accept' });
    fireEvent.click(acceptBtn);

    expect(localStorage.getItem('cookieConsent')).toBe('true');
    expect(onAccept).toHaveBeenCalledTimes(1);
    expect(
      screen.queryByRole('heading', { name: 'Cookie Consent' })
    ).not.toBeInTheDocument();
  });

  it('sets localStorage to false when Decline is clicked', async () => {
    renderWithRouter(<CookieConsent onAccept={jest.fn()} />);

    act(() => {
      jest.advanceTimersByTime(200);
    });

    const declineBtn = screen.getByRole('button', { name: 'Decline' });
    fireEvent.click(declineBtn);

    expect(localStorage.getItem('cookieConsent')).toBe('false');
    expect(
      screen.queryByRole('heading', { name: 'Cookie Consent' })
    ).not.toBeInTheDocument();
  });

  it('navigates to Privacy Policy via link', async () => {
    renderWithRouter(<CookieConsent onAccept={jest.fn()} />);

    act(() => {
      jest.advanceTimersByTime(200);
    });

    const link = screen.getByRole('link', { name: 'Privacy Policy' });
    expect(link).toHaveAttribute('href', '/privacy-policy');
  });
});
