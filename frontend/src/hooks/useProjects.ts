import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchProjects } from '../api/services';
import { Project } from '../types';

export const useProjects = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<Project[], Error>({
    queryKey: ['projects', language],
    queryFn: fetchProjects,
    staleTime: 5 * 60 * 1000,
  });
};
