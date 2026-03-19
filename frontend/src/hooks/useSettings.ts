// frontend/src/hooks/useSettings.ts
import { useQuery } from '@tanstack/react-query';
import { fetchSettings } from '../api/services';
import { EnabledFeatures, MeteorConfig } from '../types';

export interface SettingsResult extends EnabledFeatures {
  meteors?: MeteorConfig | null;
}

export const useSettings = () =>
  useQuery<SettingsResult, Error>({
    queryKey: ['settings'],
    queryFn: () => fetchSettings(),
    staleTime: 10 * 60 * 1000,
  });
