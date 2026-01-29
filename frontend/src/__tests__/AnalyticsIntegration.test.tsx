// frontend/src/__tests__/AnalyticsIntegration.test.tsx
import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Link } from 'react-router-dom';
import { useGoogleAnalytics } from '../hooks/useGoogleAnalytics';
import * as analytics from '../utils/analytics';

// Mock the analytics utility to verify calls
jest.mock('../utils/analytics', () => ({
  loadGoogleAnalytics: jest.fn(),
  trackPageView: jest.fn(),
}));

const TestComponent: React.FC<{ hasConsented: boolean }> = ({
  hasConsented,
}) => {
  useGoogleAnalytics(hasConsented);
  return (
    <div>
      <nav>
        <Link to='/'>Home</Link>
        <Link to='/about'>About</Link>
      </nav>
      <Routes>
        <Route path='/' element={<div>Home Page</div>} />
        <Route path='/about' element={<div>About Page</div>} />
      </Routes>
    </div>
  );
};

describe('Analytics Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('calls loadGoogleAnalytics and trackPageView on mount when consented', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <TestComponent hasConsented={true} />
      </MemoryRouter>
    );

    expect(analytics.loadGoogleAnalytics).toHaveBeenCalledTimes(1);
    expect(analytics.trackPageView).toHaveBeenCalledWith('/');
  });

  test('does not call analytics when not consented', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <TestComponent hasConsented={false} />
      </MemoryRouter>
    );

    expect(analytics.loadGoogleAnalytics).not.toHaveBeenCalled();
    expect(analytics.trackPageView).not.toHaveBeenCalled();
  });

  test('tracks page view on route change', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <TestComponent hasConsented={true} />
      </MemoryRouter>
    );

    // Initial hit
    expect(analytics.trackPageView).toHaveBeenCalledWith('/');

    // Navigate to /about
    const aboutLink = screen.getByText('About');
    await act(async () => {
      aboutLink.click();
    });

    // Check second hit
    expect(analytics.trackPageView).toHaveBeenCalledWith('/about');
    expect(analytics.trackPageView).toHaveBeenCalledTimes(2);
  });
});
