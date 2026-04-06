import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import Shop from '../components/Shop';

describe('Shop Component', () => {
  it('renders the static shop placeholder page', () => {
    render(
      <MemoryRouter>
        <Shop />
      </MemoryRouter>
    );

    expect(
      screen.getByRole('heading', { name: 'Collect the night sky in print.' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Browse placeholders' })
    ).toBeInTheDocument();
    expect(screen.getAllByText('Coming soon')).toHaveLength(3);
  });
});
