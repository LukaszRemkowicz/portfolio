import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import StarBackground from '../components/StarBackground';
import { useSettings } from '../hooks/useSettings';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the hook
jest.mock('../hooks/useSettings');

describe('StarBackground Component', () => {
  const mockUseSettings = useSettings as jest.Mock;
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSettings.mockReturnValue({
      data: { meteors: true },
      isLoading: false,
    });
  });

  const renderWithQueryClient = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  };

  it('renders without crashing', () => {
    const { container } = renderWithQueryClient(<StarBackground />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('contains nebula and star layers', () => {
    const { container } = renderWithQueryClient(<StarBackground />);
    // Check for the base canvas class name in a way that handles CSS modules
    expect(container.querySelector('[class*="bgCanvas"]')).toBeInTheDocument();
    expect(
      container.querySelector('[class*="nebulaTexture"]')
    ).toBeInTheDocument();
    expect(
      container.querySelector('[class*="starDensity"]')
    ).toBeInTheDocument();
  });
});
