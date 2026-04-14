import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchSettings } from '../api/services';
import { EnabledFeatures, MeteorConfig } from '../types';

export interface SettingsResult extends EnabledFeatures {
  meteors?: MeteorConfig | null;
}

export const useSettings = () => {
  const { i18n } = useTranslation();
  const language = (i18n.language || 'en').split('-')[0];

  return useQuery<SettingsResult, Error>({
    queryKey: ['settings', language],
    queryFn: () => fetchSettings(),
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnReconnect: true,
    refetchOnWindowFocus: true,
  });
};
