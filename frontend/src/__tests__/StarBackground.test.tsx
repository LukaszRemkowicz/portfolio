import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import StarBackground from '../components/StarBackground';

describe('StarBackground Component', () => {
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
