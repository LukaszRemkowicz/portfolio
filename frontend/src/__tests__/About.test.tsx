import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import About from '../components/About';
import { UserProfile } from '../types';

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
});
