import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Programming from '../components/Programming';
import { Project } from '../types';
import { useProjects } from '../hooks/useProjects';

// Mock the hook
jest.mock('../hooks/useProjects');

describe('Programming Component', () => {
  const mockUseProjects = useProjects as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });
  });

  it('renders the Project Archive title', () => {
    render(<Programming />);
    expect(screen.getByText(/Project Archive/i)).toBeInTheDocument();
  });

  it('shows loading state correctly', () => {
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: true,
      error: null,
    });

    render(<Programming />);
    expect(screen.getByText(/Compiling projects/i)).toBeInTheDocument();
  });

  it('renders projects list', () => {
    const mockProjects: Project[] = [
      {
        pk: 1,
        name: 'Test Project',
        description: 'Test Description',
        technologies: 'React, Node',
        technologies_list: ['React', 'Node'],
        github_url: 'http://github.com',
        live_url: 'http://live.com',
        images: [{ pk: 1, url: 'test.jpg', name: 'Test', is_cover: true }],
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      },
    ];

    mockUseProjects.mockReturnValue({
      data: mockProjects,
      isLoading: false,
      error: null,
    });

    render(<Programming />);
    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });
});
