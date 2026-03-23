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
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  });
};
