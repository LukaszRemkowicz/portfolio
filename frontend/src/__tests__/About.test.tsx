import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import About from '../components/About';
import { UserProfile } from '../types';
import { useSettings } from '../hooks/useSettings';

jest.mock('../hooks/useSettings', () => ({
  useSettings: jest.fn(),
}));

const mockProfile: UserProfile = {
  first_name: 'John',
  last_name: 'Doe',
  short_description: 'Test Desc',
  avatar: null,
  bio: 'Beyond the Atmosphere. Test bio',
  about_me_image: null,
  about_me_image2: null,
};

describe('About Component', () => {
  beforeEach(() => {
    (useSettings as jest.Mock).mockReturnValue({ data: {} });
  });

  it('renders the section with the new title', () => {
    render(<About profile={mockProfile} />);

    expect(screen.getByText('Beyond the')).toBeInTheDocument();
    expect(screen.getByText('Atmosphere.')).toBeInTheDocument();
  });

  it('renders technical stats', () => {
    render(<About profile={mockProfile} />);

    expect(screen.getByText('Bortle 4')).toBeInTheDocument();
    expect(screen.getByText('430mm')).toBeInTheDocument();
  });

  it('renders total time spent when available in settings', () => {
    (useSettings as jest.Mock).mockReturnValue({
      data: { total_time_spent: 15 },
    });

    render(<About profile={mockProfile} />);

    expect(screen.getByText('15h +')).toHaveAttribute('tabIndex', '0');
    expect(
      screen.getByText(
        'This is the total integration time of the images on this website'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('Total time spent')).toBeInTheDocument();
  });

  it('hides total time spent when settings value is missing', () => {
    render(<About profile={mockProfile} />);

    expect(screen.queryByText('Total time spent')).not.toBeInTheDocument();
  });
});
