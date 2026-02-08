// frontend/src/hooks/useProjects.ts
import { useQuery } from '@tanstack/react-query';
import { fetchProjects } from '../api/services';
import { useTranslation } from 'react-i18next';

export const useProjects = () => {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ['projects', i18n.language],
    queryFn: fetchProjects,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};
