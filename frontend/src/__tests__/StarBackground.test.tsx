import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import StarBackground from '../components/StarBackground';
import { useSettings } from '../hooks/useSettings';

jest.mock('../hooks/useSettings');

describe('StarBackground Component', () => {
  beforeEach(() => {
    (useSettings as jest.Mock).mockReturnValue({
      data: { meteors: null },
      isLoading: false,
      error: null,
    });
  });

  it('renders without crashing', () => {
    const { container } = render(<StarBackground />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('contains nebula and star layers', () => {
    const { container } = render(<StarBackground />);
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
