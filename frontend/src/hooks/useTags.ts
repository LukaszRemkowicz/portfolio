// frontend/src/hooks/useTags.ts
import { useQuery } from '@tanstack/react-query';
import { fetchTags } from '../api/services';
import { Tag } from '../types';

export const useTags = (category?: string) =>
  useQuery<Tag[], Error>({
    queryKey: ['tags', category],
    queryFn: () => fetchTags(category),
  });
