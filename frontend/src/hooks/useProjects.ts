// frontend/src/hooks/useProjects.ts
import { useQuery } from '@tanstack/react-query';
import { fetchProjects } from '../api/services';
import { Project } from '../types';

export const useProjects = () =>
  useQuery<Project[], Error>({
    queryKey: ['projects'],
    queryFn: fetchProjects,
    staleTime: 5 * 60 * 1000,
  });
